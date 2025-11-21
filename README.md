MediaForge v3.2 🎬A Smart, Modular, and Local-First Video Downloader.MediaForge is a powerful desktop application built with Python (Flask) and yt-dlp that provides a modern web-based interface for downloading videos from YouTube, MX Player, Twitch, and thousands of other sites. It features a modular plugin engine, a real-time dashboard, and automatic file management.(Replace this link with a real screenshot of your dashboard)🚀 Key FeaturesSmart Extraction: Automatically detects if a site uses split streams (video+audio separate like YouTube) or combined streams (like MX Player) and adjusts the UI accordingly.Modular Plugin System: Extend functionality by adding Python scripts to your user folder. Includes dependency injection for yt_dlp.Integrated Dashboard:📥 Downloader: URL analysis with format selection (Resolution, Bitrate, Language badges).📜 History: detailed log of downloads including Quality, Language, and Size.📟 Live Logs: "Matrix-style" console to debug FFmpeg/Network issues in real-time.Auto-Cleanup: Automatically deletes video files older than 3 sessions to save disk space (while keeping the history record).Cross-Platform: Runs on Linux (Native) and Windows (Portable EXE).Privacy First: All data (logs, database, downloads) is stored locally on your machine.💿 Installation & UsageLinux (Debian/Ubuntu/Zorin OS)Download the latest .deb release.Install it:sudo dpkg -i mediaforge-deb.deb
Run via terminal (it will launch your browser):mediaforge
Windows (10/11)Download MediaForge.exe and ffmpeg.exe.Place them in the same folder.Double-click MediaForge.exe.🛠️ Building from SourceIf you want to develop or build the binaries yourself, follow these steps.PrerequisitesPython 3.8+FFmpeg (Static Build)Linux: apt install python3-venv wine (Wine is required to build the Windows EXE).1. Setup ProjectClone the repo and place the correct ffmpeg binary in the root folder:git clone [https://github.com/ARTIILK/MediaForge.git](https://github.com/ARTIILK/MediaForge.git)
cd MediaForge
# Download ffmpeg binary manually and place it here
2. Build for LinuxThis script sets up the venv, installs dependencies, and creates a .deb package.chmod +x linux_auto_build.sh
./linux_auto_build.sh
3. Build for Windows (Cross-Compile)You must have ffmpeg.exe in the folder for this to work.chmod +x windows_build.sh
./windows_build.sh
🧩 Plugin SystemMediaForge v3+ uses a hot-swappable plugin system. You can write your own downloaders without recompiling the app.Location: ~/.mediaforge/plugins/ (Linux) or %USERPROFILE%/.mediaforge/plugins/ (Windows).Default Pluginsyoutube.py: High priority. Handles separate video/audio stream merging.generic.py: Fallback. Handles standard HLS/MP4 streams.Creating a PluginCreate a .py file in the plugins folder. It must contain a MediaPlugin class:class MediaPlugin:
    def __init__(self, exec_dir, download_root, ffmpeg_path, yt_dlp_module):
        self.priority = 100
        self.yt_dlp = yt_dlp_module # Use the injected library

    def can_handle(self, url):
        return "mysite.com" in url

    def extract_info(self, url):
        # Return dict with title, thumbnails, formats[]
        pass

    def download(self, task_id, data, progress_callback):
        # Perform download logic
        pass
📂 Data LocationsMediaForge keeps your system clean by isolating its data.Data TypeLocation (Linux)Location (Windows)Downloads~/Downloads/MediaForge/Downloads\MediaForge\Logs~/.mediaforge/app.log%USERPROFILE%\.mediaforge\app.logDatabase~/.mediaforge/history.db%USERPROFILE%\.mediaforge\history.dbPlugins~/.mediaforge/plugins/%USERPROFILE%\.mediaforge\plugins\🤝 ContributingPull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.📄 LicenseMIT
