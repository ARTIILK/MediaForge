# MediaForge v3.2 🎬

**A Smart, Modular, and Local-First Video Downloader.**

MediaForge is a powerful desktop application built with Python (Flask) and `yt-dlp` that provides a modern web-based interface for downloading videos from YouTube, MX Player, Twitch, and thousands of other sites. It features a modular plugin engine, a real-time dashboard, and automatic file management.

*(Replace this link with a real screenshot of your dashboard)*

-----

## 🚀 Key Features

* **Smart Extraction**: Automatically detects if a site uses split streams (video+audio separate like YouTube) or combined streams (like MX Player) and adjusts the UI accordingly.
* **Modular Plugin System**: Extend functionality by adding Python scripts to your user folder. Includes dependency injection for `yt_dlp`.
* **Integrated Dashboard**:
    * **📥 Downloader**: URL analysis with format selection (Resolution, Bitrate, Language badges).
    * **📜 History**: Detailed log of downloads including Quality, Language, and Size.
    * **📟 Live Logs**: "Matrix-style" console to debug FFmpeg/Network issues in real-time.
* **Auto-Cleanup**: Automatically deletes video files older than 3 sessions to save disk space (while keeping the history record).
* **Cross-Platform**: Runs on Linux (Native) and Windows (Portable EXE).
* **Privacy First**: All data (logs, database, downloads) is stored locally on your machine.

-----

## 💿 Installation & Usage

### Linux (Debian/Ubuntu/Zorin OS)

1.  Download the latest `.deb` release.
2.  Install it:
    ```bash
    sudo dpkg -i mediaforge-deb.deb
    ```
3.  Run via terminal (it will launch your browser):
    ```bash
    mediaforge
    ```

### Windows (10/11)

1.  Download `MediaForge.exe` and `ffmpeg.exe`.
2.  Place them in the same folder.
3.  Double-click `MediaForge.exe`.

-----

## 🛠️ Building from Source

If you want to develop or build the binaries yourself, follow these steps.

### Prerequisites

* Python 3.8+
* FFmpeg (Static Build)
* **Linux**: `apt install python3-venv wine` (Wine is required to build the Windows EXE).

### 1. Setup Project

Clone the repo and place the correct `ffmpeg` binary in the root folder:

```bash
git clone [https://github.com/ARTIILK/MediaForge.git](https://github.com/ARTIILK/MediaForge.git)
cd MediaForge
# Download ffmpeg binary manually and place it here
