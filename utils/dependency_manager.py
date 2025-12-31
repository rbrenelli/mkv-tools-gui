import os
import sys
import platform
import shutil
import urllib.request
import zipfile
import tarfile
import subprocess
import stat
from pathlib import Path

class DependencyManager:
    def __init__(self):
        self.os_name = platform.system()
        self.arch = platform.machine().lower()
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Determine installation directory
        # Windows: Keep internal bin to avoid permission issues or polluting system
        # Linux/Mac: Prefer ~/.local/bin for system-wide user availability
        if self.os_name == 'Windows':
            self.bin_dir = os.path.join(self.project_root, 'bin')
        else:
            user_bin = os.path.expanduser("~/.local/bin")
            if self._ensure_dir_writable(user_bin):
                self.bin_dir = user_bin
            else:
                self.bin_dir = os.path.join(self.project_root, 'bin')

        self.urls = self._get_urls()

        # Tools we manage
        self.tools = ['ffmpeg', 'ffprobe', 'mkvmerge', 'mkvextract']

    def _ensure_dir_writable(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return os.access(path, os.W_OK)
        except Exception:
            return False

    def _get_urls(self):
        urls = {}

        # Windows
        if self.os_name == 'Windows':
            # FFmpeg & FFprobe (Essentials build contains both)
            urls['ffmpeg_pack'] = {
                'url': 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip',
                'type': 'zip',
                'contains': ['ffmpeg', 'ffprobe']
            }
            # MKVToolNix
            urls['mkvtoolnix_pack'] = {
                'url': 'https://mkvtoolnix.download/windows/releases/88.0/mkvtoolnix-64-bit-88.0.7z',
                'type': '7z',
                'contains': ['mkvmerge', 'mkvextract']
            }

        # Linux
        elif self.os_name == 'Linux':
            is_arm = 'arm' in self.arch or 'aarch64' in self.arch
            is_64 = 'x86_64' in self.arch or 'amd64' in self.arch

            # FFmpeg
            if is_arm:
                urls['ffmpeg_pack'] = {
                    'url': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz',
                    'type': 'tar',
                    'contains': ['ffmpeg', 'ffprobe']
                }
                # MKVToolNix for ARM Linux
                # We don't have a reliable portable build URL for ARM
                print(f"Warning: Automatic download of MKVToolNix for Linux ARM ({self.arch}) is not currently supported.")

            elif is_64:
                urls['ffmpeg_pack'] = {
                    'url': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz',
                    'type': 'tar',
                    'contains': ['ffmpeg', 'ffprobe']
                }
                # MKVToolNix - AppImage approach (Only works for x86_64)
                urls['mkvtoolnix_pack'] = {
                    'url': 'https://mkvtoolnix.download/appimage/MKVToolNix_GUI-x86_64.AppImage',
                    'type': 'appimage',
                    'contains': ['mkvmerge', 'mkvextract']
                }

            else:
                # 32-bit x86 (i686, i386) or other
                print(f"Warning: Automatic download for Linux ({self.arch}) is not fully supported.")
                # We could try to provide 32-bit ffmpeg:
                urls['ffmpeg_pack'] = {
                    'url': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-i686-static.tar.xz',
                    'type': 'tar',
                    'contains': ['ffmpeg', 'ffprobe']
                }
                # But MKVToolNix AppImage for 32-bit is not available from the official site easily
                # So we leave mkvtoolnix_pack undefined, which means it won't be downloaded.
                # The user will have to install it via system package manager.

        # MacOS
        elif self.os_name == 'Darwin':
            # FFmpeg
            urls['ffmpeg'] = {
                'url': 'https://evermeet.cx/ffmpeg/getrelease/zip',
                'type': 'zip',
                'contains': ['ffmpeg']
            }
            # FFprobe
            urls['ffprobe'] = {
                'url': 'https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip',
                'type': 'zip',
                'contains': ['ffprobe']
            }
            # MKVToolNix
            urls['mkvtoolnix_pack'] = {
                'url': 'https://mkvtoolnix.download/macos/MKVToolNix-88.0.dmg',
                'type': 'dmg',
                'contains': ['mkvmerge', 'mkvextract']
            }

        return urls

    def check_missing_dependencies(self):
        """Returns a list of tools that are missing from system PATH AND ./bin"""
        missing = []

        # Ensure bin directory exists (or at least check writability context implicitly via tools check)
        # We don't exit early if bin_dir doesn't exist, because we might find tools in system PATH.

        for tool in self.tools:
            # 1. Check System PATH
            if shutil.which(tool):
                continue

            # 2. Check managed bin directory
            tool_name = tool
            if self.os_name == 'Windows':
                tool_name += '.exe'

            tool_path = os.path.join(self.bin_dir, tool_name)
            if not os.path.exists(tool_path):
                missing.append(tool)

        return missing

    def get_binary_path(self, tool_name):
        """Returns absolute path to tool, prioritizing system PATH"""
        # 1. Check System PATH
        system_path = shutil.which(tool_name)
        if system_path:
            return system_path

        # 2. Check managed bin directory
        exe_name = tool_name
        if self.os_name == 'Windows':
            exe_name += '.exe'

        local_path = os.path.join(self.bin_dir, exe_name)
        if os.path.exists(local_path):
            return local_path

        # Return None or just the tool name to let subprocess fail naturally if not found
        return tool_name

    def download_dependencies(self, progress_callback=None):
        """
        Downloads missing dependencies.
        progress_callback: function(current_step, total_steps, message)
        """
        if not os.path.exists(self.bin_dir):
            try:
                os.makedirs(self.bin_dir)
            except Exception as e:
                print(f"Error creating bin directory {self.bin_dir}: {e}")
                return

        missing = self.check_missing_dependencies()
        if not missing:
            if progress_callback:
                progress_callback(1, 1, "All dependencies present.")
            return

        # Identify which packs to download based on missing tools
        packs_to_download = set()
        for tool in missing:
            for pack_name, pack_info in self.urls.items():
                if tool in pack_info['contains']:
                    packs_to_download.add(pack_name)

        if not packs_to_download:
             # Missing tools but no packs defined (e.g. 32-bit Linux for mkvmerge)
             if progress_callback:
                 progress_callback(1, 1, "Some dependencies are missing but no automatic download is available for this platform.")
             print(f"Warning: Missing tools {missing} but no download URL configured.")
             return

        total_steps = len(packs_to_download) * 2 # Download + Extract
        current_step = 0

        for pack_name in packs_to_download:
            pack_info = self.urls[pack_name]
            url = pack_info['url']

            # Download
            filename = url.split('/')[-1]
            filepath = os.path.join(self.bin_dir, filename)

            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, f"Downloading {filename}...")

            try:
                # Basic download with progress
                # Using urllib for portability
                def report(block_num, block_size, total_size):
                    # Optional: Could update progress within the step
                    pass

                urllib.request.urlretrieve(url, filepath, report)
            except Exception as e:
                print(f"Error downloading {url}: {e}")
                continue

            # Extract
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, f"Extracting {filename}...")

            try:
                self._extract_and_install(filepath, pack_info)
            except Exception as e:
                print(f"Error extracting {filename}: {e}")

            # Cleanup downloaded archive
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass

    def _extract_and_install(self, archive_path, pack_info):
        extract_type = pack_info['type']
        targets = pack_info['contains']

        if extract_type == 'zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Find the files we need inside the zip
                for file in zip_ref.namelist():
                    filename = os.path.basename(file)
                    name_no_ext = os.path.splitext(filename)[0]

                    if name_no_ext in targets or (self.os_name == 'Windows' and name_no_ext in [t + '.exe' for t in targets]):
                        # We found a target file
                        # Extract it directly to bin_dir, flattening structure
                        source = zip_ref.open(file)
                        target_filename = filename
                        target_path = os.path.join(self.bin_dir, target_filename)

                        with open(target_path, 'wb') as target_file:
                            shutil.copyfileobj(source, target_file)

                        # Make executable on Unix
                        if self.os_name != 'Windows':
                            st = os.stat(target_path)
                            os.chmod(target_path, st.st_mode | stat.S_IEXEC)

        elif extract_type == 'tar':
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                for member in tar_ref.getmembers():
                    filename = os.path.basename(member.name)
                    # Check if this is one of our tools
                    # Note: exact match on binary name usually
                    if filename in targets:
                        # Extract
                        source = tar_ref.extractfile(member)
                        if source:
                            target_path = os.path.join(self.bin_dir, filename)
                            with open(target_path, 'wb') as target_file:
                                shutil.copyfileobj(source, target_file)

                            st = os.stat(target_path)
                            os.chmod(target_path, st.st_mode | stat.S_IEXEC)

        elif extract_type == 'appimage':
            # For AppImage, we make it executable, run with --appimage-extract
            st = os.stat(archive_path)
            os.chmod(archive_path, st.st_mode | stat.S_IEXEC)

            # Extract
            subprocess.run([archive_path, '--appimage-extract'], cwd=self.bin_dir, check=True)

            # Move binaries from squashfs-root
            squash_root = os.path.join(self.bin_dir, 'squashfs-root')
            usr_bin = os.path.join(squash_root, 'usr', 'bin')

            for tool in targets:
                src = os.path.join(usr_bin, tool)
                if os.path.exists(src):
                    shutil.move(src, os.path.join(self.bin_dir, tool))

            # Cleanup
            shutil.rmtree(squash_root)

        elif extract_type == 'dmg':
            if self.os_name == 'Darwin':
                # Mount dmg
                mount_point = os.path.join(self.bin_dir, 'dmg_mount')
                os.makedirs(mount_point, exist_ok=True)
                subprocess.run(['hdiutil', 'attach', archive_path, '-mountpoint', mount_point, '-nobrowse'], check=True)

                try:
                    # Look for the app or binaries
                    # MKVToolNix dmg usually contains MKVToolNix-*.app
                    # Binaries are in MKVToolNix-*.app/Contents/MacOS/

                    # Search for the app dir
                    app_dir = None
                    for item in os.listdir(mount_point):
                        if item.endswith('.app'):
                            app_dir = os.path.join(mount_point, item)
                            break

                    if app_dir:
                        bin_source = os.path.join(app_dir, 'Contents', 'MacOS')
                        for tool in targets:
                            src = os.path.join(bin_source, tool)
                            if os.path.exists(src):
                                shutil.copy2(src, os.path.join(self.bin_dir, tool))
                finally:
                    # Unmount
                    subprocess.run(['hdiutil', 'detach', mount_point, '-force'], check=False)
                    try:
                        os.rmdir(mount_point)
                    except:
                        pass

        elif extract_type == '7z':
            # Try using 7z command if available
            try:
                subprocess.run(['7z', 'e', archive_path, f'-o{self.bin_dir}', '-r'] + [f'{t}.exe' for t in targets], check=True)
            except Exception as e:
                print(f"Failed to extract 7z: {e}. Please install 7zip or extract manually.")
