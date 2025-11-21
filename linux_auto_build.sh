#!/bin/bash
echo "Building MediaForge V3..."

# 1. Prepare Directories
mkdir -p templates static/js
mv index.html templates/ 2>/dev/null
if [ ! -f "static/js/tailwindcss.js" ]; then
    curl -L -o static/js/tailwindcss.js https://cdn.tailwindcss.com
fi

# 2. Setup Venv
python3 -m venv venv
source venv/bin/activate
pip install flask yt-dlp pyinstaller

# 3. Build (Now including Plugins!)
rm -rf build dist mediaforge.spec
pyinstaller --noconfirm --onefile --windowed \
    --name "mediaforge" \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "plugins:plugins" \
    --add-binary "ffmpeg:." \
    app.py

# 4. Package
mkdir -p mediaforge-deb/usr/local/bin
mkdir -p mediaforge-deb/DEBIAN
cp dist/mediaforge mediaforge-deb/usr/local/bin/
chmod +x mediaforge-deb/usr/local/bin/mediaforge

cat > mediaforge-deb/DEBIAN/control <<EOF
Package: mediaforge
Version: 3.0
Architecture: amd64
Maintainer: You
Description: MediaForge V3 - Smart Video Downloader
EOF

dpkg-deb --build mediaforge-deb
echo "Build Complete: mediaforge-deb.deb"
