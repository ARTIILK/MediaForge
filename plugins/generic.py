import os
import re
import subprocess

class MediaPlugin:
    def __init__(self, exec_dir, download_root, ffmpeg_path, yt_dlp_module):
        self.priority = 1
        self.download_root = download_root
        self.ffmpeg_path = ffmpeg_path
        self.yt_dlp = yt_dlp_module # Store passed module

    def can_handle(self, url): return True

    def extract_info(self, url):
        with self.yt_dlp.YoutubeDL({'quiet': True, 'ffmpeg_location': self.ffmpeg_path}) as ydl:
            info = ydl.extract_info(url, download=False)
        
        v_formats, a_formats = [], []
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none':
                note = "Combined" if f.get('acodec') != 'none' else "Video Only"
                v_formats.append({
                    'format_id': f['format_id'], 'resolution': f.get('resolution', 'Unknown'), 
                    'filesize_str': f"{(f.get('filesize') or 0)/1024/1024:.2f} MB", 
                    'ext': f['ext'], 'note': note
                })
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                a_formats.append({
                    'format_id': f['format_id'], 'abr': f.get('abr', 0), 
                    'filesize_str': f"{(f.get('filesize') or 0)/1024/1024:.2f} MB", 
                    'ext': f['ext'], 'language': f.get('language', 'unk'), 'acodec': f.get('acodec')
                })
        
        return {'title': info.get('title'), 'thumbnail': info.get('thumbnail'), 'duration': info.get('duration'), 'video_formats': v_formats[:20], 'audio_formats': a_formats[:10], 'extract_time': 0}

    def download(self, task_id, data, progress_cb):
        title = re.sub(r'[<>:"/\\|?*]', '', data.get('title', 'video')).strip()[:150]
        final_path = os.path.join(self.download_root, f"{title}.mp4")

        class Hook:
            def __call__(self, d):
                if d['status'] == 'downloading': progress_cb('video', (d.get('downloaded_bytes', 0) / (d.get('total_bytes') or 1)) * 100, d.get('speed', 0))

        opts = {'format': data['video_format'], 'outtmpl': final_path, 'progress_hooks': [Hook()], 'ffmpeg_location': self.ffmpeg_path}
        
        if data.get('audio_format'):
             opts['format'] = f"{data['video_format']}+{data['audio_format']}"

        with self.yt_dlp.YoutubeDL(opts) as ydl: ydl.download([data['url']])

        return {'filename': f"{title}.mp4", 'file_size': os.path.getsize(final_path) if os.path.exists(final_path) else 0, 'download_url': f"/download/{title}.mp4"}
