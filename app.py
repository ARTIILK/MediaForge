import os
import sys
import time
import uuid
import threading
import logging
from logging.handlers import RotatingFileHandler
import webbrowser
import sqlite3
import importlib.util
import shutil
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

# --- 1. Setup Paths ---
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    BASE_DIR = sys._MEIPASS 
    EXEC_DIR = os.path.dirname(sys.executable)
    USER_HOME = os.path.expanduser("~")
    DATA_DIR = os.path.join(USER_HOME, ".mediaforge")
    DOWNLOAD_ROOT = os.path.join(USER_HOME, "Downloads", "MediaForge")
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    EXEC_DIR = BASE_DIR
    DATA_DIR = BASE_DIR
    DOWNLOAD_ROOT = os.path.join(BASE_DIR, "downloads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

PLUGINS_DIR = os.path.join(DATA_DIR, 'plugins')
INTERNAL_PLUGINS_DIR = os.path.join(BASE_DIR, 'plugins')

# --- 2. Advanced Logging (Rotating + Session Separator) ---
log_file = os.path.join(DATA_DIR, 'app.log')

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove default handlers to avoid duplication
if logger.hasHandlers():
    logger.handlers.clear()

# Add Rotating File Handler (Max 1MB, keep 1 backup)
handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=1, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Mark new session
logger.info("\n" + "="*40 + "\n=== NEW SESSION STARTED ===\n" + "="*40)

# --- 3. Database & Cleanup Logic ---
DB_PATH = os.path.join(DATA_DIR, 'history.db')

def init_db():
    """Initialize DB and perform migrations if columns are missing."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create Base Table
        c.execute('''CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            task_id TEXT, 
            url TEXT, 
            filename TEXT, 
            file_size INTEGER, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # MIGRATION: Add new columns if they don't exist
        try: c.execute("ALTER TABLE downloads ADD COLUMN quality TEXT")
        except: pass
        try: c.execute("ALTER TABLE downloads ADD COLUMN language TEXT")
        except: pass
        try: c.execute("ALTER TABLE downloads ADD COLUMN sessions_old INTEGER DEFAULT 0")
        except: pass
        try: c.execute("ALTER TABLE downloads ADD COLUMN deleted INTEGER DEFAULT 0")
        except: pass

        conn.commit()
        conn.close()
    except Exception as e: 
        logger.error(f"DB Init Error: {e}")

def run_auto_cleanup():
    """Delete files downloaded 3+ sessions ago."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. Increment age for all non-deleted files
        c.execute("UPDATE downloads SET sessions_old = sessions_old + 1 WHERE deleted = 0")
        
        # 2. Find files to delete (Age >= 3)
        c.execute("SELECT id, filename FROM downloads WHERE sessions_old >= 3 AND deleted = 0")
        targets = c.fetchall()
        
        for row_id, filename in targets:
            file_path = os.path.join(DOWNLOAD_ROOT, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleanup: Deleted old file '{filename}'")
                except Exception as del_err:
                    logger.error(f"Cleanup Failed for '{filename}': {del_err}")
            
            # Mark as deleted in DB
            c.execute("UPDATE downloads SET deleted = 1 WHERE id = ?", (row_id,))
            
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Auto Cleanup Error: {e}")

def log_db(task_id, url, filename, size, quality, language):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO downloads 
            (task_id, url, filename, file_size, quality, language, sessions_old, deleted) 
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)''', 
            (task_id, url, filename, size, quality, language))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Log Error: {e}")

def resource_path(relative_path): return os.path.join(BASE_DIR, relative_path)
def get_ffmpeg_path():
    path = os.path.join(EXEC_DIR, 'ffmpeg')
    return path if os.path.exists(path) else 'ffmpeg'

def sanitize_filename(name):
    # Aggressive sanitization to prevent 404s and filesystem errors
    # Strip hashtags, questions, slashes, and non-printable chars
    name = re.sub(r'[<>:"/\\|?*#]', '', name)
    name = "".join(c for c in name if c.isprintable())
    return name.strip()[:200]

# --- 4. Plugin Manager (Same as v3.1) ---
loaded_plugins = []

def load_plugins():
    global loaded_plugins
    loaded_plugins = []
    
    if not os.path.exists(PLUGINS_DIR): os.makedirs(PLUGINS_DIR)
    
    if IS_FROZEN and os.path.exists(INTERNAL_PLUGINS_DIR):
        try:
            for filename in os.listdir(INTERNAL_PLUGINS_DIR):
                src = os.path.join(INTERNAL_PLUGINS_DIR, filename)
                dst = os.path.join(PLUGINS_DIR, filename)
                if filename.endswith(".py") and not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    logger.info(f"Installed default plugin: {filename}")
        except Exception as e: logger.error(f"Failed to copy defaults: {e}")

    logger.info(f"Scanning plugins in {PLUGINS_DIR}")
    
    for filename in os.listdir(PLUGINS_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                module_name = filename[:-3]
                file_path = os.path.join(PLUGINS_DIR, filename)
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'MediaPlugin'):
                    plugin = module.MediaPlugin(EXEC_DIR, DOWNLOAD_ROOT, get_ffmpeg_path(), yt_dlp)
                    loaded_plugins.append(plugin)
                    logger.info(f"Loaded: {module_name}")
            except Exception as e: logger.error(f"Plugin Load Error ({filename}): {e}")
    
    loaded_plugins.sort(key=lambda x: x.priority, reverse=True)

def get_plugin_for_url(url):
    for plugin in loaded_plugins:
        if plugin.can_handle(url): return plugin
    return None

# --- 5. Routes ---
template_dir = resource_path('templates')
static_dir = resource_path('static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
tasks = {}

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    plugin = get_plugin_for_url(url)
    if not plugin: return jsonify({'error': 'No supported plugin found'}), 400
    try: return jsonify(plugin.extract_info(url))
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    plugin = get_plugin_for_url(data.get('url'))
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'progress': {'video': {'percent': 0, 'speed': 0}, 'audio': {'percent': 0, 'speed': 0}}}

    def worker():
        try:
            def progress_cb(type, p, s): tasks[task_id]['progress'][type] = {'percent': p, 'speed': s}
            tasks[task_id]['status'] = 'processing'
            
            # Pre-Sanitize title
            if 'title' in data:
                data['title'] = sanitize_filename(data['title'])
            
            result = plugin.download(task_id, data, progress_cb)
            
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = result
            
            # Log with new detailed fields
            log_db(
                task_id, 
                data.get('url'), 
                result['filename'], 
                result['file_size'],
                data.get('quality_label', 'Unknown'), # New
                data.get('language', 'Unknown')       # New
            )
        except Exception as e:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = str(e)
            logger.error(f"Task Failed: {e}")

    threading.Thread(target=worker).start()
    return jsonify({'task_id': task_id})

@app.route('/api/progress/<task_id>')
def get_progress(task_id): return jsonify(tasks.get(task_id) or {'error': 'Not found'})

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_ROOT, filename, as_attachment=True)

@app.route('/api/logs')
def get_logs():
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Return last 100 lines
                return jsonify({'logs': f.readlines()[-100:]})
    except: pass
    return jsonify({'logs': []})

@app.route('/api/history')
def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Fetch latest 50
        c.execute("SELECT * FROM downloads ORDER BY timestamp DESC LIMIT 50")
        return jsonify([dict(row) for row in c.fetchall()])
    except: return jsonify([])

if __name__ == '__main__':
    init_db()
    run_auto_cleanup() # Clean old files on start
    load_plugins()
    if not IS_FROZEN: 
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open('http://127.0.0.1:5000'))).start()
    app.run(port=5000)
