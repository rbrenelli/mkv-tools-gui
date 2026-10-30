import os
import subprocess
import tempfile
import unittest

from mkvsuite.core import commands, ffmpeg, jobs, naming, plan
from mkvsuite.core.media import read_media
from mkvsuite.core.tools import find_tool, missing_ffmpeg

PROBE = {
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "2.000000"},
    "streams": [
        {"index": 0, "codec_type": "video", "codec_name": "h264", "disposition": {"default": 1}, "tags": {"language": "und"}},
        {"index": 1, "codec_type": "audio", "codec_name": "aac", "disposition": {"default": 1}, "tags": {"language": "eng"}},
        {"index": 2, "codec_type": "subtitle", "codec_name": "mov_text", "disposition": {"default": 1, "forced": 0},
         "tags": {"language": "por", "title": "Português"}},
        {"index": 3, "codec_type": "subtitle", "codec_name": "hdmv_pgs_subtitle", "disposition": {}, "tags": {}},
        {"index": 4, "codec_type": "data", "codec_name": "bin_data"},
    ],
}


def sample():
    return ffmpeg.parse_probe(PROBE, "/v/clip.mp4")


class ParseTests(unittest.TestCase):
    def test_parse(self):
        info = sample()
        self.assertEqual(info.backend, "ffmpeg")
        self.assertEqual([t.id for t in info.tracks], [0, 1, 2, 3])   # data stream skipped
        self.assertEqual(info.tracks[2].language, "por")
        self.assertEqual(info.tracks[2].name, "Português")
        self.assertTrue(info.tracks[2].text_subtitles)
        self.assertFalse(info.tracks[3].text_subtitles)
        self.assertEqual(info.duration_ns, 2_000_000_000)

    def test_names(self):
        t = sample().tracks
        self.assertEqual(naming.default_name("clip", t[2]), "clip.por.Português.srt")  # mov_text -> srt
        self.assertEqual(naming.default_name("clip", t[3]), "clip.sup")
        self.assertEqual(naming.default_name("clip", t[1]), "clip.eng.aac")


class CommandTests(unittest.TestCase):
    def test_extract_converts_text_subs_and_copies_the_rest(self):
        cmd = ffmpeg.build_extract("ffmpeg", sample(), {2: "/o/a.srt", 1: "/o/a.aac", 3: "/o/a.sup"})
        s = " ".join(cmd)
        self.assertIn("-map 0:2 -c:s srt /o/a.srt", s)
        self.assertIn("-map 0:1 -c copy /o/a.aac", s)
        self.assertIn("-map 0:3 -c copy /o/a.sup", s)

    def test_mp4_rejects_pgs(self):
        with self.assertRaises(ffmpeg.UnsupportedError):
            ffmpeg.build_mux("ffmpeg", "/o/o.mp4", sample())
        ffmpeg.build_mux("ffmpeg", "/o/o.mp4", sample(), keep_ids={0, 1, 2})   # fine without the PGS track
        ffmpeg.build_mux("ffmpeg", "/o/o.mkv", sample())                       # MKV can hold it

    def test_mux_adds_subs_with_metadata(self):
        s = commands.SubInput("/s/pt.srt", "por", "Português", True, False)
        cmd = ffmpeg.build_mux("ffmpeg", "/o/o.mp4", sample(), keep_ids={0, 1, 2}, subs=[s])
        j = " ".join(cmd)
        self.assertIn("-i /s/pt.srt", j)
        self.assertIn("-map 1:0", j)
        self.assertIn("-c:s:1 mov_text", j)                 # second subtitle stream in the output
        self.assertIn("-metadata:s:s:1 language=por", j)
        self.assertIn("-disposition:s:1 default", j)

    def test_edits_only_touch_what_changed(self):
        e = {2: commands.TrackEdit(language="cze", forced=True)}
        cmd = ffmpeg.build_mux("ffmpeg", "/o/o.mkv", sample(), keep_ids={0, 1, 2}, edits=e)
        j = " ".join(cmd)
        self.assertIn("-metadata:s:s:0 language=cze", j)
        self.assertIn("-disposition:s:0 default+forced", j)   # default kept, forced added
        self.assertNotIn("title=", j)
        self.assertIn("-c:s:0 srt", j)                        # mov_text becomes SRT in MKV


class JobTests(unittest.TestCase):
    def test_progress_and_noise(self):
        self.assertEqual(jobs.ffmpeg_progress("out_time_us=1000000", 2_000_000_000), 50)
        self.assertIsNone(jobs.ffmpeg_progress("out_time_us=1000000", 0))
        self.assertTrue(jobs.is_noise("speed=2.3x"))
        self.assertFalse(jobs.is_noise("Error opening input"))

    def test_interpret(self):
        self.assertTrue(jobs.interpret_ffmpeg(0, "").ok)
        o = jobs.interpret_ffmpeg(1, "progress=end\nSomething broke")
        self.assertEqual((o.ok, o.error), (False, "Something broke"))


@unittest.skipUnless(find_tool("ffmpeg") and not missing_ffmpeg() and find_tool("mkvmerge"), "ffmpeg/MKVToolNix missing")
class IntegrationTests(unittest.TestCase):
    def run_ff(self, cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_mp4_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            en, pt = os.path.join(d, "en.srt"), os.path.join(d, "pt.srt")
            for p, text in ((en, "Hello"), (pt, "Olá")):
                with open(p, "w", encoding="utf-8") as f:
                    f.write(f"1\n00:00:00,000 --> 00:00:01,000\n{text}\n")
            mp4 = os.path.join(d, "clip.mp4")
            self.run_ff(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=d=2:s=160x120", "-i", en,
                         "-map", "0", "-map", "1", "-c:v", "libx264", "-c:s", "mov_text",
                         "-metadata:s:s:0", "language=eng", mp4])
            info = read_media(mp4)
            self.assertEqual(info.backend, "ffmpeg")
            self.assertEqual([(t.type, t.language) for t in info.tracks], [("video", "und"), ("subtitles", "eng")])

            # extract the mov_text track as a real .srt
            out = os.path.join(d, "clip.eng.srt")
            self.run_ff(ffmpeg.build_extract("ffmpeg", info, {1: out}))
            with open(out, encoding="utf-8") as f:
                self.assertIn("Hello", f.read())

            # add a Portuguese subtitle, output MP4
            out_mp4 = os.path.join(d, "out.mp4")
            sub = commands.SubInput(pt, "por", "", default=False)
            self.run_ff(ffmpeg.build_mux("ffmpeg", out_mp4, info, subs=[sub]))
            info2 = read_media(out_mp4)
            self.assertEqual([t.language for t in info2.of_type("subtitles")], ["eng", "por"])

            # edit language + forced flag into a new MKV
            out_mkv = os.path.join(d, "out.mkv")
            self.run_ff(ffmpeg.build_mux("ffmpeg", out_mkv, info2,
                                         edits={2: commands.TrackEdit(language="cze", forced=True)}))
            info3 = read_media(out_mkv)
            self.assertEqual(info3.backend, "mkvtoolnix")
            subs = info3.of_type("subtitles")
            self.assertEqual((subs[1].language, subs[1].forced), ("cze", True))

    def test_mkv_to_mp4_and_planner_choices(self):
        with tempfile.TemporaryDirectory() as d:
            en = os.path.join(d, "en.srt")
            with open(en, "w", encoding="utf-8") as f:
                f.write("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
            mkv = os.path.join(d, "a.mkv")
            self.run_ff(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=d=2:s=160x120", "-i", en,
                         "-map", "0", "-map", "1", "-c:v", "libx264", "-c:s", "srt", "-metadata:s:s:0", "language=eng", mkv])
            info = read_media(mkv)                       # read by mkvmerge
            p = plan.mux(info, os.path.join(d, "b.mp4"))  # MKV -> MP4 must go through ffmpeg
            self.assertEqual(p.kind, "ffmpeg")
            self.run_ff(p.argv)
            self.assertEqual([t.language for t in read_media(os.path.join(d, "b.mp4")).of_type("subtitles")], ["eng"])
            self.assertEqual(plan.mux(info, os.path.join(d, "c.mkv")).kind, "mkvtoolnix")
            self.assertEqual(plan.extract(info, {1: "x.srt"}).kind, "mkvtoolnix")
            mp4_info = read_media(os.path.join(d, "b.mp4"))
            self.assertEqual(plan.mux(mp4_info, os.path.join(d, "e.mkv")).kind, "ffmpeg")   # MP4 source -> ffmpeg
            with self.assertRaises(ffmpeg.UnsupportedError):
                plan.propedit(mp4_info, {})


if __name__ == "__main__":
    unittest.main()
