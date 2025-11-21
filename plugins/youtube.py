import os
import time
import subprocess
import re

class MediaPlugin:
    def __init__(self, exec_dir, download_root, ffmpeg_path, yt_dlp_module):
        self.priority = 10
        self.exec_dir = exec_dir
        self.download_root = download_root
        self.ffmpeg_path = ffmpeg_path
        self.yt_dlp = yt_dlp_module # Store the passed module

    def can_handle(self, url):
        return "youtube.com" in url or "youtu.be" in url

    def extract_info(self, url):
        with self.yt_dlp.YoutubeDL({'quiet': True, 'ffmpeg_location': self.ffmpeg_path}) as ydl:
            info = ydl.extract_info(url, download=False)
        
        v_formats = [
            {'format_id': f['format_id'], 'resolution': f.get('resolution', 'N/A'), 'filesize_str': f"{(f.get('filesize') or 0)/1024/1024:.2f} MB", 'ext': f['ext']}
            for f in info.get('formats', []) if f.get('vcodec') != 'none' and f.get('acodec') == 'none'
        ]
        a_formats = [
            {'format_id': f['format_id'], 'abr': f.get('abr', 0), 'filesize_str': f"{(f.get('filesize') or 0)/1024/1024:.2f} MB", 'ext': f['ext'], 'language': f.get('language', 'unk')}
            for f in info.get('formats', []) if f.get('acodec') != 'none' and f.get('vcodec') == 'none'
        ]
        return {'title': info.get('title'), 'thumbnail': info.get('thumbnail'), 'duration': info.get('duration'), 'video_formats': v_formats[:10], 'audio_formats': a_formats[:5], 'extract_time': 0}

    def download(self, task_id, data, progress_cb):
        temp_dir = os.path.join(self.download_root, 'temp') 
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        
        v_temp = os.path.join(temp_dir, f"{task_id}_v.mp4")
        a_temp = os.path.join(temp_dir, f"{task_id}_a.m4a")
        title = re.sub(r'[<>:"/\\|?*]', '', data.get('title', 'video')).strip()[:150]
        final_path = os.path.join(self.download_root, f"{title}.mp4")

        class Hook:
            def __init__(self, t): self.t = t
            def __call__(self, d):
                if d['status'] == 'downloading': progress_cb(self.t, (d.get('downloaded_bytes', 0) / (d.get('total_bytes') or 1)) * 100, d.get('speed', 0))

        for fmt, path, type in [(data['video_format'], v_temp, 'video'), (data['audio_format'], a_temp, 'audio')]:
            with self.yt_dlp.YoutubeDL({'format': fmt, 'outtmpl': path, 'progress_hooks': [Hook(type)], 'ffmpeg_location': self.ffmpeg_path, 'quiet':True}) as ydl:
                ydl.download([data['url']])

        subprocess.run([self.ffmpeg_path, '-y', '-i', v_temp, '-i', a_temp, '-c', 'copy', final_path], check=True)
        if os.path.exists(v_temp): os.remove(v_temp)
        if os.path.exists(a_temp): os.remove(a_temp)

        return {'filename': f"{title}.mp4", 'file_size': os.path.getsize(final_path), 'download_url': f"/download/{title}.mp4"}
