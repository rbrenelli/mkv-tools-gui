import json
import os
import subprocess
import tempfile
import unittest

from mkvsuite.core import commands, jobs, languages, naming, paths
from mkvsuite.core.model import MediaInfo, Track, parse_info, read_info
from mkvsuite.core.tools import clean_env, find_tool

SAMPLE_JSON = {
    "container": {"type": "Matroska", "recognized": True, "properties": {"duration": 2023000000}},
    "tracks": [
        {"id": 0, "type": "video", "codec": "AVC/H.264", "properties": {"codec_id": "V_MPEG4/ISO/AVC", "uid": 11}},
        {"id": 1, "type": "audio", "codec": "AAC", "properties": {"codec_id": "A_AAC", "language": "jpn", "uid": 12, "default_track": True}},
        {"id": 2, "type": "subtitles", "codec": "SubRip/SRT",
         "properties": {"codec_id": "S_TEXT/UTF8", "language": "eng", "uid": 13, "forced_track": True, "track_name": "Signs & Songs"}},
        {"id": 3, "type": "subtitles", "codec": "SubRip/SRT",
         "properties": {"codec_id": "S_TEXT/UTF8", "language": "ces", "uid": 14}},
    ],
}

TABLE = """English language name                                      | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code
-----------------------------------------------------------+----------------+----------------+---------------
'Are'are                                                   | alu            |                |
English                                                    | eng            | eng            | en
Portuguese                                                 | por            | por            | pt
Czech                                                      | ces            | cze            | cs
"""


def sample():
    return parse_info(SAMPLE_JSON, "/v/movie.mkv")


class ModelTests(unittest.TestCase):
    def test_parse(self):
        info = sample()
        self.assertEqual(len(info.tracks), 4)
        self.assertEqual(info.tracks[2].language, "eng")
        self.assertTrue(info.tracks[2].forced)
        self.assertTrue(info.tracks[1].default)
        self.assertEqual(info.tracks[0].language, "und")  # missing language -> und
        self.assertEqual(info.duration_ns, 2023000000)


class NamingTests(unittest.TestCase):
    def test_default_name_keeps_forced_and_name(self):
        t = sample().tracks[2]
        self.assertEqual(naming.default_name("Movie", t), "Movie.eng.Signs Songs.forced.srt")

    def test_unique(self):
        t = sample().tracks[3]
        a = naming.default_name("M", t)
        b = naming.default_name("M", t, taken={a})
        self.assertEqual((a, b), ("M.ces.srt", "M.ces_1.srt"))

    def test_extensions(self):
        self.assertEqual(naming.extension_for("S_TEXT/ASS"), ".ass")
        self.assertEqual(naming.extension_for("S_HDMV/PGS"), ".sup")
        self.assertEqual(naming.extension_for("A_AAC/MPEG4/LC"), ".aac")
        self.assertEqual(naming.extension_for("X_UNKNOWN"), ".bin")

    def test_unicode_name_kept(self):
        t = Track(1, "subtitles", "SRT", "S_TEXT/UTF8", "por", "Português [BR]", False, False, True, 1)
        self.assertEqual(naming.default_name("Filme", t), "Filme.por.Português [BR].srt")


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.langs = languages.parse_language_table(TABLE) + languages.FALLBACK

    def test_table_parse_skips_rows_without_639_2(self):
        codes = [l.code for l in languages.parse_language_table(TABLE)]
        self.assertEqual(codes, ["eng", "por", "cze"])

    def test_detect(self):
        d = lambda f: languages.detect_language(f, self.langs)
        self.assertEqual(d("Movie.pt-BR.srt"), "por")
        self.assertEqual(d("Movie_English.srt"), "eng")
        self.assertEqual(d("Movie.en.srt"), "eng")
        self.assertEqual(d("Movie.cs.srt"), "cze")
        self.assertEqual(d("pt.srt"), "por")    # translations are often just named by language
        self.assertEqual(d("eng.srt"), "eng")
        self.assertIsNone(d("Italian.srt"))     # a lone long word is more likely a title
        self.assertIsNone(d("It.Follows.srt"))  # 'It' is the title, not Italian
        self.assertIsNone(d("Movie.2020.srt"))

    def test_czech_survives(self):
        # the old app turned any language outside its 12 into 'und'
        self.assertIn("cze", [l.code for l in self.langs])


class CommandTests(unittest.TestCase):
    def test_extract(self):
        cmd = commands.build_extract("mkvextract", "/v/a.mkv", {2: "/o/a.eng.srt", 3: "/o/a.ces.srt"})
        self.assertEqual(cmd, ["mkvextract", "--gui-mode", "/v/a.mkv", "tracks", "2:/o/a.eng.srt", "3:/o/a.ces.srt"])

    def test_mux_keeps_everything_without_flags_when_nothing_changed(self):
        cmd = commands.build_mux("mkvmerge", "/o/out.mkv", sample())
        self.assertEqual(cmd, ["mkvmerge", "--gui-mode", "-o", "/o/out.mkv", "/v/movie.mkv"])

    def test_mux_does_not_touch_flags_it_was_not_asked_to(self):
        cmd = commands.build_mux("mkvmerge", "/o/out.mkv", sample(), keep_ids={0, 1, 2, 3})
        self.assertNotIn("--forced-display-flag", cmd)
        self.assertNotIn("--language", cmd)

    def test_mux_drop_tracks(self):
        cmd = commands.build_mux("mkvmerge", "/o/o.mkv", sample(), keep_ids={0, 1, 3})
        self.assertIn("--subtitle-tracks", cmd)
        self.assertEqual(cmd[cmd.index("--subtitle-tracks") + 1], "3")
        cmd = commands.build_mux("mkvmerge", "/o/o.mkv", sample(), keep_ids={0, 1})
        self.assertIn("--no-subtitles", cmd)

    def test_mux_add_subs(self):
        s = commands.SubInput("/s/pt.srt", "por", "Português", True, False)
        cmd = commands.build_mux("mkvmerge", "/o/o.mkv", sample(), subs=[s])
        tail = cmd[cmd.index("/v/movie.mkv") + 1:]
        self.assertEqual(tail, ["--language", "0:por", "--track-name", "0:Português",
                                "--default-track-flag", "0:1", "--forced-display-flag", "0:0", "/s/pt.srt"])

    def test_propedit_uses_uid(self):
        e = {3: commands.TrackEdit(language="cze", name="", default=True), 1: commands.TrackEdit()}
        cmd = commands.build_propedit("mkvpropedit", "/v/movie.mkv", sample(), e)
        self.assertEqual(cmd, ["mkvpropedit", "/v/movie.mkv", "--edit", "track:=14", "--set", "language=cze",
                               "--delete", "name", "--set", "flag-default=1"])


class JobTests(unittest.TestCase):
    def test_progress(self):
        self.assertEqual(jobs.progress_from_line("#GUI#progress 42%"), 42)
        self.assertIsNone(jobs.progress_from_line("hello"))

    def test_exit_codes(self):
        self.assertTrue(jobs.interpret(0, "").ok)
        o = jobs.interpret(1, "#GUI#warning something odd\n#GUI#progress 100%")
        self.assertTrue(o.ok)
        self.assertEqual(o.warnings, "something odd")
        o = jobs.interpret(2, "#GUI#error file not found")
        self.assertFalse(o.ok)
        self.assertEqual(o.error, "file not found")


class PathAndEnvTests(unittest.TestCase):
    def test_safe_path(self):
        self.assertEqual(paths.safe_output_path("/o", "../../x.srt"), os.path.join("/o", "x.srt"))
        self.assertIsNone(paths.safe_output_path("/o", ".."))

    def test_unique_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.srt")
            with open(p, "w"):
                pass
            self.assertEqual(paths.unique_path(p), os.path.join(d, "a_1.srt"))

    def test_clean_env_restores_library_path(self):
        env = clean_env({"LD_LIBRARY_PATH": "/bundle/_internal", "LD_LIBRARY_PATH_ORIG": "/usr/lib/x"})
        self.assertEqual(env["LD_LIBRARY_PATH"], "/usr/lib/x")
        env = clean_env({"LD_LIBRARY_PATH": "/bundle/_internal", "LD_LIBRARY_PATH_ORIG": ""})
        self.assertNotIn("LD_LIBRARY_PATH", env)


@unittest.skipUnless(all(find_tool(t) for t in ("mkvmerge", "mkvextract", "mkvpropedit")), "MKVToolNix not installed")
class IntegrationTests(unittest.TestCase):
    """Drives the real tools end to end through the command builders."""

    def run_cmd(self, cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(jobs.interpret(r.returncode, r.stdout).ok, True, r.stdout + r.stderr)

    def test_extract_add_and_edit_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            en = os.path.join(d, "en.srt")
            pt = os.path.join(d, "pt.srt")
            for path, text in ((en, "Hello"), (pt, "Olá")):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"1\n00:00:00,000 --> 00:00:01,000\n{text}\n")
            base = os.path.join(d, "base.mkv")
            subprocess.run(["mkvmerge", "-o", base, "--language", "0:eng", "--forced-display-flag", "0:1", en],
                           capture_output=True, check=True)
            info = read_info(base)
            self.assertEqual([t.language for t in info.tracks], ["eng"])
            self.assertTrue(info.tracks[0].forced)

            # add a Portuguese subtitle; the existing forced flag must survive
            out = os.path.join(d, "out.mkv")
            sub = commands.SubInput(pt, "por", "Português", default=True)
            self.run_cmd(commands.build_mux("mkvmerge", out, info, subs=[sub]))
            info2 = read_info(out)
            self.assertEqual([(t.language, t.forced) for t in info2.tracks], [("eng", True), ("por", False)])
            self.assertEqual(info2.tracks[1].name, "Português")

            # edit in place with mkvpropedit: a language outside the old 12-item list
            self.run_cmd(commands.build_propedit("mkvpropedit", out, info2,
                                                 {1: commands.TrackEdit(language="cze", default=False)}))
            info3 = read_info(out)
            self.assertEqual(info3.tracks[1].language, "cze")
            self.assertFalse(info3.tracks[1].default)
            self.assertTrue(info3.tracks[0].forced)

            # extract both subtitles with generated names
            taken, mapping = set(), {}
            for t in info3.tracks:
                name = naming.default_name("out", t, taken)
                taken.add(name)
                mapping[t.id] = os.path.join(d, name)
            self.run_cmd(commands.build_extract("mkvextract", out, mapping))
            for p in mapping.values():
                self.assertTrue(os.path.getsize(p) > 0, p)
            with open(next(iter(mapping.values())), encoding="utf-8") as f:
                self.assertIn("Hello", f.read())


if __name__ == "__main__":
    unittest.main()
