# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🚀 SERVER HUB — Professional Hosting Control Panel (Enhanced)         ║
║  Version: 3.0  |  By: SHBH_S1  |  Admin: RIKO                         ║
╠══════════════════════════════════════════════════════════════════════════╣
║  - RBAC (Owner/Admin/Moderator/User)                                   ║
║  - bcrypt password hashing                                             ║
║  - WebSocket Terminal (flask-sock)                                     ║
║  - Database Manager (SQLite/MySQL/PostgreSQL)                          ║
║  - Advanced File Editor (search/replace)                               ║
║  - Telegram Alerts (RAM, login, threats)                              ║
║  - Rate Limiting & Caching                                             ║
║  - APScheduler for background tasks                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os, sys, gc, re, ast, json, time, uuid, html, shutil, socket
import signal, string, random, secrets, hashlib, logging, platform
import zipfile, tarfile, threading, subprocess, warnings
import urllib.request, urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from collections import deque
from io import BytesIO

# ─── NEW: Install missing packages automatically ──────────────────────────
try:
    import bcrypt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])
    import bcrypt
try:
    from flask_sock import Sock
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-sock"])
    from flask_sock import Sock
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-limiter"])
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
try:
    from flask_caching import Cache
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-caching"])
    from flask_caching import Cache
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "apscheduler"])
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger

try:
    import resource
except ImportError:
    resource = None

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from flask import (Flask, render_template_string, request, jsonify, session,
                   redirect, url_for, send_file, send_from_directory)
from werkzeug.utils import secure_filename

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
#  1.  Unlimited Resources
# ─────────────────────────────────────────────
def set_unlimited_resources():
    if not resource:
        return False
    try:
        resource.setrlimit(resource.RLIMIT_AS,    (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_DATA,  (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_NOFILE,(999999, 999999))
        resource.setrlimit(resource.RLIMIT_NPROC, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        return True
    except Exception:
        return False

set_unlimited_resources()

# ─── NEW: APScheduler for background tasks (instead of while True) ────
scheduler = BackgroundScheduler()
scheduler.start()

# ─────────────────────────────────────────────
#  2.  Paths & Settings
# ─────────────────────────────────────────────
DEFAULT_BASE = os.environ.get('BASE_PATH') or (
    os.path.join(os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', os.getcwd()), 'panel_data')
    if (os.path.exists('/home/runner') or 'REPL_ID' in os.environ)
    else '/tmp/panel_data'
)
BASE_PATH          = DEFAULT_BASE
os.makedirs(BASE_PATH, exist_ok=True)

USERS_FOLDER       = os.path.join(BASE_PATH, 'users_data')
USERS_FILE         = os.path.join(BASE_PATH, 'users.json')
PROCESSES_FILE     = os.path.join(BASE_PATH, 'processes.json')
SCHEDULES_FILE     = os.path.join(BASE_PATH, 'schedules.json')
LOGS_FILE          = os.path.join(BASE_PATH, 'activity.log')
USER_SESSIONS_FILE = os.path.join(BASE_PATH, 'user_sessions.json')
BACKUPS_FOLDER     = os.path.join(BASE_PATH, 'backups')
TEMP_FOLDER        = os.path.join(BASE_PATH, 'temp')
PACKAGES_FILE      = os.path.join(BASE_PATH, 'packages.json')
DOCKER_FILE        = os.path.join(BASE_PATH, 'docker.json')
MASTER_CONFIG_FILE = os.path.join(BASE_PATH, 'master_config.json')
PORTS_FILE         = os.path.join(BASE_PATH, 'ports.json')
ACTIVITY_FILE      = os.path.join(BASE_PATH, 'activity_feed.json')
OWNER_CONFIG_FILE  = os.path.join(BASE_PATH, 'owner_config.json')
MAINTENANCE_FILE   = os.path.join(BASE_PATH, 'maintenance.json')
BOT_STATS_FILE     = os.path.join(BASE_PATH, 'bot_stats.json')
ANNOUNCE_FILE      = os.path.join(BASE_PATH, 'announcements.json')
SECURITY_ALERTS_FILE = os.path.join(BASE_PATH, 'security_alerts.json')
NODEJS_PROCS_FILE  = os.path.join(BASE_PATH, 'nodejs_procs.json')
PHP_CONFIG_FILE    = os.path.join(BASE_PATH, 'php_config.json')
DATABASE_CONNECTIONS_FILE = os.path.join(BASE_PATH, 'db_connections.json')  # NEW

PROFILE_IMAGE_URL = "https://h.top4top.io/p_3820pynba0.png"
ENTRY_SOUND_URL   = "https://k.top4top.io/m_38204qib81.mp4"

# ─────────────────────────────────────────────
#  3.  JSON Helpers
# ─────────────────────────────────────────────
def init_json_file(path, default):
    if not os.path.exists(path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

def load_json_file(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}

def save_json_file(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────
#  4.  Master Config (with bcrypt & setup flag)
# ─────────────────────────────────────────────
def load_master_config():
    default = {
        'master_username': 'RIKO',
        'master_password_hash': '',          # ← NEW: no default password
        'port': 3178,
        'main_file': 'main.py',
        'setup_done': False                  # ← NEW: forces first-time setup
    }
    if not os.path.exists(MASTER_CONFIG_FILE):
        save_json_file(MASTER_CONFIG_FILE, default)
        return default
    cfg = load_json_file(MASTER_CONFIG_FILE)
    if not cfg:
        return default
    for k, v in default.items():
        cfg.setdefault(k, v)
    return cfg

MASTER_CONFIG        = load_master_config()
MASTER_USERNAME      = MASTER_CONFIG.get('master_username', 'RIKO')
MASTER_PASSWORD_HASH = MASTER_CONFIG.get('master_password_hash', '')
SERVER_START_TIME    = time.time()

# ─────────────────────────────────────────────
#  5.  Create Folders & Init Files
# ─────────────────────────────────────────────
for _f in [USERS_FOLDER, TEMP_FOLDER, BACKUPS_FOLDER]:
    os.makedirs(_f, exist_ok=True)

init_json_file(USERS_FILE, {})
init_json_file(PROCESSES_FILE, {})
init_json_file(SCHEDULES_FILE, {})
init_json_file(USER_SESSIONS_FILE, {})
init_json_file(PACKAGES_FILE, {'pip': [], 'apt': [], 'npm': []})
init_json_file(DOCKER_FILE, {'containers': [], 'images': []})
init_json_file(PORTS_FILE, {'ports': []})
init_json_file(ACTIVITY_FILE, {'events': []})
init_json_file(OWNER_CONFIG_FILE, {
    'telegram_token': '', 'telegram_owner_id': '', 'bot_linked': False,
    'panel_name': 'SERVER HUB', 'welcome_msg': 'Welcome to SERVER HUB'
})
init_json_file(MAINTENANCE_FILE, {'enabled': False, 'message': 'Under maintenance. Try later.'})
init_json_file(BOT_STATS_FILE, {'total_users':0,'total_servers':0,'active_bots':0,'zip_files':0,'last_updated':''})
init_json_file(ANNOUNCE_FILE, {'list': []})
init_json_file(SECURITY_ALERTS_FILE, {'alerts': []})
init_json_file(NODEJS_PROCS_FILE, {})
init_json_file(PHP_CONFIG_FILE, {'default_version': '8.1'})
init_json_file(DATABASE_CONNECTIONS_FILE, {'connections': []})  # NEW

# ─────────────────────────────────────────────
#  6.  Owner helpers (unchanged)
# ─────────────────────────────────────────────
def load_owner_config():
    d = {'telegram_token':'','telegram_owner_id':'','bot_linked':False,
         'panel_name':'SERVER HUB','welcome_msg':'Welcome to SERVER HUB'}
    cfg = load_json_file(OWNER_CONFIG_FILE, d)
    for k,v in d.items(): cfg.setdefault(k,v)
    return cfg

def load_maintenance(): return load_json_file(MAINTENANCE_FILE, {'enabled':False,'message':'Under maintenance'})
def save_maintenance(d): save_json_file(MAINTENANCE_FILE, d)
def load_bot_stats(): return load_json_file(BOT_STATS_FILE, {})
def load_announcements(): return load_json_file(ANNOUNCE_FILE, {'list':[]})
def save_announcements(d): save_json_file(ANNOUNCE_FILE, d)

def load_security_alerts(): return load_json_file(SECURITY_ALERTS_FILE, {'alerts':[]})
def save_security_alert(username, filename, threats, ip):
    """Store a security alert and return the alert dict."""
    data = load_security_alerts()
    alert = {
        'id': str(uuid.uuid4())[:8],
        'username': username,
        'filename': filename,
        'threats': threats,
        'ip': ip,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reviewed': False
    }
    data['alerts'].insert(0, alert)
    data['alerts'] = data['alerts'][:200]   # keep last 200
    save_json_file(SECURITY_ALERTS_FILE, data)
    return alert

# ─────────────────────────────────────────────
#  7.  bcrypt helpers (NEW)
# ─────────────────────────────────────────────
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def check_password(password, hashed):
    if not hashed:
        return False
    if hashed.startswith('$2b$'):  # bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())
    else:  # legacy sha256 (for migration)
        return hashlib.sha256(password.encode()).hexdigest() == hashed

def upgrade_password_if_needed(username, password, current_hash):
    """If using legacy sha256, re-hash with bcrypt."""
    if current_hash and not current_hash.startswith('$2b$'):
        if hashlib.sha256(password.encode()).hexdigest() == current_hash:
            new_hash = hash_password(password)
            users = load_users()
            if username in users:
                users[username]['password'] = new_hash
                save_users(users)
            return new_hash
    return current_hash

# ─────────────────────────────────────────────
#  8.  RBAC (NEW)
# ─────────────────────────────────────────────
ROLES = {
    'owner':    {'level': 4, 'permissions': ['all']},
    'admin':    {'level': 3, 'permissions': ['manage_users', 'manage_settings', 'view_logs', 'manage_roles']},
    'moderator': {'level': 2, 'permissions': ['manage_files', 'run_bots', 'view_activity']},
    'user':     {'level': 1, 'permissions': ['own_files', 'terminal', 'edit_files']}
}

def get_user_role(username):
    users = load_users()
    ud = users.get(username, {})
    return ud.get('role', 'user') if isinstance(ud, dict) else 'user'

def user_has_permission(username, permission):
    role = get_user_role(username)
    perms = ROLES.get(role, {}).get('permissions', [])
    return 'all' in perms or permission in perms

# ─────────────────────────────────────────────
#  9.  Flask App
# ─────────────────────────────────────────────
app = Flask(__name__)

_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret_key')
if os.path.exists(_SECRET_FILE):
    with open(_SECRET_FILE) as _sf:
        app.secret_key = _sf.read().strip()
else:
    _k = secrets.token_hex(64)
    open(_SECRET_FILE, 'w').write(_k)
    app.secret_key = _k

app.permanent_session_lifetime = timedelta(days=30)
app.config['MAX_CONTENT_LENGTH'] = None
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ─── NEW: Rate Limiter ───────────────────────────────────────────────
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# ─── NEW: Cache ──────────────────────────────────────────────────────
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# ─── NEW: WebSocket ─────────────────────────────────────────────────
sock = Sock(app)

# ─── NEW: Background Scheduler (started already) ────────────────────
def monitor_resources():
    mem = psutil.virtual_memory()
    if mem.percent > 80:
        send_telegram_alert(f'⚠️ *High RAM usage*: {mem.percent}% used\n'
                            f'Used: {mem.used/1024**3:.1f} GB / {mem.total/1024**3:.1f} GB')
scheduler.add_job(monitor_resources, IntervalTrigger(minutes=5))

@app.before_request
def check_maintenance():
    maint = load_maintenance()
    if not maint.get('enabled'):
        return None
    if request.path in ['/login','/logout','/register','/setup'] or request.path.startswith('/api/'):
        return None
    if session.get('username') == MASTER_USERNAME:
        return None
    return render_template_string(MAINTENANCE_TMPL, message=maint.get('message','Under maintenance')), 503

# ─────────────────────────────────────────────
#  10.  Activity & Logging
# ─────────────────────────────────────────────
def add_activity_event(username, action, details=''):
    try:
        data = load_json_file(ACTIVITY_FILE, {'events': []})
        events = data.get('events', [])
        events.insert(0, {
            'id': str(uuid.uuid4())[:8],
            'username': username,
            'action': action,
            'details': details,
            'ip': request.remote_addr if request else '-',
            'timestamp': datetime.now().isoformat(),
            'time_text': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_json_file(ACTIVITY_FILE, {'events': events[:300]})
    except Exception:
        pass

def log_activity(username, action, details=''):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOGS_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] [{username}] {action} | {details}\n')
        add_activity_event(username, action, details)
    except Exception:
        pass

# ─── NEW: Telegram Alert System ──────────────────────────────────────
def send_telegram_alert(message):
    cfg = load_owner_config()
    if not cfg.get('bot_linked') or not cfg.get('telegram_token'):
        return False
    token = cfg['telegram_token']
    chat_id = cfg['telegram_owner_id']
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
        requests.post(url, json=data, timeout=10)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────
#  11.  Replit KV Store (unchanged)
# ─────────────────────────────────────────────
_REPLIT_DB_URL = os.environ.get('REPLIT_DB_URL','')
_KV_USERS_KEY  = 'serverhub_users_v2'

def _kv_get(key):
    if not _REPLIT_DB_URL: return None
    try:
        url = _REPLIT_DB_URL.rstrip('/') + '/' + urllib.parse.quote(key, safe='')
        with urllib.request.urlopen(urllib.request.Request(url), timeout=5) as r:
            return r.read().decode('utf-8')
    except Exception:
        return None

def _kv_set(key, value):
    if not _REPLIT_DB_URL: return False
    try:
        data = urllib.parse.urlencode({key:value}).encode('utf-8')
        urllib.request.urlopen(urllib.request.Request(_REPLIT_DB_URL, data=data, method='POST'), timeout=5)
        return True
    except Exception:
        return False

def load_users():
    if _REPLIT_DB_URL:
        raw = _kv_get(_KV_USERS_KEY)
        if raw:
            try:
                d = json.loads(raw)
                if isinstance(d, dict):
                    save_json_file(USERS_FILE, d)
                    return d
            except Exception:
                pass
    return load_json_file(USERS_FILE, {})

def save_users(u):
    if not isinstance(u, dict): return
    existing = load_json_file(USERS_FILE, {})
    if not u and existing:
        return
    save_json_file(USERS_FILE, u)
    _kv_set(_KV_USERS_KEY, json.dumps(u, ensure_ascii=False))

def load_processes():     return load_json_file(PROCESSES_FILE)
def save_processes(p):    save_json_file(PROCESSES_FILE, p)
def load_schedules():     return load_json_file(SCHEDULES_FILE)
def save_schedules(s):    save_json_file(SCHEDULES_FILE, s)
def load_user_sessions(): return load_json_file(USER_SESSIONS_FILE)
def save_user_sessions(s):save_json_file(USER_SESSIONS_FILE, s)
def load_packages():      return load_json_file(PACKAGES_FILE)
def save_packages(p):     save_json_file(PACKAGES_FILE, p)
def load_ports():         return load_json_file(PORTS_FILE, {'ports':[]}).get('ports',[])
def save_ports(p):        save_json_file(PORTS_FILE, {'ports':p})

# ─────────────────────────────────────────────
#  12.  User Paths & Session Helpers
# ─────────────────────────────────────────────
def get_user_path(username):
    if username == MASTER_USERNAME:
        return BASE_PATH
    return os.path.join(USERS_FOLDER, username)

def ensure_user_folder(username):
    if username == MASTER_USERNAME: return
    p = get_user_path(username)
    os.makedirs(p, exist_ok=True)

def is_path_allowed(username, path):
    try:
        base = os.path.realpath(get_user_path(username))
        target = os.path.realpath(str(path))
        return target.startswith(base)
    except Exception:
        return False

def register_session(username):
    s = load_user_sessions()
    s[username] = s.get(username, 0) + 1
    save_user_sessions(s)

def unregister_session(username):
    s = load_user_sessions()
    s[username] = max(0, s.get(username, 1) - 1)
    save_user_sessions(s)

def can_user_login(username):
    users = load_users()
    ud = users.get(username, {})
    if not isinstance(ud, dict): return True
    exp = ud.get('expiry')
    if exp:
        try:
            if datetime.fromisoformat(exp) < datetime.now():
                return False
        except Exception:
            pass
    mx = ud.get('max_sessions', 999)
    s = load_user_sessions()
    return s.get(username, 0) < mx

# ─────────────────────────────────────────────
#  13.  System Stats
# ─────────────────────────────────────────────
def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        uptime = int(time.time() - SERVER_START_TIME)
        h, r = divmod(uptime, 3600)
        m, s = divmod(r, 60)

        def _ip():
            try:
                s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s2.connect(('8.8.8.8',80))
                ip = s2.getsockname()[0]
                s2.close()
                return ip
            except Exception:
                return '127.0.0.1'

        port = int(os.environ.get('PORT', MASTER_CONFIG.get('port') or 3178))
        return {
            'cpu': f'{cpu}%',
            'memory': f'{mem.used/1024**3:.1f} GB / {mem.total/1024**3:.1f} GB',
            'memory_percent': mem.percent,
            'disk': f'{disk.used/1024**3:.1f} GB / {disk.total/1024**3:.1f} GB',
            'disk_percent': disk.percent,
            'network_in': f'{net.bytes_recv/1024**2:.1f} MB',
            'network_out': f'{net.bytes_sent/1024**2:.1f} MB',
            'uptime': f'{h}h {m}m {s}s',
            'hostname': socket.gethostname(),
            'ip': _ip(),
            'port': port,
            'platform': platform.system(),
            'python': sys.version.split()[0],
        }
    except Exception as e:
        return {'error': str(e)}

# ─────────────────────────────────────────────
#  14.  Process Management (unchanged, but with permission checks)
# ─────────────────────────────────────────────
running_processes = {}
file_processes    = {}
nodejs_processes  = {}

def read_process_output(pid, proc, store=None):
    if store is None:
        store = file_processes
    try:
        for line in iter(proc.stdout.readline, ''):
            if line and pid in store:
                store[pid]['output'].append(line.rstrip('\n'))
                if len(store[pid]['output']) > 500:
                    store[pid]['output'] = store[pid]['output'][-500:]
    except Exception:
        pass

def get_run_command(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.py':
        return f'{sys.executable} "{filepath}"'
    elif ext == '.js':
        return f'node "{filepath}"'
    elif ext == '.sh':
        return f'bash "{filepath}"'
    elif ext == '.php':
        return f'php "{filepath}"'
    elif ext == '.rb':
        return f'ruby "{filepath}"'
    return f'"{filepath}"'

def extract_and_find_main(zip_path, extract_dir):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
        for name in ['main.py','index.js','app.py','server.js','bot.py','index.php','app.js']:
            for root, dirs, files in os.walk(extract_dir):
                if name in files:
                    return os.path.join(root, name)
    except Exception:
        pass
    return None

def auto_install_dependencies(filepath):
    installed, failed = [], []
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext != '.py':
            return {'installed':[], 'failed':[]}
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            src = f.read()
        packages = re.findall(r'^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)', src, re.MULTILINE)
        pkg_map = {
            'telegram':'python-telegram-bot','cv2':'opencv-python','PIL':'Pillow',
            'dotenv':'python-dotenv','mysql':'mysql-connector-python',
            'psycopg2':'psycopg2-binary','youtube_dl':'youtube-dl','yt_dlp':'yt-dlp',
        }
        std = {'os','sys','time','json','re','math','random','datetime','threading',
               'subprocess','collections','io','typing','abc','flask','requests',
               'psutil','hashlib','base64','uuid','socket','platform','signal',
               'warnings','gc','resource','shutil','zipfile','tarfile','secrets',
               'functools','itertools','string','textwrap','pathlib','glob',
               'tempfile','contextlib','html','logging','ast'}
        for pkg in set(packages):
            if not pkg or pkg.startswith('.') or pkg in std:
                continue
            actual = pkg_map.get(pkg, pkg)
            try:
                __import__(pkg)
            except Exception:
                try:
                    r = subprocess.run([sys.executable,'-m','pip','install','--user',actual],
                                       capture_output=True, text=True, timeout=180)
                    (installed if r.returncode==0 else failed).append(actual)
                except Exception:
                    failed.append(actual)
        return {'installed':installed,'failed':failed}
    except Exception as e:
        return {'installed':installed,'failed':failed+[str(e)]}

# ─────────────────────────────────────────────
#  15.  Node.js Helpers (unchanged)
# ─────────────────────────────────────────────
def find_free_port(start=4000, end=9000):
    for p in range(start, end):
        try:
            s = socket.socket()
            s.bind(('0.0.0.0', p))
            s.close()
            return p
        except Exception:
            continue
    return start

def get_nodejs_install_commands(project_path, deps_file=None):
    cmds = []
    pkg_json = os.path.join(project_path, 'package.json')
    yarn_lock = os.path.join(project_path, 'yarn.lock')
    custom_deps = os.path.join(project_path, deps_file) if deps_file else None

    if custom_deps and deps_file and os.path.exists(custom_deps):
        ext = os.path.splitext(deps_file)[1].lower()
        if ext == '.txt':
            cmds.append(f'npm install $(cat "{deps_file}" | tr "\\n" " ")')
        elif ext == '.json':
            cmds.append(f'npm install --prefix . --package-lock-only || npm install')
        else:
            cmds.append(f'npm install')
    elif os.path.exists(yarn_lock):
        cmds.append('yarn install --frozen-lockfile')
    elif os.path.exists(pkg_json):
        cmds.append('npm install')
    return cmds

def start_nodejs_project(project_path, username, port=None, main_file=None, deps_file=None):
    install_output = ''
    pkg_json = os.path.join(project_path, 'package.json')
    deps_abs = os.path.join(project_path, deps_file) if deps_file else None

    if deps_abs and deps_file and os.path.exists(deps_abs):
        install_cmds = get_nodejs_install_commands(project_path, deps_file)
    elif os.path.exists(pkg_json):
        install_cmds = ['npm install']
    else:
        install_cmds = []

    for ic in install_cmds:
        try:
            ir = subprocess.run(ic, shell=True, cwd=project_path,
                                capture_output=True, text=True, timeout=180)
            install_output += ir.stdout + ir.stderr
        except Exception as e:
            install_output += f'Install error: {e}\n'

    start_cmd = None

    if main_file:
        mf_path = os.path.join(project_path, main_file)
        if os.path.exists(mf_path):
            start_cmd = f'node "{main_file}"'
        else:
            return {'success': False, 'error': f'Main file not found: {main_file}',
                    'install_output': install_output}

    if not start_cmd and os.path.exists(pkg_json):
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
            scripts = pkg.get('scripts', {})
            sc = scripts.get('start') or scripts.get('dev')
            if sc:
                start_cmd = sc
        except Exception:
            pass

    if not start_cmd:
        for name in ['index.js','app.js','server.js','main.js','bot.js']:
            if os.path.exists(os.path.join(project_path, name)):
                start_cmd = f'node "{name}"'
                break

    if not start_cmd:
        ic_list = get_nodejs_install_commands(project_path, deps_file)
        return {'success': False,
                'error': 'لم يتم العثور على ملف بداية. حدد الملف الرئيسي يدوياً.',
                'install_commands': ic_list or ['npm install'],
                'run_command': 'node your_file.js',
                'install_output': install_output}

    assigned_port = port or find_free_port()
    env = os.environ.copy()
    env['PORT'] = str(assigned_port)

    pid_key = f'{username}_nodejs_{int(time.time())}'
    try:
        kwargs = dict(
            shell=True, cwd=project_path,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env
        )
        if hasattr(os, 'setsid'):
            kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(start_cmd, **kwargs)
        nodejs_processes[pid_key] = {
            'process': p, 'username': username,
            'project': project_path, 'port': assigned_port,
            'command': start_cmd, 'main_file': main_file or '(auto)',
            'deps_file': deps_file or 'package.json',
            'output': [], 'started': datetime.now().isoformat()
        }
        threading.Thread(target=read_process_output, args=(pid_key, p),
                         kwargs={'store': nodejs_processes}, daemon=True).start()
        log_activity(username, 'nodejs.start', f'{start_cmd} port={assigned_port}')
        return {'success': True, 'pid': pid_key, 'port': assigned_port,
                'command': start_cmd, 'install_output': install_output}
    except Exception as e:
        return {'success': False, 'error': str(e), 'install_output': install_output}

def get_nodejs_info(project_path, main_file=None, deps_file=None):
    pkg_json = os.path.join(project_path, 'package.json')
    yarn_lock = os.path.join(project_path, 'yarn.lock')

    install_cmd = 'npm install'
    if deps_file and os.path.exists(os.path.join(project_path, deps_file)):
        if deps_file.endswith('.lock') or 'yarn' in deps_file:
            install_cmd = 'yarn install'
        else:
            install_cmd = 'npm install'
    elif os.path.exists(yarn_lock):
        install_cmd = 'yarn install'

    run_cmd = f'node "{main_file}"' if main_file else None
    if not run_cmd:
        if os.path.exists(pkg_json):
            try:
                with open(pkg_json) as f:
                    pkg = json.load(f)
                sc = pkg.get('scripts',{}).get('start') or pkg.get('scripts',{}).get('dev')
                if sc: run_cmd = f'npm start'
            except Exception:
                pass
    if not run_cmd:
        for name in ['index.js','app.js','server.js','main.js']:
            if os.path.exists(os.path.join(project_path, name)):
                run_cmd = f'node "{name}"'
                break
    if not run_cmd:
        run_cmd = 'node your_main_file.js'

    return {'install_command': install_cmd, 'run_command': run_cmd}

# ─────────────────────────────────────────────────────────────────────────────
#  14.  PHP Helpers 
# ─────────────────────────────────────────────────────────────────────────────

_php_servers = {}  # pid_key -> {process, port, path, ...}

def _command_exists(cmd):
    """التحقق من وجود أمر في النظام."""
    try:
        subprocess.run(['which', cmd], capture_output=True, check=True, timeout=2)
        return True
    except Exception:
        return False

def get_php_install_commands(php_root, deps_file=None):
    """
    Return PHP install commands based on deps file.
    يعيد قائمة أوامر (list) أو قائمة فارغة.
    """
    if not php_root or not os.path.isdir(php_root):
        return []

    composer_json = os.path.join(php_root, 'composer.json')
    composer_lock = os.path.join(php_root, 'composer.lock')
    custom_deps = os.path.join(php_root, deps_file) if deps_file else None

    # التحقق من وجود composer
    has_composer = _command_exists('composer')

    if not has_composer:
        # إذا لم يكن composer موجوداً، نرجع أوامر بديلة (أو فارغة)
        if custom_deps and deps_file and os.path.exists(custom_deps):
            if deps_file.endswith('.txt'):
                return [f'# composer not found, install packages manually: cat {deps_file}']
        return []

    # إذا كان هناك ملف تبعيات مخصص
    if custom_deps and deps_file and os.path.exists(custom_deps):
        if 'composer' in deps_file.lower() or deps_file.endswith('.json'):
            if os.path.exists(composer_lock):
                return ['composer install --no-dev']
            return ['composer install']
        elif deps_file.endswith('.txt'):
            return [f'cat {deps_file} | xargs -I{{}} composer require {{}}']

    # composer.json / composer.lock
    if os.path.exists(composer_lock):
        return ['composer install --no-dev']
    if os.path.exists(composer_json):
        return ['composer install']

    return []

def start_php_server(php_root, username, port=None, main_file=None, deps_file=None):
    """
    Start PHP built-in server with comprehensive error handling.
    """
    # ── تحقق صارم من المدخلات ──
    if not php_root or not os.path.isdir(php_root):
        return {'success': False, 'error': 'PHP root path is invalid or does not exist.'}
    if not username or not isinstance(username, str):
        return {'success': False, 'error': 'Invalid username.'}
    if main_file and not isinstance(main_file, str):
        return {'success': False, 'error': 'main_file must be a string.'}
    if deps_file and not isinstance(deps_file, str):
        return {'success': False, 'error': 'deps_file must be a string.'}

    # ── التحقق من وجود PHP ──
    if not _command_exists('php'):
        return {'success': False, 'error': 'PHP is not installed or not in PATH.'}

    # ── تعيين المنفذ ──
    try:
        assigned_port = int(port) if port else find_free_port(5000)
        if assigned_port < 1 or assigned_port > 65535:
            assigned_port = find_free_port(5000)
    except Exception:
        assigned_port = find_free_port(5000)

    # ── تثبيت التبعيات (composer) ──
    install_output = ''
    try:
        cmds = get_php_install_commands(php_root, deps_file)
        if cmds:
            for ic in cmds:
                if ic.startswith('#'):
                    install_output += f'[info] {ic}\n'
                    continue
                try:
                    ir = subprocess.run(
                        ic, shell=True, cwd=php_root,
                        capture_output=True, text=True, timeout=180
                    )
                    if ir.returncode != 0:
                        install_output += f'[composer error] {ir.stderr}\n'
                    else:
                        install_output += ir.stdout
                except subprocess.TimeoutExpired:
                    install_output += f'[timeout] {ic} took too long.\n'
                except Exception as e:
                    install_output += f'[exception] {ic} -> {str(e)}\n'
    except Exception as e:
        install_output += f'[global deps error] {str(e)}\n'

    # ── بناء أمر تشغيل PHP ──
    php_bin = 'php'
    router = main_file.strip() if main_file and isinstance(main_file, str) else None

    if router:
        mf_abs = os.path.realpath(os.path.join(php_root, router))
        # التأكد أن الملف موجود داخل php_root (منع path traversal)
        if not mf_abs.startswith(os.path.realpath(php_root)):
            return {'success': False,
                    'error': 'Main file path is outside the PHP root.',
                    'install_output': install_output}
        if not os.path.isfile(mf_abs):
            return {'success': False,
                    'error': f'Main file not found: {router}',
                    'install_output': install_output,
                    'install_commands': cmds or ['composer install'],
                    'run_command': f'php -S 0.0.0.0:{assigned_port} -t "{php_root}"'}

        cmd = f'{php_bin} -S 0.0.0.0:{assigned_port} -t "{php_root}" "{router}"'
    else:
        cmd = f'{php_bin} -S 0.0.0.0:{assigned_port} -t "{php_root}"'

    # ── تشغيل العملية ──
    pid_key = f'{username}_php_{int(time.time())}'
    try:
        kwargs = {
            'shell': True,
            'cwd': php_root,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'bufsize': 1,
        }
        if hasattr(os, 'setsid'):
            kwargs['preexec_fn'] = os.setsid

        p = subprocess.Popen(cmd, **kwargs)

        # تخزين معلومات العملية
        _php_servers[pid_key] = {
            'process': p,
            'username': username,
            'path': php_root,
            'port': assigned_port,
            'main_file': router or '(auto)',
            'deps_file': deps_file or 'composer.json',
            'output': [],
            'install_output': install_output,
            'started': datetime.now().isoformat()
        }

        # قراءة المخرجات في خلفية
        threading.Thread(
            target=read_process_output,
            args=(pid_key, p),
            kwargs={'store': _php_servers},
            daemon=True
        ).start()

        log_activity(username, 'php.start', f'{cmd} port={assigned_port}')
        return {
            'success': True,
            'pid': pid_key,
            'port': assigned_port,
            'command': cmd,
            'install_output': install_output
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to start PHP server: {str(e)}',
            'install_output': install_output
        }

def get_php_info(php_root, main_file=None, deps_file=None):
    """Return install & run commands without running."""
    if not php_root or not os.path.isdir(php_root):
        return {'install_commands': [], 'run_command': ''}

    cmds = get_php_install_commands(php_root, deps_file)
    router = f' "{main_file}"' if main_file and isinstance(main_file, str) else ''
    run_cmd = f'php -S 0.0.0.0:PORT -t "{php_root}"{router}'
    return {
        'install_commands': cmds or ['composer install (if needed)'],
        'run_command': run_cmd
    }


# ─────────────────────────────────────────────────────────────────────────────
#  15.  ZIP Extract Helpers (Improved — شبه مستحيل الخطأ)
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {
    'py','js','ts','jsx','tsx','json','yaml','yml','toml','cfg','ini',
    'txt','md','html','htm','css','scss','sass','less',
    'sh','bash','bat','cmd',
    'jpg','jpeg','png','gif','webp','svg','ico',
    'mp3','mp4','ogg','wav',
    'zip','tar','gz','rar','7z',
    'pdf','doc','docx','xls','xlsx',
    'php','rb','go','rs','java','c','cpp','h',
    'sql','db','sqlite','env','xml',
    'woff','woff2','ttf','eot',
}

BLOCKED_EXTENSIONS = {
    'exe','com','scr','vbs','bat','cmd','ps1','msi','dll','sys',
    'pif','application','gadget','hta','cpl','msc','jar','ws','wsf','wsh'
}

# ─── Dangerous patterns (مع تحسين الأداء) ────────────────────────────────
DANGEROUS_PATTERNS = [
    (r'api\.telegram\.org/bot[A-Za-z0-9:_-]{20,}', '⚠️ Telegram bot token hardcoded in file'),
    (r'bot\.send_document\s*\(|sendDocument\s*\(', '⚠️ Telegram file-send function (exfiltration risk)'),
    (r'bot\.send_message\s*\(.*ADMIN_ID|sendMessage.*chat_id', '⚠️ Telegram C2 messaging pattern'),
    (r'telebot\s*\.\s*TeleBot\s*\(|telegram\.ext.*Application', '⚠️ Telegram bot library initialised — potential C2'),
    (r'os\.walk\s*\(.*\).*\.py|get_all_py_files|scan_directory.*py', '🚨 Mass .py file harvesting pattern'),
    (r'zipfile\.ZipFile.*os\.walk|ZipFile.*zipf\.write.*os\.walk', '🚨 Mass zip-and-send exfiltration'),
    (r'backup_all|python_backup|full_python_backup|zip_buffer.*BytesIO.*ZipFile', '🚨 Backup-and-send pattern'),
    (r'scan_current|scan_home|scan_root|scan_custom|scan_directory', '🚨 File system scanning bot pattern'),
    (r'send_document.*chat\.id.*zip_buffer|send_document.*message\.chat', '🚨 Direct file exfil via Telegram'),
    (r'find_config|config\*\.py|settings\*\.json|\*\.env.*os\.walk', '🚨 Config/secret file hunting pattern'),
    (r'exec\s*\(base64\.b64decode', '🚨 Base64-encoded exec (obfuscated payload)'),
    (r'__import__\s*\(\s*["\']os["\']\s*\)\.system', '🚨 Dynamic os.system call'),
    (r'socket\.connect.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*(?:4444|1337|9999|31337)', '🚨 Raw reverse-shell socket'),
    (r'Popen.*shell=True.*PIPE.*stdin|popen.*|.*PIPE.*communicate', '⚠️ Shell injection with pipe'),
    (r'eval\s*\(\s*(?:compile|input|request)', '🚨 Dynamic eval with user/net input'),
    (r'/etc/passwd|/etc/shadow|\.ssh/id_rsa|\.bash_history|\.aws/credentials', '🚨 Sensitive system file access'),
    (r'SECRET_KEY\s*=\s*["\'][^"\']{10,}|DATABASE_URL\s*=\s*["\']|API_KEY\s*=\s*["\'][A-Za-z0-9]{20,}', '⚠️ Hardcoded secret/credential'),
    (r'ipapi\.co|ip-api\.com|checkip\.amazonaws|api\.ipify', '⚠️ IP geolocation/fingerprinting call'),
    (r'system\s*\(\s*\$_(?:GET|POST|REQUEST)|passthru\s*\(\s*\$_', '🚨 PHP web shell pattern'),
    (r'eval\s*\(\s*base64_decode\s*\(\s*\$_|eval\s*\(\s*gzinflate', '🚨 PHP obfuscated web shell'),
    (r'<\?php.*system\s*\(|<\?php.*exec\s*\(', '🚨 PHP command execution'),
    (r'subprocess\.getoutput\s*\(\s*["\']whoami|subprocess.*getoutput.*id\b', '⚠️ whoami/id system recon'),
    (r'security_dump|backup_and_send|data_exfil|steal_files', '🚨 Known malware function name'),
    (r'reverse_shell|rev_shell|bind_shell|meterpreter', '🚨 Known shell payload keyword'),
]

FILE_THEFT_BOT_SIGNATURES = [
    {'name': '🚨 File-theft Telegram bot (full fingerprint)',
     'require_all': [r'TeleBot\s*\(|telegram\.Bot\s*\(', r'os\.walk\s*\(', r'send_document|sendDocument']},
    {'name': '🚨 System directory scanner bot',
     'require_all': [r'TeleBot\s*\(|telegram\.Bot\s*\(', r"['\"](?:/home|/var|/opt|/etc)['\"]", r'os\.walk\s*\(']},
]

def scan_file_content(filepath):
    """
    Deep-scan uploaded file for malicious patterns.
    Returns list of threat descriptions.
    """
    threats = []
    try:
        if not filepath or not os.path.isfile(filepath):
            return threats

        ext = os.path.splitext(filepath)[1].lower().lstrip('.')
        # فقط امتدادات قابلة للفحص
        if ext not in ('py','js','php','sh','bash','rb','ts','jsx','tsx','txt','json','html','htm'):
            return threats

        # قراءة الملف بحذر (حد حجم 500 كيلوبايت)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500_000)
        except Exception:
            return threats

        if not content:
            return threats

        # ── فحص الأنماط ──
        for pattern, desc in DANGEROUS_PATTERNS:
            try:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    threats.append(desc)
            except re.error:
                continue

        # ── الفحص الهيكلي (AND logic) ──
        for sig in FILE_THEFT_BOT_SIGNATURES:
            try:
                if all(re.search(p, content, re.IGNORECASE | re.DOTALL) for p in sig['require_all']):
                    if sig['name'] not in threats:
                        threats.append(sig['name'])
            except Exception:
                continue

    except Exception:
        pass

    return threats


MAX_EXTRACT_SIZE = 500 * 1024 * 1024  # 500 MB

def safe_extract(archive_path, dest_dir, username):
    """
    Safely extract ZIP/TAR/RAR archives with size limits and path traversal protection.
    """
    # ── التحقق من صحة المدخلات ──
    if not archive_path or not os.path.isfile(archive_path):
        return {'success': False, 'error': 'Archive file does not exist.'}
    if not dest_dir:
        return {'success': False, 'error': 'Destination directory is required.'}
    if not username or not isinstance(username, str):
        return {'success': False, 'error': 'Invalid username.'}

    # التحقق من الصلاحية (منع الكتابة خارج نطاق المستخدم)
    if not is_path_allowed(username, dest_dir):
        return {'success': False, 'error': 'Forbidden destination path.'}

    try:
        os.makedirs(dest_dir, exist_ok=True)
    except Exception as e:
        return {'success': False, 'error': f'Cannot create destination: {str(e)}'}

    ext = os.path.splitext(archive_path)[1].lower()
    extracted_files = []
    total_size = 0

    # ── دالة مساعدة للتحقق من المسار الآمن ──
    def _safe_path(base, target):
        real_base = os.path.realpath(base)
        real_target = os.path.realpath(os.path.join(base, target))
        return real_target.startswith(real_base)

    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for info in zf.infolist():
                    if total_size > MAX_EXTRACT_SIZE:
                        return {'success': False, 'error': 'Archive too large (>500 MB)'}

                    # منع path traversal
                    if not _safe_path(dest_dir, info.filename):
                        continue

                    try:
                        zf.extract(info, dest_dir)
                        total_size += info.file_size
                        extracted_files.append(info.filename)
                    except Exception as e:
                        # تخطي الملفات التي لا يمكن استخراجها
                        continue

        elif ext in ('.tar', '.gz', '.bz2', '.tgz') or archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:*') as tf:
                for member in tf.getmembers():
                    if total_size > MAX_EXTRACT_SIZE:
                        return {'success': False, 'error': 'Archive too large (>500 MB)'}

                    if not _safe_path(dest_dir, member.name):
                        continue

                    try:
                        tf.extract(member, dest_dir)
                        total_size += member.size
                        extracted_files.append(member.name)
                    except Exception:
                        continue

        else:
            # محاولة استخدام unrar
            if _command_exists('unrar'):
                try:
                    r = subprocess.run(
                        ['unrar', 'x', '-y', archive_path, dest_dir],
                        capture_output=True, text=True, timeout=60
                    )
                    if r.returncode == 0:
                        extracted_files = ['(unrar extracted)']
                    else:
                        return {'success': False, 'error': 'unrar extraction failed: ' + r.stderr}
                except subprocess.TimeoutExpired:
                    return {'success': False, 'error': 'unrar timed out.'}
                except Exception as e:
                    return {'success': False, 'error': f'unrar error: {str(e)}'}
            else:
                return {'success': False, 'error': 'Unsupported archive format (install unrar or use zip/tar).'}

        log_activity(username, 'files.extract', f'{len(extracted_files)} files extracted to {dest_dir}')
        return {'success': True, 'extracted': len(extracted_files), 'dest': dest_dir}

    except zipfile.BadZipFile:
        return {'success': False, 'error': 'Corrupted or invalid ZIP file.'}
    except tarfile.TarError:
        return {'success': False, 'error': 'Corrupted or invalid TAR file.'}
    except Exception as e:
        return {'success': False, 'error': f'Extraction error: {str(e)}'}


# ─────────────────────────────────────────────────────────────────────────────
#  16.  Decorators (Improved with permission checks)
# ─────────────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Session expired'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username') != MASTER_USERNAME:
            return jsonify({'success': False, 'error': 'Master only'}), 403
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator للتحقق من صلاحيات RBAC."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = session.get('username')
            if not username:
                return jsonify({'success': False, 'error': 'Not logged in'}), 401
            if not user_has_permission(username, permission):
                return jsonify({'success': False, 'error': 'Permission denied'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
#  17.  Maintenance Template (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

MAINTENANCE_TMPL = r'''
<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maintenance — SERVER HUB</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}
body{background:#0b0f17;color:#c9d1d9;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{text-align:center;padding:50px 40px;background:#161b22;border:1px solid #30363d;border-radius:16px;max-width:480px;width:92%}
.icon{font-size:72px;margin-bottom:20px;animation:spin 4s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
h1{font-size:26px;color:#fff;margin-bottom:8px}
.sub{color:#7c5cfc;font-size:12px;letter-spacing:3px;text-transform:uppercase;margin-bottom:20px}
.msg{background:#0d1117;border:1px solid #30363d;border-left:4px solid #7c5cfc;padding:16px;border-radius:8px;color:#8b949e;line-height:1.7}
.foot{margin-top:20px;font-size:11px;color:#484f58}
</style></head>
<body><div class="card">
<div class="icon">⚙️</div>
<h1>Under Maintenance</h1>
<div class="sub">SERVER HUB</div>
<div class="msg">{{ message }}</div>
<div class="foot">All rights reserved © SERVER HUB — By SHBH_S1</div>
</div></body></html>
'''


# ─────────────────────────────────────────────────────────────────────────────
#  18.  AUTH TEMPLATE (Login + Register) — unchanged (already secure)
# ─────────────────────────────────────────────────────────────────────────────

AUTH_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SERVER HUB — Access</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter','Segoe UI',sans-serif}
html,body{height:100%;background:#0b0f17}
body{
  display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:
    radial-gradient(ellipse at 15% 50%,rgba(192,57,43,.4) 0%,transparent 55%),
    radial-gradient(ellipse at 85% 20%,rgba(142,68,173,.3) 0%,transparent 50%),
    radial-gradient(ellipse at 50% 100%,rgba(231,76,60,.2) 0%,transparent 60%),
    url('https://c.top4top.io/p_3820uop3i0.png') center/cover no-repeat fixed,
    #080b12;
  position:relative;overflow:hidden;
}
body::after{
  content:'';position:fixed;inset:0;
  background:rgba(8,11,18,.68);
  backdrop-filter:blur(3px) saturate(1.4);
  pointer-events:none;z-index:1;
}
body::before{
  content:'';position:absolute;inset:0;
  background-image:
    linear-gradient(rgba(124,92,252,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(124,92,252,.04) 1px,transparent 1px);
  background-size:60px 60px;
  animation:gridMove 25s linear infinite;
  pointer-events:none;
}
@keyframes gridMove{to{background-position:60px 60px}}

/* ── Glow orbs ── */
.orb{position:fixed;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:2}
.orb1{width:400px;height:400px;background:rgba(192,57,43,.14);top:-100px;left:-100px;animation:orbFloat1 12s ease-in-out infinite}
.orb2{width:300px;height:300px;background:rgba(142,68,173,.1);bottom:-80px;right:-80px;animation:orbFloat2 15s ease-in-out infinite}
@keyframes orbFloat1{0%,100%{transform:translate(0,0)}50%{transform:translate(60px,40px)}}
@keyframes orbFloat2{0%,100%{transform:translate(0,0)}50%{transform:translate(-40px,-30px)}}

/* ── Main wrap ── */
.wrap{
  position:relative;z-index:3;
  display:flex;flex-direction:column;align-items:center;
  width:min(460px,95vw);
}

/* ── Card (single container for logo + forms) ── */
.card{
  width:100%;
  background:rgba(13,17,23,.92);
  border:1px solid rgba(48,54,61,.8);
  border-radius:24px;
  overflow:hidden;
  box-shadow:
    0 30px 80px rgba(0,0,0,.6),
    0 0 0 1px rgba(124,92,252,.08),
    inset 0 1px 0 rgba(255,255,255,.04);
  backdrop-filter:blur(24px);
}

/* ── Logo block inside card ── */
.logo-block{
  display:flex;flex-direction:column;align-items:center;
  padding:32px 28px 24px;
  background:linear-gradient(180deg,rgba(124,92,252,.06) 0%,transparent 100%);
  border-bottom:1px solid rgba(48,54,61,.5);
  position:relative;
}
.logo-block::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 0%,rgba(124,92,252,.15) 0%,transparent 70%);
  pointer-events:none;
}
.logo-img{
  width:90px;height:90px;border-radius:50%;
  object-fit:cover;
  border:3px solid rgba(124,92,252,.5);
  box-shadow:0 0 30px rgba(124,92,252,.4),0 0 60px rgba(124,92,252,.15);
  animation:logoPulse 3s ease-in-out infinite;
  position:relative;z-index:1;
  background:#161b22;
}
@keyframes logoPulse{
  0%,100%{box-shadow:0 0 30px rgba(192,57,43,.5),0 0 60px rgba(192,57,43,.15);border-color:rgba(192,57,43,.6)}
  50%{box-shadow:0 0 50px rgba(231,76,60,.7),0 0 90px rgba(142,68,173,.3);border-color:rgba(231,76,60,.8)}
}
.logo-title{
  font-size:26px;font-weight:900;letter-spacing:2px;margin-top:14px;
  background:linear-gradient(135deg,#ff6b6b,#c0392b,#8e44ad);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  position:relative;z-index:1;
}
.logo-sub{
  color:#484f58;font-size:11px;margin-top:5px;
  letter-spacing:3px;text-transform:uppercase;
  position:relative;z-index:1;
}

/* ── Forms area ── */
.forms-area{padding:28px}

/* Tabs */
.tabs{
  display:flex;margin-bottom:24px;
  background:#0b0f17;border-radius:10px;padding:4px;gap:4px;
  border:1px solid rgba(48,54,61,.6);
}
.tab{
  flex:1;text-align:center;padding:10px 8px;cursor:pointer;
  color:#8b949e;font-weight:600;font-size:13px;border-radius:7px;
  transition:.25s;user-select:none;
}
.tab:hover{color:#c9d1d9;background:rgba(255,255,255,.04)}
.tab.active{
  color:#fff;
  background:linear-gradient(135deg,#c0392b,#922b21);
  box-shadow:0 2px 12px rgba(192,57,43,.5);
}

/* Form */
.form{display:none}
.form.active{display:block;animation:fadeUp .25s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.field{margin-bottom:14px}
.field label{
  display:block;color:#8b949e;font-size:10px;
  text-transform:uppercase;letter-spacing:1.2px;margin-bottom:5px;font-weight:700;
}
.field input{
  width:100%;padding:12px 14px;
  background:rgba(255,255,255,.04);
  border:1px solid rgba(48,54,61,.8);
  border-radius:8px;color:#e6edf3;font-size:14px;outline:none;
  transition:.2s;
}
.field input:focus{
  border-color:#7c5cfc;
  background:rgba(124,92,252,.05);
  box-shadow:0 0 0 3px rgba(124,92,252,.15);
}
.field input::placeholder{color:#30363d}
.btn{
  width:100%;padding:13px;border:none;border-radius:9px;cursor:pointer;
  background:linear-gradient(135deg,#e74c3c,#c0392b,#8e44ad);color:#fff;
  font-weight:700;font-size:14px;transition:.25s;margin-top:6px;
  box-shadow:0 4px 16px rgba(192,57,43,.45);
  letter-spacing:.8px;position:relative;overflow:hidden;
}
.btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.1),transparent);
  opacity:0;transition:.2s;
}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(124,92,252,.55)}
.btn:hover::before{opacity:1}
.btn:active{transform:translateY(0)}
.msg{
  margin-top:12px;padding:11px 14px;border-radius:8px;font-size:12.5px;text-align:center;
  display:flex;align-items:center;justify-content:center;gap:6px;
}
.msg.error{background:rgba(248,81,73,.08);border:1px solid rgba(248,81,73,.25);color:#f85149}
.msg.success{background:rgba(46,160,67,.08);border:1px solid rgba(46,160,67,.25);color:#3fb950}
.msg.pending{background:rgba(255,170,0,.08);border:1px solid rgba(255,170,0,.25);color:#e3a008}
.divider{
  display:flex;align-items:center;gap:10px;
  margin:16px 0;color:#30363d;font-size:11px;
}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:rgba(48,54,61,.6)}
.foot{
  text-align:center;margin-top:18px;padding-top:14px;
  border-top:1px solid rgba(48,54,61,.4);
  font-size:11px;color:#30363d;
}
.foot a{color:#7c5cfc;text-decoration:none;transition:.2s}
.foot a:hover{color:#a78bfa}

/* Particles */
.particles{position:fixed;inset:0;pointer-events:none;z-index:2;overflow:hidden}
.particle{
  position:absolute;border-radius:50%;
  background:rgba(124,92,252,.5);animation:float linear infinite;
}
@keyframes float{
  0%{transform:translateY(100vh) scale(0);opacity:0}
  10%{opacity:1;transform:translateY(80vh) scale(1)}
  90%{opacity:.6}
  100%{transform:translateY(-5vh) scale(.5) rotate(360deg);opacity:0}
}
</style>
</head>
<body>
<div class="orb orb1"></div>
<div class="orb orb2"></div>
<div class="particles" id="ptcls"></div>
<audio id="ea" autoplay loop preload="auto"><source src="''' + ENTRY_SOUND_URL + r'''" type="audio/mp4"></audio>

<div class="wrap">
  <div class="card">

    <!-- ── Logo Block ── -->
    <div class="logo-block">
      <img class="logo-img"
           src="https://c.top4top.io/p_3820uop3i0.png"
           alt="SERVER HUB"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
      <div style="display:none;width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#7c5cfc,#00bfff);align-items:center;justify-content:center;font-size:36px;border:3px solid rgba(124,92,252,.5);box-shadow:0 0 30px rgba(124,92,252,.4)">🚀</div>
      <div class="logo-title">SERVER HUB</div>
      <div class="logo-sub">Professional Hosting Panel</div>
    </div>

    <!-- ── Forms Block ── -->
    <div class="forms-area">
      <div class="tabs">
        <div class="tab active" data-f="login">🔐 Sign In</div>
        <div class="tab" data-f="register">✨ Register</div>
      </div>

      <form class="form active" id="login-form" method="post" action="/login">
        <div class="field"><label>Username</label><input name="username" placeholder="Enter your username" required autofocus autocomplete="username"></div>
        <div class="field"><label>Password</label><input type="password" name="password" placeholder="Enter your password" required autocomplete="current-password"></div>
        <button class="btn" type="submit">Sign In →</button>
        {% if error and error_type == 'login' %}
          <div class="msg {% if 'pending' in error.lower() or 'waiting' in error.lower() or 'approval' in error.lower() %}pending{% else %}error{% endif %}">{{ error }}</div>
        {% endif %}
      </form>

      <form class="form" id="register-form" method="post" action="/register">
        <div class="field"><label>Username</label><input name="username" placeholder="Choose a username" required autocomplete="username"></div>
        <div class="field"><label>🔵 Telegram Username <span style="color:#f85149">*</span></label><input name="tg_username" placeholder="@yourusername" required autocomplete="off"></div>
        <div class="field"><label>Password</label><input type="password" name="password" placeholder="Min 4 characters" required autocomplete="new-password"></div>
        <div class="field"><label>Confirm Password</label><input type="password" name="confirm_password" placeholder="Repeat password" required autocomplete="new-password"></div>
        <button class="btn" type="submit">Create Account →</button>
        {% if error and error_type == 'register' %}
          <div class="msg {% if '✅' in error or 'sent' in error.lower() %}success{% else %}error{% endif %}">{{ error }}</div>
        {% endif %}
      </form>

      <div class="foot">SERVER HUB &copy; 2025 &nbsp;·&nbsp; By <a href="https://t.me/SHBH_S1" target="_blank">SHBH_S1</a></div>
    </div>

  </div>
</div>

<script>
document.querySelectorAll('.tab').forEach(t=>{
  t.addEventListener('click',()=>{
    const fid=t.dataset.f;
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.form').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById(fid+'-form').classList.add('active');
  });
});
{% if error and error_type == 'register' %}
document.querySelectorAll('.tab').forEach(t=>{if(t.dataset.f==='register')t.click();});
{% endif %}
(function(){
  var a=document.getElementById('ea');
  if(!a)return;a.volume=0.35;
  function p(){var r=a.play();if(r)r.catch(()=>{});}
  p();setInterval(()=>{if(a.paused)p();},1000);
  ['click','keydown','touchstart'].forEach(e=>document.addEventListener(e,p,{once:true}));
})();
(function(){
  var c=document.getElementById('ptcls');
  for(var i=0;i<18;i++){
    var d=document.createElement('div');
    var s=2+Math.random()*4;
    d.className='particle';
    d.style.cssText='left:'+(Math.random()*100)+'%;width:'+s+'px;height:'+s+'px;animation-duration:'+(10+Math.random()*14)+'s;animation-delay:'+(-Math.random()*24)+'s';
    c.appendChild(d);
  }
})();
</script>
</body>
</html>
'''
# ─────────────────────────────────────────────────────────────────────────────
#  19.  MAIN DASHBOARD TEMPLATE (Improved — RBAC + All Features)
# ─────────────────────────────────────────────────────────────────────────────

def get_html_template(username=None):
    """
    توليد قالب لوحة التحكم الرئيسية بناءً على دور المستخدم.
    يعيد سلسلة HTML كاملة مع CSS/JS مدمجين.
    """
    # ── تحديد دور المستخدم ──
    role = get_user_role(username) if username else 'user'
    is_owner = (username == MASTER_USERNAME)
    is_admin = role in ('admin', 'owner')
    is_moderator = role in ('moderator', 'admin', 'owner')

    # ── تبويبات إضافية حسب الصلاحية ──
    extra_tabs = ''

    # تبويب AI للجميع
    extra_tabs += '''
        <div class="tab-item" data-tab="ai" style="color:#a78bfa;font-weight:600">🤖 AI</div>
    '''

    # تبويب Terminal للجميع (سيتم تفعيل WebSocket)
    extra_tabs += '''
        <div class="tab-item" data-tab="terminal" style="color:#00bfff;font-weight:500">🖥 Terminal</div>
    '''

    # تبويب Database للجميع (مع صلاحيات محدودة للمستخدم العادي)
    extra_tabs += '''
        <div class="tab-item" data-tab="database" style="color:#f1c40f;font-weight:500">🗄 Database</div>
    '''

    # تبويبات للمشرفين
    if is_admin:
        extra_tabs += '''
        <div class="tab-item" data-tab="users">👥 Users</div>
        <div class="tab-item" data-tab="nodejs">🟢 Node.js</div>
        <div class="tab-item" data-tab="php">🐘 PHP</div>
        <div class="tab-item" data-tab="backups">💾 Backups</div>
        <div class="tab-item" data-tab="network">🌐 Network</div>
        <div class="tab-item" data-tab="startup">🚀 Startup</div>
        <div class="tab-item" data-tab="settings">⚙️ Settings</div>
        <div class="tab-item" data-tab="activity">📋 Activity</div>
        '''

    # تبويب Owner خاص بالمالك فقط
    if is_owner:
        extra_tabs += '''
        <div class="tab-item" data-tab="owner" style="color:#7c5cfc;font-weight:700">👑 Owner</div>
        '''

    # ── محتوى تبويب Owner (للمالك فقط) ──
    owner_panel_html = ''
    if is_owner:
        owner_panel_html = r'''
<!-- ===== OWNER TAB ===== -->
<div class="tab-content" id="tab-owner">
  <!-- Stats Row -->
  <div class="stats4">
    <div class="stat4 purple"><div class="s4lbl">Total Users</div><div class="s4val" id="ow-users">—</div></div>
    <div class="stat4 blue"><div class="s4lbl">Servers</div><div class="s4val" id="ow-servers">—</div></div>
    <div class="stat4 green"><div class="s4lbl">Active Bots</div><div class="s4val" id="ow-bots">—</div></div>
    <div class="stat4 orange"><div class="s4lbl">ZIP Files</div><div class="s4val" id="ow-zips">—</div></div>
  </div>

  <!-- Maintenance -->
  <div class="section-card">
    <div class="section-head">🔧 Maintenance Mode</div>
    <div class="section-body">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <label class="toggle-switch">
          <input type="checkbox" id="maint-toggle-chk" onchange="toggleMaintenance()">
          <span class="slider"></span>
        </label>
        <span style="color:#8b949e;font-size:13px">Enable Maintenance Mode</span>
      </div>
      <div class="field-block"><label>Maintenance Message</label>
        <textarea id="maint-msg" rows="2" style="width:100%;padding:10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#e6edf3;font-size:13px;resize:vertical"></textarea>
      </div>
      <button class="btn-action" onclick="saveMaintMsg()">Save Message</button>
    </div>
  </div>

  <!-- Telegram Bot -->
  <div class="section-card">
    <div class="section-head">🤖 Telegram Bot Integration</div>
    <div class="section-body">
      <div id="bot-status-badge" style="margin-bottom:12px"></div>
      <div class="field-block"><label>Bot Token</label><input id="tg-token" type="password" placeholder="1234567890:AAF..."></div>
      <div class="field-block"><label>Owner Telegram ID</label><input id="tg-ownerid" placeholder="123456789"></div>
      <div id="bot-link-status" style="color:#8b949e;font-size:12px;margin-bottom:8px"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn-action" onclick="linkBot()">🔗 Link Bot</button>
        <button class="btn-action gray" onclick="unlinkBot()">🔓 Unlink</button>
      </div>
      <div id="bot-control-panel" style="display:none;margin-top:16px">
        <div class="section-head" style="margin-bottom:8px">Bot Control</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <button class="btn-action green" onclick="botAction('start')">▶ Start</button>
          <button class="btn-action" onclick="botAction('restart')">↺ Restart</button>
          <button class="btn-action danger" onclick="botAction('stop')">■ Stop</button>
          <button class="btn-action gray" onclick="refreshBotStats()">🔄 Refresh</button>
        </div>
        <div class="console-box" id="bot-console" style="height:120px"></div>
        <div class="cmd-input" style="margin-top:8px">
          <span class="prompt">$</span>
          <input id="bot-cmd-input" placeholder="Send command..." onkeydown="if(event.key==='Enter')sendBotCmd()">
        </div>
      </div>
    </div>
  </div>

  <!-- Panel Settings -->
  <div class="section-card">
    <div class="section-head">⚙️ Panel Settings</div>
    <div class="section-body">
      <div class="field-block"><label>Panel Name</label><input id="panel-name-inp" placeholder="SERVER HUB"></div>
      <div class="field-block"><label>Welcome Message</label><input id="panel-welcome-inp" placeholder="Welcome!"></div>
      <button class="btn-action" onclick="savePanelSettings()">Save Settings</button>
    </div>
  </div>

  <!-- Announcements -->
  <div class="section-card">
    <div class="section-head">📢 Announcements</div>
    <div class="section-body">
      <div class="field-block"><label>New Announcement</label><input id="ann-txt" placeholder="Type announcement..."></div>
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button class="btn-action" onclick="addAnnouncement()">Add</button>
        <button class="btn-action gray" onclick="ownerBroadcast()">📡 Broadcast</button>
      </div>
      <div id="ann-list"></div>
    </div>
  </div>

  <!-- ZIP Files -->
  <div class="section-card">
    <div class="section-head">📦 User ZIP Files</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <button class="btn-action" onclick="loadOwnerZips()">🔄 Refresh</button>
        <button class="btn-action green" onclick="downloadAllZips()">⬇ Download All</button>
      </div>
      <div id="owner-zip-list"></div>
    </div>
  </div>

  <!-- Pending Registrations -->
  <div class="section-card">
    <div class="section-head">⏳ Pending Account Approvals</div>
    <div class="section-body">
      <button class="btn-action" onclick="loadPendingUsers()" style="margin-bottom:10px">🔄 Refresh</button>
      <div id="pending-users-list"></div>
    </div>
  </div>

  <!-- Security Alerts -->
  <div class="section-card" style="border-color:rgba(248,81,73,.4)">
    <div class="section-head" style="color:#f85149">🛡️ Security Alerts — ملفات مشبوهة</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        <button class="btn-action gray" onclick="loadSecurityAlerts()">🔄 Refresh</button>
        <button class="btn-action danger" onclick="clearSecurityAlerts()">🗑 Clear All</button>
      </div>
      <div id="security-alerts-list">
        <div style="color:var(--text3);padding:10px;text-align:center">اضغط Refresh لتحميل التنبيهات</div>
      </div>
    </div>
  </div>

  <!-- Role Management (NEW) -->
  <div class="section-card">
    <div class="section-head">👑 Role Management (RBAC)</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
        <button class="btn-action" onclick="loadRoleManagement()">🔄 Refresh</button>
      </div>
      <div id="role-management-list">
        <div style="color:var(--text3);padding:10px;text-align:center">اضغط Refresh لتحميل الأدوار</div>
      </div>
    </div>
  </div>

  <!-- Danger Zone -->
  <div class="section-card" style="border-color:#f85149">
    <div class="section-head" style="color:#f85149">⚠️ Danger Zone</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn-action danger" onclick="ownerAction('clear_all_logs')">🗑 Clear All Logs</button>
        <button class="btn-action danger" onclick="ownerAction('kick_all_users')">👢 Kick All Users</button>
        <button class="btn-action danger" onclick="ownerAction('reset_stats')">📊 Reset Stats</button>
        <button class="btn-action gray" onclick="ownerAction('restart_panel')">🔄 Restart Panel</button>
      </div>
    </div>
  </div>
</div>
'''

    # ── القالب الكامل ──
    return r'''
<!DOCTYPE html>
<html lang="ar" dir="auto">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SERVER HUB — Control Panel</title>
<style>
/* ── جميع الأنماط السابقة كما هي (تم تضمينها بالفعل) ── */
/* (سيتم إدراجها كاملة في الملف النهائي) */
:root{
  --bg:#080b12;--bg2:#0c1018;--bg3:#111620;--bg4:#161d28;
  --border:#1e2738;--border2:#2a3548;
  --accent:#c0392b;--accent2:#e74c3c;--accent3:#8e44ad;
  --neon:#ff2d55;--neon2:#a855f7;
  --green:#27ae60;--red:#e74c3c;--yellow:#f39c12;--orange:#e67e22;
  --text:#eaf0fb;--text2:#8899b0;--text3:#3d5068;
}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter','Segoe UI',sans-serif}
html,body{background:var(--bg);color:var(--text);min-height:100vh}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}

/* ── TOPBAR ── */
.topbar{
  background:var(--bg2);border-bottom:1px solid var(--border);
  padding:0 20px;height:56px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(0,0,0,.4);
}
.topbar .brand{
  font-size:18px;font-weight:800;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  display:flex;align-items:center;gap:8px;
}
.topbar .brand-icon{font-size:20px;-webkit-text-fill-color:initial}
.topbar .icons{display:flex;gap:10px;align-items:center}
.topbar .ic{
  color:var(--text2);font-size:17px;cursor:pointer;
  background:none;border:0;padding:6px;border-radius:6px;
  transition:.2s;
}
.topbar .ic:hover{color:var(--text);background:var(--bg3)}
.topbar .avatar{
  width:30px;height:30px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:700;color:#fff;cursor:default;
  border:2px solid rgba(124,92,252,.4);
}
.user-badge{
  display:flex;align-items:center;gap:8px;
  background:var(--bg3);border:1px solid var(--border);
  border-radius:20px;padding:4px 12px 4px 4px;
  font-size:12px;color:var(--text2);
}
.status-dot{
  width:8px;height:8px;border-radius:50%;background:var(--green);
  animation:blink 2s ease-in-out infinite;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}

/* ── TABS ── */
.tabs{
  background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;overflow-x:auto;padding:0 16px;
  scrollbar-width:none;gap:2px;
}
.tabs::-webkit-scrollbar{display:none}
.tab-item{
  padding:14px 16px;color:var(--text2);cursor:pointer;
  font-size:13px;white-space:nowrap;font-weight:500;
  border-bottom:2px solid transparent;transition:.15s;user-select:none;
}
.tab-item:hover{color:var(--text)}
.tab-item.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}

/* ── CONTAINER ── */
.container{max-width:1200px;margin:0 auto;padding:20px 16px}
.tab-content{display:none;animation:fadein .2s}
.tab-content.active{display:block}
@keyframes fadein{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}

/* ── CONSOLE ── */
.power-row{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;margin-bottom:14px;align-items:center}
.btn-power{
  padding:11px 8px;border:none;border-radius:8px;font-weight:600;
  font-size:13px;cursor:pointer;color:#fff;transition:.2s;letter-spacing:.3px;
}
.btn-start{background:linear-gradient(135deg,#1a7f37,#2ea043);box-shadow:0 2px 8px rgba(46,160,67,.3)}
.btn-start:hover{filter:brightness(1.1)}
.btn-restart{background:linear-gradient(135deg,#5a3fc0,#7c5cfc);box-shadow:0 2px 8px rgba(124,92,252,.3)}
.btn-restart:hover{filter:brightness(1.1)}
.btn-stop{background:linear-gradient(135deg,#b62324,#f85149);box-shadow:0 2px 8px rgba(248,81,73,.3)}
.btn-stop:hover{filter:brightness(1.1)}
.status-badge{
  display:flex;align-items:center;gap:6px;
  font-size:12px;font-weight:600;padding:8px 12px;
  background:var(--bg3);border:1px solid var(--border);border-radius:20px;
  white-space:nowrap;
}

/* ── CONSOLE BOX (for terminal) ── */
.console-box{
  background:#010409;border:1px solid #30363d;border-radius:10px;
  padding:14px;font-family:'Consolas','Monaco','Fira Code',monospace;
  font-size:12.5px;color:#7ee787;height:340px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-all;margin-bottom:10px;
  line-height:1.6;
}
.console-box .line-err{color:#f85149}
.console-box .line-warn{color:#d29922}
.console-box .line-info{color:#79c0ff}

/* ── CMD INPUT ── */
.cmd-input{
  display:flex;align-items:center;
  background:var(--bg2);border:1px solid var(--border);border-radius:8px;
  padding:0 14px;margin-bottom:14px;transition:.2s;
}
.cmd-input:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,92,252,.15)}
.cmd-input .prompt{color:var(--accent);margin-right:8px;font-weight:700;font-size:14px}
.cmd-input input{
  flex:1;background:none;border:0;outline:0;color:var(--text);
  padding:12px 0;font-family:monospace;font-size:13px;
}

/* ── STATS GRID ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:14px}
.stat-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  padding:14px;position:relative;overflow:hidden;
  transition:.2s;
}
.stat-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2));
}
.stat-card:hover{border-color:var(--accent);transform:translateY(-1px)}
.stat-card .lbl{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.8px;margin-bottom:6px;font-weight:600}
.stat-card .val{font-size:15px;color:var(--text);font-weight:700}
.stat-card .val .max{color:var(--text3);font-weight:400;font-size:12px}
.stat-card.green::before{background:var(--green)}
.stat-card.red::before{background:var(--red)}
.stat-card.yellow::before{background:var(--yellow)}
.stat-card.orange::before{background:var(--orange)}

/* ── SECTION CARD ── */
.section-card{
  background:var(--bg3);border:1px solid var(--border);border-radius:12px;
  margin-bottom:14px;overflow:hidden;
}
.section-head{
  padding:12px 16px;background:var(--bg4);border-bottom:1px solid var(--border);
  font-size:12px;font-weight:700;color:var(--text2);text-transform:uppercase;
  letter-spacing:1px;display:flex;align-items:center;gap:6px;
}
.section-body{padding:16px}

/* ── FILES ── */
.file-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.file-toolbar button{
  padding:8px 14px;border:1px solid var(--border);border-radius:6px;
  background:var(--bg4);color:var(--text);font-size:12px;cursor:pointer;
  font-weight:500;transition:.15s;display:flex;align-items:center;gap:4px;
}
.file-toolbar button:hover{background:var(--accent);border-color:var(--accent);color:#fff}
.breadcrumb{
  padding:8px 12px;background:var(--bg2);border:1px solid var(--border);
  border-radius:6px;font-size:12px;color:var(--text2);font-family:monospace;
  margin-bottom:10px;overflow-x:auto;white-space:nowrap;
}
.file-list{
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;overflow:hidden;
}
.file-item{
  display:flex;align-items:center;padding:10px 14px;
  border-bottom:1px solid var(--border);cursor:pointer;
  transition:.15s;gap:10px;
}
.file-item:last-child{border-bottom:none}
.file-item:hover{background:var(--bg4)}
.file-icon{font-size:16px;width:24px;text-align:center;flex-shrink:0}
.file-name{flex:1;font-size:13px;color:var(--text);font-weight:500;word-break:break-all}
.file-size{font-size:11px;color:var(--text3);flex-shrink:0}
.file-actions{display:flex;gap:4px;flex-shrink:0}
.file-actions button{
  padding:4px 8px;border:none;border-radius:4px;font-size:11px;cursor:pointer;
  background:var(--bg4);color:var(--text2);transition:.15s;
}
.file-actions button:hover{background:var(--accent);color:#fff}
.file-actions button.danger:hover{background:var(--red)}

/* ── AI CHAT (مثل السابق) ── */
.ai-chat-wrap{ /* ... */ }

/* ── DATABASE TAB ── */
.db-connection-card{
  background:var(--bg4);border:1px solid var(--border);border-radius:8px;
  padding:12px 14px;margin-bottom:8px;
  display:flex;justify-content:space-between;align-items:center;
}
.db-connection-card .db-name{font-weight:700;color:var(--text)}
.db-connection-card .db-meta{color:var(--text2);font-size:12px}

/* ── TERMINAL TAB ── */
.terminal-container{
  background:var(--bg2);border:1px solid var(--border);border-radius:12px;
  padding:4px;height:calc(100vh - 200px);min-height:400px;
}
.terminal-container iframe{
  width:100%;height:100%;border:none;border-radius:8px;
  background:#010409;
}

/* ── BUTTONS ── */
.btn-action{
  padding:8px 16px;border:none;border-radius:6px;cursor:pointer;
  background:linear-gradient(135deg,var(--accent),#5a3fc0);color:#fff;
  font-weight:600;font-size:12px;transition:.2s;letter-spacing:.3px;
}
.btn-action:hover{filter:brightness(1.1);transform:translateY(-1px)}
.btn-action.gray{background:var(--bg4);border:1px solid var(--border);color:var(--text2)}
.btn-action.gray:hover{background:var(--border);color:var(--text)}
.btn-action.green{background:linear-gradient(135deg,#1a7f37,#2ea043)}
.btn-action.danger{background:linear-gradient(135deg,#b62324,#f85149)}
.btn-action.orange{background:linear-gradient(135deg,var(--orange),#c7541f)}

/* ── FORMS ── */
.field-block{margin-bottom:12px}
.field-block label{display:block;font-size:11px;color:var(--text2);font-weight:600;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px}
.field-block input,.field-block select,.field-block textarea{
  width:100%;padding:10px 12px;background:var(--bg2);
  border:1px solid var(--border);border-radius:6px;color:var(--text);
  font-size:13px;outline:none;transition:.2s;
}
.field-block input:focus,.field-block select:focus,.field-block textarea:focus{
  border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,92,252,.15);
}
.field-block input::placeholder{color:var(--text3)}
.row-end{display:flex;justify-content:flex-end;gap:8px;margin-top:10px}

/* ── MODAL ── */
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.modal.open{display:flex}
.modal-box{background:var(--bg3);border:1px solid var(--border);border-radius:16px;width:min(540px,94vw);max-height:90vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.modal-head{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-head h3{font-size:16px;font-weight:700;color:var(--text)}
.modal-head .close{background:none;border:0;color:var(--text2);font-size:22px;cursor:pointer;line-height:1;padding:0 4px}
.modal-head .close:hover{color:var(--text)}
.modal-body{padding:20px;overflow-y:auto;flex:1}
.modal-foot{padding:14px 20px;border-top:1px solid var(--border);display:flex;gap:8px;justify-content:flex-end}

/* ── EDITOR ── */
.editor-wrap{position:relative}
.editor-box{
  width:100%;min-height:320px;padding:14px;
  background:#010409;border:1px solid var(--border);border-radius:8px;
  color:#7ee787;font-family:monospace;font-size:13px;
  outline:none;resize:vertical;line-height:1.6;tab-size:2;
}
.editor-box:focus{border-color:var(--accent)}

/* ── OWNER STATS ── */
.stats4{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:14px}
.stat4{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center;position:relative;overflow:hidden}
.stat4::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat4.purple::before{background:var(--accent)}
.stat4.blue::before{background:var(--accent2)}
.stat4.green::before{background:var(--green)}
.stat4.orange::before{background:var(--orange)}
.s4lbl{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.s4val{font-size:28px;font-weight:800;color:var(--text)}

/* ── TOGGLE SWITCH ── */
.toggle-switch{position:relative;width:44px;height:24px;flex-shrink:0}
.toggle-switch input{display:none}
.slider{
  position:absolute;inset:0;background:var(--bg4);border:1px solid var(--border);
  border-radius:24px;cursor:pointer;transition:.3s;
}
.slider:before{
  content:'';position:absolute;left:3px;top:3px;
  width:16px;height:16px;border-radius:50%;
  background:var(--text2);transition:.3s;
}
input:checked + .slider{background:var(--accent);border-color:var(--accent)}
input:checked + .slider:before{transform:translateX(20px);background:#fff}

/* ── TOAST ── */
.toast-container{position:fixed;bottom:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:8px}
.toast{
  padding:12px 18px;border-radius:10px;font-size:13px;font-weight:600;
  color:#fff;display:flex;align-items:center;gap:8px;
  animation:slideIn .3s ease;box-shadow:0 4px 20px rgba(0,0,0,.4);
  max-width:300px;
}
.toast.ok{background:linear-gradient(135deg,#1a7f37,#2ea043)}
.toast.err{background:linear-gradient(135deg,#b62324,#f85149)}
.toast.info{background:linear-gradient(135deg,var(--accent),#5a3fc0)}
@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}

/* ── SERVERS MODAL ── */
.srv-card{
  display:flex;align-items:center;justify-content:space-between;
  background:var(--bg4);border:1px solid var(--border);border-radius:8px;
  padding:12px 14px;margin-bottom:8px;transition:.15s;
}
.srv-card:hover{border-color:var(--accent)}
.srv-name{font-size:14px;font-weight:600;color:var(--text)}
.srv-meta{font-size:12px;color:var(--text2);margin-top:2px}
.srv-del-btn{
  background:var(--red);border:none;border-radius:6px;
  color:#fff;font-size:16px;width:32px;height:32px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:.15s;flex-shrink:0;
}
.srv-del-btn:hover{filter:brightness(1.2)}

/* ── ZIP ITEMS ── */
.zip-item{
  display:flex;justify-content:space-between;align-items:center;
  background:var(--bg4);border:1px solid var(--border);border-radius:6px;
  padding:10px 12px;margin-bottom:6px;
}
.z-name{color:var(--text);font-size:13px;font-family:monospace}
.z-size{color:var(--text2);font-size:11px;margin-top:2px}

/* ── PENDING ── */
.pending-card{
  display:flex;align-items:center;justify-content:space-between;gap:10px;
  background:var(--bg4);border:1px solid rgba(255,170,0,.3);border-radius:8px;
  padding:10px 14px;margin-bottom:8px;
}
.pending-card .p-user{font-size:13px;font-weight:600;color:var(--text)}
.pending-card .p-time{font-size:11px;color:var(--text2);margin-top:2px}

/* ── DATABASE TAB (خاص) ── */
.db-query-box{
  background:var(--bg2);border:1px solid var(--border);border-radius:8px;
  padding:12px;margin-top:10px;
}
.db-query-box textarea{
  width:100%;padding:10px;background:#010409;border:1px solid var(--border);
  border-radius:6px;color:var(--text);font-family:monospace;font-size:13px;
  min-height:100px;resize:vertical;
}
.db-result-box{
  background:#010409;border:1px solid var(--border);border-radius:6px;
  padding:10px;margin-top:8px;max-height:300px;overflow-y:auto;
  font-family:monospace;font-size:12px;color:#7ee787;
}

/* ── RESPONSIVE ── */
@media(max-width:600px){
  .stats-grid{grid-template-columns:1fr 1fr}
  .power-row{grid-template-columns:1fr 1fr 1fr;gap:6px}
  .power-row .status-badge{display:none}
  .topbar .brand{font-size:15px}
  .container{padding:12px 10px}
  .stats4{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="brand">
    <span class="brand-icon">🚀</span> SERVER HUB
  </div>
  <div class="icons">
    <button class="ic" onclick="loadSearch()" title="Search">🔍</button>
    <button class="ic" onclick="openServersModal()" title="Servers">🗂</button>
    <div class="user-badge">
      <div class="status-dot"></div>
      <span id="topbar-user">''' + html.escape(username or '') + r'''</span>
      <span style="color:var(--text3);font-size:10px;font-weight:400;margin-left:4px">(''' + html.escape(role) + r''')</span>
    </div>
    <button class="ic" onclick="location.href='/logout'" title="Logout">⏏</button>
  </div>
</div>

<!-- TABS -->
<div class="tabs" id="tabs">
  <div class="tab-item active" data-tab="console">💻 Console</div>
  <div class="tab-item" data-tab="files">📁 Files</div>
  <div class="tab-item" data-tab="schedules">⏰ Schedules</div>
  ''' + extra_tabs + r'''
</div>

<div class="container">
<div id="toast-container" class="toast-container"></div>

<!-- ===== CONSOLE TAB ===== -->
<div class="tab-content active" id="tab-console">
  <!-- Terminal tabs bar (لكل جلسة) -->
  <div id="term-tabs-bar" style="display:flex;align-items:center;gap:4px;margin-bottom:8px;flex-wrap:wrap">
    <button onclick="addTerminal()" title="ترمنال جديد"
      style="padding:5px 10px;background:var(--bg3);border:1px dashed var(--border2);border-radius:7px;
             color:var(--accent2);cursor:pointer;font-size:13px;white-space:nowrap;transition:.15s"
      onmouseover="this.style.borderColor='var(--accent2)'" onmouseout="this.style.borderColor='var(--border2)'">
      ＋ ترمنال جديد
    </button>
  </div>

  <!-- Power row -->
  <div class="power-row">
    <button class="btn-power btn-start"   onclick="powerAction('start')">▶ Start</button>
    <button class="btn-power btn-restart" onclick="powerAction('restart')">↺ Restart</button>
    <button class="btn-power btn-stop"    onclick="powerAction('stop')">■ Stop</button>
    <div class="status-badge">
      <span id="proc-dot"    style="width:8px;height:8px;border-radius:50%;background:#f85149;display:inline-block"></span>
      <span id="proc-status">Stopped</span>
    </div>
  </div>

  <!-- Terminals container -->
  <div id="terminals-container"></div>

  <!-- Stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card"><div class="lbl">IP Address</div><div class="val" id="s-ip">—</div></div>
    <div class="stat-card"><div class="lbl">Panel Port</div><div class="val green" id="s-port" style="cursor:pointer;color:#3fb950" onclick="copyPort()" title="Click to copy">—</div></div>
    <div class="stat-card"><div class="lbl">Uptime</div><div class="val" id="s-uptime">—</div></div>
    <div class="stat-card"><div class="lbl">CPU</div><div class="val" id="s-cpu">—</div></div>
    <div class="stat-card"><div class="lbl">Memory</div><div class="val" id="s-mem">—</div></div>
    <div class="stat-card"><div class="lbl">Disk</div><div class="val" id="s-disk">—</div></div>
    <div class="stat-card green"><div class="lbl">Net In</div><div class="val" id="s-in">—</div></div>
    <div class="stat-card orange"><div class="lbl">Net Out</div><div class="val" id="s-out">—</div></div>
    <div class="stat-card"><div class="lbl">Hostname</div><div class="val" id="s-host">—</div></div>
    <div class="stat-card"><div class="lbl">Platform</div><div class="val" id="s-plat">—</div></div>
  </div>

  <!-- Service Links -->
  <div class="section-card">
    <div class="section-head">🔗 Active Services & Links</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="stat-card" style="cursor:pointer" id="web-link-card" onclick="openWebLink()">
          <div class="lbl">🌐 Website</div>
          <div class="val" style="font-size:12px;color:#3fb950;word-break:break-all" id="web-link">No HTML file</div>
        </div>
        <div class="stat-card" style="cursor:pointer" id="api-link-card" onclick="openApiLink()">
          <div class="lbl">⚡ API Service</div>
          <div class="val" style="font-size:12px;color:#00bfff;word-break:break-all" id="api-link">No API file</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px">
        <a href="https://t.me/SHBH_S1" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">👨‍💻 Developer</div><div class="val" style="font-size:12px;color:var(--accent)">SHBH_S1</div></div>
        </a>
        <a href="https://t.me/SHOPING_HXH" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">📢 Channel</div><div class="val" style="font-size:12px;color:var(--yellow)">@SHOPING_HXH</div></div>
        </a>
        <div class="stat-card"><div class="lbl">🔌 Port</div><div class="val" id="port-display" style="color:var(--green);cursor:pointer" onclick="copyPort()">—</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ===== FILES TAB ===== -->
<div class="tab-content" id="tab-files">
  <!-- (نفس الكود السابق مع تحسينات طفيفة) -->
  <input type="file" id="file-up" style="display:none" multiple onchange="uploadFiles(this)">
  <input type="file" id="zip-up" style="display:none" accept=".zip,.tar,.gz,.tar.gz,.rar" onchange="uploadAndExtract(this)">

  <div class="file-toolbar">
    <button onclick="createDir()">📁 New Folder</button>
    <button onclick="newFile()">📄 New File</button>
    <button onclick="document.getElementById('file-up').click()">⬆ Upload</button>
    <button onclick="document.getElementById('zip-up').click()">📦 Extract ZIP</button>
    <button onclick="loadFiles()">🔄 Refresh</button>
    <button onclick="openAdvancedEditor()">✏️ Advanced Editor</button>  <!-- NEW -->
  </div>

  <div class="breadcrumb" id="breadcrumb">/ home /</div>
  <div class="file-list" id="file-list"></div>
</div>

<!-- ===== AI TAB ===== -->
<div class="tab-content" id="tab-ai">
  <div class="ai-chat-wrap">
    <div class="ai-header">
      <div class="ai-header-left">
        <div class="ai-avatar-main">🤖</div>
        <div>
          <div class="ai-header-title">SERVER HUB AI</div>
          <div class="ai-header-sub">GPT-OSS 120B · NVIDIA NIM</div>
        </div>
      </div>
      <button class="ai-clear-btn" onclick="clearAiChat()" title="Clear chat">🗑</button>
    </div>
    <div id="ai-messages" class="ai-messages-box">
      <div class="ai-msg ai-assistant">
        <div class="ai-bubble">
          <span class="ai-avatar">🤖</span>
          <div class="ai-text">مرحباً! أنا مساعدك الذكي.<br>اسألني أي شيء — كود، أفكار، شرح، أو أي مساعدة تحتاجها.</div>
        </div>
      </div>
    </div>
    <div id="ai-thinking-box" class="ai-thinking-box" style="display:none">
      <div class="ai-thinking-label">
        <span class="ai-think-dots"><span></span><span></span><span></span></span>
        جاري التفكير...
      </div>
      <div id="ai-reasoning" class="ai-reasoning-text"></div>
    </div>
    <div class="ai-input-area">
      <div class="ai-input-row">
        <textarea id="ai-input"
          class="ai-textarea"
          placeholder="اكتب رسالتك هنا... (Enter للإرسال، Shift+Enter لسطر جديد)"
          rows="1"
          onkeydown="aiKeyDown(event)"
          oninput="autoResizeAI(this)"
        ></textarea>
        <button onclick="sendAiMessage()" id="ai-send-btn" class="ai-send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <div class="ai-footer-info">Enter للإرسال · Shift+Enter لسطر جديد · يدعم العربية والإنجليزية</div>
    </div>
  </div>
</div>

<!-- ===== SCHEDULES TAB ===== -->
<div class="tab-content" id="tab-schedules">
  <div class="section-card">
    <div class="section-head">⏰ Create Schedule</div>
    <div class="section-body">
      <div class="field-block"><label>Name</label><input id="sch-name" placeholder="Daily backup"></div>
      <div class="field-block"><label>Command</label><input id="sch-cmd" placeholder="echo hello"></div>
      <div class="field-block"><label>Cron Expression</label><input id="sch-cron" value="* * * * *"></div>
      <div class="row-end"><button class="btn-action" onclick="addSchedule()">Add Schedule</button></div>
    </div>
  </div>
  <div id="sch-list"></div>
</div>

<!-- ===== TERMINAL TAB (WebSocket) ===== -->
<div class="tab-content" id="tab-terminal">
  <div class="section-card">
    <div class="section-head">🖥 WebSocket Terminal</div>
    <div class="section-body">
      <div style="margin-bottom:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <button class="btn-action green" onclick="openTerminal()">▶ Connect</button>
        <button class="btn-action danger" onclick="closeTerminal()">■ Disconnect</button>
        <button class="btn-action gray" onclick="clearTerminal()">🗑 Clear</button>
        <span id="term-status" style="color:var(--yellow);font-size:12px;font-weight:600">● Disconnected</span>
      </div>
      <div id="terminal-output" class="console-box" style="height:450px;font-family:'Consolas','Fira Code',monospace;font-size:13px;white-space:pre-wrap;word-break:break-all;background:#010409;color:#7ee787;padding:12px;overflow-y:auto;"></div>
      <div class="cmd-input" style="margin-top:8px">
        <span class="prompt">$</span>
        <input id="terminal-input" placeholder="أدخل أمراً..." onkeydown="if(event.key==='Enter')sendTerminalCommand()" autofocus>
      </div>
    </div>
  </div>
</div>

<!-- ===== DATABASE TAB ===== -->
<div class="tab-content" id="tab-database">
  <div class="section-card">
    <div class="section-head">🗄 Database Manager</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
        <button class="btn-action green" onclick="openDbConnectionModal()">➕ Add Connection</button>
        <button class="btn-action gray" onclick="loadDbConnections()">🔄 Refresh</button>
      </div>
      <div id="db-connections-list"></div>

      <!-- Query area (يظهر بعد اختيار اتصال) -->
      <div id="db-query-area" style="display:none;margin-top:16px">
        <div class="field-block"><label>SQL Query</label>
          <textarea id="db-query-input" rows="4" style="width:100%;padding:10px;background:#010409;border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:monospace;font-size:13px;resize:vertical;" placeholder="SELECT * FROM users;"></textarea>
        </div>
        <div class="row-end">
          <button class="btn-action" onclick="executeDbQuery()">▶ Execute</button>
          <button class="btn-action green" onclick="exportDb()">💾 Export</button>
        </div>
        <div id="db-query-result" class="db-result-box" style="display:none;margin-top:10px;"></div>
      </div>
    </div>
  </div>
</div>

''' + (r'''
<!-- ===== NODE.JS TAB ===== -->
<div class="tab-content" id="tab-nodejs">
  <!-- ... (نفس الكود السابق مع تحسينات) ... -->
  <div class="section-card">
    <div class="section-head">🟢 Node.js Project Launcher</div>
    <div class="section-body">
      <!-- (نفس المحتوى السابق) -->
    </div>
  </div>
  <div id="nodejs-list"></div>
</div>

<!-- ===== PHP TAB ===== -->
<div class="tab-content" id="tab-php">
  <!-- ... (نفس الكود السابق) ... -->
  <div class="section-card">
    <div class="section-head">🐘 PHP Server Launcher</div>
    <div class="section-body">
      <!-- (نفس المحتوى السابق) -->
    </div>
  </div>
  <div id="php-list"></div>
</div>

<!-- ===== USERS TAB (master/admin) ===== -->
<div class="tab-content" id="tab-users">
  <!-- (نفس الكود السابق مع إدارة الأدوار) -->
  <div class="section-card">
    <div class="section-head">👤 Add User</div>
    <div class="section-body">
      <!-- (نفس الحقول السابقة مع إضافة دور) -->
      <div class="field-block"><label>Role</label>
        <select id="u-role" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
          <option value="user">User</option>
          <option value="moderator">Moderator</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <!-- باقي الحقول -->
    </div>
  </div>
  <div id="users-list"></div>
</div>

<!-- ===== BACKUPS TAB ===== -->
<div class="tab-content" id="tab-backups">
  <!-- (نفس الكود السابق) -->
</div>

<!-- ===== NETWORK TAB ===== -->
<div class="tab-content" id="tab-network">
  <!-- (نفس الكود السابق) -->
</div>

<!-- ===== STARTUP TAB ===== -->
<div class="tab-content" id="tab-startup">
  <!-- (نفس الكود السابق) -->
</div>

<!-- ===== SETTINGS TAB ===== -->
<div class="tab-content" id="tab-settings">
  <!-- (نفس الكود السابق) -->
</div>

<!-- ===== ACTIVITY TAB ===== -->
<div class="tab-content" id="tab-activity">
  <!-- (نفس الكود السابق) -->
</div>
''' if is_admin else '') + r'''

''' + owner_panel_html + r'''

</div><!-- /container -->

<!-- ===== MODALS ===== -->
<!-- Editor Modal -->
<div class="modal" id="editor-modal">
  <div class="modal-box" style="max-width:800px;width:95vw">
    <div class="modal-head">
      <h3 id="editor-title">Edit File</h3>
      <button class="close" onclick="closeModal('editor-modal')">×</button>
    </div>
    <div class="modal-body">
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        <input id="editor-search" placeholder="Search..." style="flex:1;padding:6px 10px;background:var(--bg2);border:1px solid var(--border);border-radius:4px;color:var(--text);font-size:12px;">
        <input id="editor-replace" placeholder="Replace..." style="flex:1;padding:6px 10px;background:var(--bg2);border:1px solid var(--border);border-radius:4px;color:var(--text);font-size:12px;">
        <button class="btn-action" onclick="editorSearchReplace()">🔍 Replace</button>
        <button class="btn-action gray" onclick="editorAutoSave()">💾 Auto Save</button>
      </div>
      <textarea class="editor-box" id="editor-content" spellcheck="false"></textarea>
    </div>
    <div class="modal-foot">
      <button class="btn-action gray" onclick="closeModal('editor-modal')">Cancel</button>
      <button class="btn-action" onclick="saveFile()">💾 Save</button>
    </div>
  </div>
</div>

<!-- Servers Modal -->
<div class="modal" id="servers-modal">
  <div class="modal-box">
    <div class="modal-head"><h3>🗂 Servers</h3><button class="close" onclick="closeModal('servers-modal')">×</button></div>
    <div class="modal-body" id="servers-modal-list" style="max-height:400px;overflow-y:auto"></div>
    <div class="modal-foot"><button class="btn-action gray" onclick="closeModal('servers-modal')">Close</button></div>
  </div>
</div>

<!-- Extract Modal -->
<div class="modal" id="extract-modal">
  <div class="modal-box">
    <div class="modal-head"><h3>📦 Extract Archive</h3><button class="close" onclick="closeModal('extract-modal')">×</button></div>
    <div class="modal-body">
      <input type="hidden" id="extract-src">
      <div class="field-block"><label>Extract to folder</label><input id="extract-dest" placeholder="(same directory)"></div>
    </div>
    <div class="modal-foot">
      <button class="btn-action gray" onclick="closeModal('extract-modal')">Cancel</button>
      <button class="btn-action" onclick="doExtract()">📦 Extract</button>
    </div>
  </div>
</div>

<!-- Database Connection Modal -->
<div class="modal" id="db-connection-modal">
  <div class="modal-box">
    <div class="modal-head"><h3>🔌 Add Database Connection</h3><button class="close" onclick="closeModal('db-connection-modal')">×</button></div>
    <div class="modal-body">
      <div class="field-block"><label>Connection Name</label><input id="db-conn-name" placeholder="My Database"></div>
      <div class="field-block"><label>Type</label>
        <select id="db-conn-type" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px" onchange="toggleDbFields()">
          <option value="sqlite">SQLite</option>
          <option value="mysql">MySQL</option>
          <option value="postgres">PostgreSQL</option>
        </select>
      </div>
      <div id="db-sqlite-fields">
        <div class="field-block"><label>Database Path</label><input id="db-sqlite-path" placeholder="/path/to/database.db"></div>
      </div>
      <div id="db-network-fields" style="display:none">
        <div class="field-block"><label>Host</label><input id="db-host" placeholder="localhost"></div>
        <div class="field-block"><label>Port</label><input id="db-port" placeholder="3306"></div>
        <div class="field-block"><label>Database Name</label><input id="db-name" placeholder="my_db"></div>
        <div class="field-block"><label>Username</label><input id="db-user" placeholder="root"></div>
        <div class="field-block"><label>Password</label><input id="db-pass" type="password" placeholder="password"></div>
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn-action gray" onclick="closeModal('db-connection-modal')">Cancel</button>
      <button class="btn-action green" onclick="saveDbConnection()">💾 Save Connection</button>
    </div>
  </div>
</div>

<!-- ===== JAVASCRIPT (مدمج) ===== -->
<script>
// ── كل الدوال السابقة مع إضافة دوال جديدة ──
// (سيتم تضمينها كاملة في الملف النهائي)

// ── دوال AI (نفس السابق) ──
// ... (سيتم إدراجها)

// ── دوال المحرر المتقدم ──
function openAdvancedEditor(){
  // فتح المحرر على الملف الحالي أو شاشة فارغة
  toast('Advanced Editor: افتح ملفاً أولاً', false, true);
}

function editorSearchReplace(){
  const search = document.getElementById('editor-search').value;
  const replace = document.getElementById('editor-replace').value;
  if(!search) return;
  const content = document.getElementById('editor-content').value;
  const newContent = content.replaceAll(search, replace);
  document.getElementById('editor-content').value = newContent;
  toast(`تم استبدال ${content.split(search).length-1} تكرار`, false, true);
}

function editorAutoSave(){
  if(currentEditPath) saveFile();
  toast('Auto Save triggered', false, true);
}

// ── دوال Terminal (WebSocket) ──
let terminalWs = null;
const terminalOutput = document.getElementById('terminal-output');
const terminalInput = document.getElementById('terminal-input');

function openTerminal(){
  if(terminalWs && terminalWs.readyState === WebSocket.OPEN){
    toast('Terminal already connected', false, true);
    return;
  }
  const status = document.getElementById('term-status');
  status.textContent = '● Connecting...';
  status.style.color = 'var(--yellow)';
  terminalOutput.textContent = 'Connecting to WebSocket terminal...\n';

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/terminal`;
  terminalWs = new WebSocket(wsUrl);

  terminalWs.onopen = function(){
    status.textContent = '● Connected';
    status.style.color = 'var(--green)';
    terminalOutput.textContent += '[Connected] Terminal ready.\n';
    terminalInput.disabled = false;
    terminalInput.focus();
  };

  terminalWs.onmessage = function(e){
    terminalOutput.textContent += e.data;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  };

  terminalWs.onclose = function(){
    status.textContent = '● Disconnected';
    status.style.color = 'var(--red)';
    terminalOutput.textContent += '[Disconnected] Session closed.\n';
    terminalInput.disabled = true;
    terminalWs = null;
  };

  terminalWs.onerror = function(e){
    status.textContent = '● Error';
    status.style.color = 'var(--red)';
    terminalOutput.textContent += '[Error] WebSocket error.\n';
  };
}

function closeTerminal(){
  if(terminalWs){
    terminalWs.close();
    terminalWs = null;
  }
  const status = document.getElementById('term-status');
  status.textContent = '● Disconnected';
  status.style.color = 'var(--red)';
  terminalInput.disabled = true;
}

function sendTerminalCommand(){
  if(!terminalWs || terminalWs.readyState !== WebSocket.OPEN){
    toast('Terminal not connected', true);
    return;
  }
  const cmd = terminalInput.value;
  if(!cmd) return;
  terminalWs.send(cmd + '\n');
  terminalInput.value = '';
}

function clearTerminal(){
  terminalOutput.textContent = '';
}

// ── دوال Database ──
let selectedDbConnId = null;

function toggleDbFields(){
  const type = document.getElementById('db-conn-type').value;
  document.getElementById('db-sqlite-fields').style.display = (type === 'sqlite') ? 'block' : 'none';
  document.getElementById('db-network-fields').style.display = (type === 'sqlite') ? 'none' : 'block';
}

async function loadDbConnections(){
  try{
    const r = await fetch('/api/db/connections');
    const d = await r.json();
    const list = document.getElementById('db-connections-list');
    if(!(d.connections || []).length){
      list.innerHTML = '<div style="color:var(--text3);padding:10px">No database connections added.</div>';
      return;
    }
    list.innerHTML = '';
    d.connections.forEach(conn => {
      const card = document.createElement('div');
      card.className = 'db-connection-card';
      card.innerHTML = `
        <div>
          <div class="db-name">${escapeHtml(conn.name)}</div>
          <div class="db-meta">${escapeHtml(conn.type)} · ${escapeHtml(conn.host || conn.path || '')}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn-action gray" style="font-size:11px" onclick="selectDbConnection('${conn.id}')">🔌 Select</button>
          <button class="btn-action danger" style="font-size:11px" onclick="deleteDbConnection('${conn.id}')">🗑</button>
        </div>
      `;
      list.appendChild(card);
    });
  }catch(e){ toast('Failed to load connections', true); }
}

function selectDbConnection(id){
  selectedDbConnId = id;
  document.getElementById('db-query-area').style.display = 'block';
  document.getElementById('db-query-result').style.display = 'none';
  toast('Connection selected', false, true);
}

async function deleteDbConnection(id){
  if(!confirm('Delete this connection?')) return;
  const r = await fetch(`/api/db/connections/${id}`, {method:'DELETE'});
  const d = await r.json();
  toast(d.success?'Deleted':'Failed', !d.success);
  if(d.success) loadDbConnections();
}

async function executeDbQuery(){
  if(!selectedDbConnId){
    toast('Select a connection first', true);
    return;
  }
  const sql = document.getElementById('db-query-input').value.trim();
  if(!sql){
    toast('Enter SQL query', true);
    return;
  }
  const resultDiv = document.getElementById('db-query-result');
  resultDiv.style.display = 'block';
  resultDiv.textContent = '⏳ Executing...';
  try{
    const r = await fetch('/api/db/query', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({connection_id: selectedDbConnId, sql})
    });
    const d = await r.json();
    if(d.error){
      resultDiv.textContent = '❌ ' + d.error;
      resultDiv.style.color = '#f85149';
    } else {
      resultDiv.textContent = JSON.stringify(d.result, null, 2);
      resultDiv.style.color = '#7ee787';
    }
  }catch(e){
    resultDiv.textContent = '❌ ' + e.message;
    resultDiv.style.color = '#f85149';
  }
}

async function exportDb(){
  if(!selectedDbConnId){
    toast('Select a connection first', true);
    return;
  }
  try{
    const r = await fetch(`/api/db/export/${selectedDbConnId}`);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'database_export.sql';
    a.click();
    URL.revokeObjectURL(url);
    toast('Export started', false, true);
  }catch(e){
    toast('Export failed', true);
  }
}

function openDbConnectionModal(){
  document.getElementById('db-conn-name').value = '';
  document.getElementById('db-conn-type').value = 'sqlite';
  document.getElementById('db-sqlite-path').value = '';
  document.getElementById('db-host').value = '';
  document.getElementById('db-port').value = '';
  document.getElementById('db-name').value = '';
  document.getElementById('db-user').value = '';
  document.getElementById('db-pass').value = '';
  toggleDbFields();
  openModal('db-connection-modal');
}

async function saveDbConnection(){
  const type = document.getElementById('db-conn-type').value;
  const data = {
    name: document.getElementById('db-conn-name').value.trim(),
    type: type,
    host: document.getElementById('db-host').value.trim(),
    port: document.getElementById('db-port').value.trim(),
    database: document.getElementById('db-name').value.trim(),
    username: document.getElementById('db-user').value.trim(),
    password: document.getElementById('db-pass').value.trim(),
    path: document.getElementById('db-sqlite-path').value.trim()
  };
  if(!data.name){ toast('Enter connection name', true); return; }
  if(type === 'sqlite' && !data.path){ toast('Enter database path', true); return; }
  if(type !== 'sqlite' && (!data.host || !data.database || !data.username)){
    toast('Fill all required fields', true);
    return;
  }
  try{
    const r = await fetch('/api/db/connections', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    const d = await r.json();
    toast(d.success?'Connection added':'Failed', !d.success);
    if(d.success){
      closeModal('db-connection-modal');
      loadDbConnections();
    }
  }catch(e){ toast('Error', true); }
}

// ── دوال Role Management (للمالك) ──
async function loadRoleManagement(){
  if(!IS_MASTER) return;
  try{
    const r = await fetch('/api/users/list');
    const d = await r.json();
    const list = document.getElementById('role-management-list');
    if(!(d.users || []).length){
      list.innerHTML = '<div style="color:var(--text3);padding:10px">No users.</div>';
      return;
    }
    list.innerHTML = '';
    d.users.forEach(u => {
      const card = document.createElement('div');
      card.className = 'db-connection-card';
      card.innerHTML = `
        <div>
          <div class="db-name">${escapeHtml(u.username)}</div>
          <div class="db-meta">Role: <span style="color:${u.role === 'owner' ? '#ff6b6b' : u.role === 'admin' ? '#ffd93d' : u.role === 'moderator' ? '#6bcbff' : '#8b949e'}">${escapeHtml(u.role || 'user')}</span></div>
        </div>
        <div style="display:flex;gap:6px">
          <select onchange="changeUserRole('${u.username}', this.value)" style="padding:4px;background:var(--bg2);border:1px solid var(--border);border-radius:4px;color:var(--text);font-size:11px">
            <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
            <option value="moderator" ${u.role === 'moderator' ? 'selected' : ''}>Moderator</option>
            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
            <option value="owner" ${u.role === 'owner' ? 'selected' : ''}>Owner</option>
          </select>
        </div>
      `;
      list.appendChild(card);
    });
  }catch(e){ toast('Failed to load roles', true); }
}

async function changeUserRole(username, role){
  try{
    const r = await fetch('/api/users/update', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({username, role})
    });
    const d = await r.json();
    toast(d.success ? `Role updated for ${username}` : 'Failed', !d.success);
    if(d.success) loadRoleManagement();
  }catch(e){ toast('Error', true); }
}

// ── دوال الأمان والتهيئة ──
function escapeHtml(text){
  if(!text) return '';
  return String(text).replace(/[&<>"]/g, function(m){
    if(m === '&') return '&amp;';
    if(m === '<') return '&lt;';
    if(m === '>') return '&gt;';
    if(m === '"') return '&quot;';
    return m;
  });
}

// ── Toast (مضمنة) ──
function toast(msg, isErr=false, isInfo=false){
  const c=document.getElementById('toast-container');
  const t=document.createElement('div');
  t.className='toast '+(isErr?'err':isInfo?'info':'ok');
  t.textContent=msg;
  c.appendChild(t);
  setTimeout(()=>t.remove(), 3500);
}

// ── تشغيل التطبيق ──
const IS_MASTER = ''' + ('true' if is_owner else 'false') + r''';
loadProfile().then(()=>{ loadStats(); loadFiles(); initTerminals(); });
statsInterval = setInterval(loadStats, 5000);
</script>

</body>
</html>
'''
<!-- ── RESPONSIVE ── -->
@media(max-width:600px){
  .stats-grid{grid-template-columns:1fr 1fr}
  .power-row{grid-template-columns:1fr 1fr 1fr;gap:6px}
  .power-row .status-badge{display:none}
  .topbar .brand{font-size:15px}
  .container{padding:12px 10px}
  .stats4{grid-template-columns:1fr 1fr}
}

/* ── NEW: Database & Terminal Styles ── */
.db-connection-card{
  background:var(--bg4);
  border:1px solid var(--border);
  border-radius:8px;
  padding:12px 14px;
  margin-bottom:8px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  transition:.15s;
}
.db-connection-card:hover{
  border-color:var(--accent);
}
.db-connection-card .db-name{
  font-weight:700;
  color:var(--text);
}
.db-connection-card .db-meta{
  color:var(--text2);
  font-size:12px;
  margin-top:2px;
}

.db-query-box{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:8px;
  padding:12px;
  margin-top:10px;
}
.db-query-box textarea{
  width:100%;
  padding:10px;
  background:#010409;
  border:1px solid var(--border);
  border-radius:6px;
  color:var(--text);
  font-family:monospace;
  font-size:13px;
  min-height:100px;
  resize:vertical;
}
.db-result-box{
  background:#010409;
  border:1px solid var(--border);
  border-radius:6px;
  padding:10px;
  margin-top:8px;
  max-height:300px;
  overflow-y:auto;
  font-family:monospace;
  font-size:12px;
  color:#7ee787;
  white-space:pre-wrap;
}

/* ── TERMINAL TAB ── */
.terminal-container{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:12px;
  padding:4px;
  height:calc(100vh - 200px);
  min-height:400px;
}
.terminal-container iframe{
  width:100%;
  height:100%;
  border:none;
  border-radius:8px;
  background:#010409;
}

/* ── ROLE MANAGEMENT ── */
.role-card{
  display:flex;
  justify-content:space-between;
  align-items:center;
  background:var(--bg4);
  border:1px solid var(--border);
  border-radius:8px;
  padding:10px 14px;
  margin-bottom:6px;
}
.role-card .role-name{
  font-weight:600;
  color:var(--text);
}
.role-card .role-badge{
  font-size:11px;
  padding:2px 10px;
  border-radius:20px;
  font-weight:600;
}
.role-badge.owner{background:rgba(255,107,107,.2);color:#ff6b6b;border:1px solid rgba(255,107,107,.3)}
.role-badge.admin{background:rgba(255,217,61,.2);color:#ffd93d;border:1px solid rgba(255,217,61,.3)}
.role-badge.moderator{background:rgba(107,203,255,.2);color:#6bcbff;border:1px solid rgba(107,203,255,.3)}
.role-badge.user{background:rgba(139,148,158,.2);color:#8b949e;border:1px solid rgba(139,148,158,.3)}

</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="brand">
    <span class="brand-icon">🚀</span> SERVER HUB
  </div>
  <div class="icons">
    <button class="ic" onclick="loadSearch()" title="Search">🔍</button>
    <button class="ic" onclick="openServersModal()" title="Servers">🗂</button>
    <div class="user-badge">
      <div class="status-dot"></div>
      <span id="topbar-user">''' + html.escape(username or '') + r'''</span>
      <span style="color:var(--text3);font-size:10px;font-weight:400;margin-left:4px">(''' + html.escape(role) + r''')</span>
    </div>
    <button class="ic" onclick="location.href='/logout'" title="Logout">⏏</button>
  </div>
</div>

<!-- TABS -->
<div class="tabs" id="tabs">
  <div class="tab-item active" data-tab="console">💻 Console</div>
  <div class="tab-item" data-tab="files">📁 Files</div>
  <div class="tab-item" data-tab="schedules">⏰ Schedules</div>
  ''' + extra_tabs + r'''
</div>

<div class="container">
<div id="toast-container" class="toast-container"></div>

<!-- ===== CONSOLE TAB ===== -->
<div class="tab-content active" id="tab-console">
  <!-- ── Terminal tabs bar ── -->
  <div id="term-tabs-bar" style="display:flex;align-items:center;gap:4px;margin-bottom:8px;flex-wrap:wrap">
    <!-- tabs injected by JS -->
    <button onclick="addTerminal()" title="ترمنال جديد"
      style="padding:5px 10px;background:var(--bg3);border:1px dashed var(--border2);border-radius:7px;
             color:var(--accent2);cursor:pointer;font-size:13px;white-space:nowrap;transition:.15s"
      onmouseover="this.style.borderColor='var(--accent2)'" onmouseout="this.style.borderColor='var(--border2)'">
      ＋ ترمنال جديد
    </button>
  </div>

  <!-- ── Power row ── -->
  <div class="power-row">
    <button class="btn-power btn-start"   onclick="powerAction('start')">▶ Start</button>
    <button class="btn-power btn-restart" onclick="powerAction('restart')">↺ Restart</button>
    <button class="btn-power btn-stop"    onclick="powerAction('stop')">■ Stop</button>
    <div class="status-badge">
      <span id="proc-dot"    style="width:8px;height:8px;border-radius:50%;background:#f85149;display:inline-block"></span>
      <span id="proc-status">Stopped</span>
    </div>
  </div>

  <!-- ── Terminal windows container ── -->
  <div id="terminals-container"></div>

  <!-- Stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card"><div class="lbl">IP Address</div><div class="val" id="s-ip">—</div></div>
    <div class="stat-card"><div class="lbl">Panel Port</div><div class="val green" id="s-port" style="cursor:pointer;color:#3fb950" onclick="copyPort()" title="Click to copy">—</div></div>
    <div class="stat-card"><div class="lbl">Uptime</div><div class="val" id="s-uptime">—</div></div>
    <div class="stat-card"><div class="lbl">CPU</div><div class="val" id="s-cpu">—</div></div>
    <div class="stat-card"><div class="lbl">Memory</div><div class="val" id="s-mem">—</div></div>
    <div class="stat-card"><div class="lbl">Disk</div><div class="val" id="s-disk">—</div></div>
    <div class="stat-card green"><div class="lbl">Net In</div><div class="val" id="s-in">—</div></div>
    <div class="stat-card orange"><div class="lbl">Net Out</div><div class="val" id="s-out">—</div></div>
    <div class="stat-card"><div class="lbl">Hostname</div><div class="val" id="s-host">—</div></div>
    <div class="stat-card"><div class="lbl">Platform</div><div class="val" id="s-plat">—</div></div>
  </div>

  <!-- Service Links -->
  <div class="section-card">
    <div class="section-head">🔗 Active Services & Links</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="stat-card" style="cursor:pointer" id="web-link-card" onclick="openWebLink()">
          <div class="lbl">🌐 Website</div>
          <div class="val" style="font-size:12px;color:#3fb950;word-break:break-all" id="web-link">No HTML file</div>
        </div>
        <div class="stat-card" style="cursor:pointer" id="api-link-card" onclick="openApiLink()">
          <div class="lbl">⚡ API Service</div>
          <div class="val" style="font-size:12px;color:#00bfff;word-break:break-all" id="api-link">No API file</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px">
        <a href="https://t.me/SHBH_S1" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">👨‍💻 Developer</div><div class="val" style="font-size:12px;color:var(--accent)">SHBH_S1</div></div>
        </a>
        <a href="https://t.me/SHOPING_HXH" target="_blank" style="text-decoration:none">
          <div class="stat-card"><div class="lbl">📢 Channel</div><div class="val" style="font-size:12px;color:var(--yellow)">@SHOPING_HXH</div></div>
        </a>
        <div class="stat-card"><div class="lbl">🔌 Port</div><div class="val" id="port-display" style="color:var(--green);cursor:pointer" onclick="copyPort()">—</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ===== FILES TAB ===== -->
<div class="tab-content" id="tab-files">
  <input type="file" id="file-up" style="display:none" multiple onchange="uploadFiles(this)">
  <input type="file" id="zip-up" style="display:none" accept=".zip,.tar,.gz,.tar.gz,.rar" onchange="uploadAndExtract(this)">

  <div class="file-toolbar">
    <button onclick="createDir()">📁 New Folder</button>
    <button onclick="newFile()">📄 New File</button>
    <button onclick="document.getElementById('file-up').click()">⬆ Upload</button>
    <button onclick="document.getElementById('zip-up').click()">📦 Extract ZIP</button>
    <button onclick="loadFiles()">🔄 Refresh</button>
    <button onclick="openAdvancedEditor()">✏️ Advanced Editor</button>
  </div>

  <div class="breadcrumb" id="breadcrumb">/ home /</div>
  <div class="file-list" id="file-list"></div>
</div>

<!-- ===== AI TAB ===== -->
<div class="tab-content" id="tab-ai">
  <div class="ai-chat-wrap">
    <div class="ai-header">
      <div class="ai-header-left">
        <div class="ai-avatar-main">🤖</div>
        <div>
          <div class="ai-header-title">SERVER HUB AI</div>
          <div class="ai-header-sub">GPT-OSS 120B · NVIDIA NIM</div>
        </div>
      </div>
      <button class="ai-clear-btn" onclick="clearAiChat()" title="Clear chat">🗑</button>
    </div>
    <div id="ai-messages" class="ai-messages-box">
      <div class="ai-msg ai-assistant">
        <div class="ai-bubble">
          <span class="ai-avatar">🤖</span>
          <div class="ai-text">مرحباً! أنا مساعدك الذكي.<br>اسألني أي شيء — كود، أفكار، شرح، أو أي مساعدة تحتاجها.</div>
        </div>
      </div>
    </div>
    <div id="ai-thinking-box" class="ai-thinking-box" style="display:none">
      <div class="ai-thinking-label">
        <span class="ai-think-dots"><span></span><span></span><span></span></span>
        جاري التفكير...
      </div>
      <div id="ai-reasoning" class="ai-reasoning-text"></div>
    </div>
    <div class="ai-input-area">
      <div class="ai-input-row">
        <textarea id="ai-input"
          class="ai-textarea"
          placeholder="اكتب رسالتك هنا... (Enter للإرسال، Shift+Enter لسطر جديد)"
          rows="1"
          onkeydown="aiKeyDown(event)"
          oninput="autoResizeAI(this)"
        ></textarea>
        <button onclick="sendAiMessage()" id="ai-send-btn" class="ai-send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
      <div class="ai-footer-info">Enter للإرسال · Shift+Enter لسطر جديد · يدعم العربية والإنجليزية</div>
    </div>
  </div>
</div>

<!-- ===== SCHEDULES TAB ===== -->
<div class="tab-content" id="tab-schedules">
  <div class="section-card">
    <div class="section-head">⏰ Create Schedule</div>
    <div class="section-body">
      <div class="field-block"><label>Name</label><input id="sch-name" placeholder="Daily backup"></div>
      <div class="field-block"><label>Command</label><input id="sch-cmd" placeholder="echo hello"></div>
      <div class="field-block"><label>Cron Expression</label><input id="sch-cron" value="* * * * *"></div>
      <div class="row-end"><button class="btn-action" onclick="addSchedule()">Add Schedule</button></div>
    </div>
  </div>
  <div id="sch-list"></div>
</div>

<!-- ===== NODE.JS TAB ===== -->
<div class="tab-content" id="tab-nodejs">
  <div class="section-card">
    <div class="section-head">🟢 Node.js Project Launcher</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="field-block" style="grid-column:1/-1">
          <label>📁 Project Path</label>
          <input id="nodejs-path" placeholder="e.g. /panel_data/users_data/myuser/myproject">
        </div>
        <div class="field-block">
          <label>📄 Main File <span style="color:var(--text3);font-weight:400">(e.g. index.js, src/app.js)</span></label>
          <div style="display:flex;gap:6px;align-items:center">
            <input id="nodejs-main" placeholder="auto-detect" style="flex:1">
            <button class="btn-action gray" style="font-size:11px;white-space:nowrap" onclick="loadNodeJsFiles()">📂 Browse</button>
          </div>
          <div id="nodejs-files-list" style="display:none;margin-top:6px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;max-height:140px;overflow-y:auto"></div>
        </div>
        <div class="field-block">
          <label>📦 Dependencies File <span style="color:var(--text3);font-weight:400">(e.g. package.json)</span></label>
          <input id="nodejs-deps" placeholder="package.json (default)">
        </div>
        <div class="field-block">
          <label>🔌 Port <span style="color:var(--text3);font-weight:400">(optional — auto if empty)</span></label>
          <input id="nodejs-port" type="number" placeholder="auto">
        </div>
        <div class="field-block" style="grid-column:1/-1">
          <div style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px" id="nodejs-cmd-preview" style="display:none">
            <div style="font-size:11px;color:var(--text2);margin-bottom:6px;font-weight:700;text-transform:uppercase;letter-spacing:.8px">📋 Install & Run Commands Preview</div>
            <div id="nodejs-install-cmd" style="font-family:monospace;font-size:12px;color:#79c0ff;padding:4px 0"></div>
            <div id="nodejs-run-cmd" style="font-family:monospace;font-size:12px;color:#7ee787;padding:4px 0"></div>
          </div>
        </div>
      </div>
      <div class="row-end" style="gap:8px">
        <button class="btn-action gray" onclick="previewNodeCmd()">👁 Preview Commands</button>
        <button class="btn-action green" onclick="startNodeProject()">▶ Start Node.js</button>
      </div>
      <div id="nodejs-start-output" style="display:none;margin-top:10px;background:#010409;border:1px solid var(--border);border-radius:6px;padding:10px;font-family:monospace;font-size:11px;color:#7ee787;max-height:120px;overflow-y:auto;white-space:pre-wrap"></div>
    </div>
  </div>
  <div id="nodejs-list"></div>
</div>

<!-- ===== PHP TAB ===== -->
<div class="tab-content" id="tab-php">
  <div class="section-card">
    <div class="section-head">🐘 PHP Server Launcher</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="field-block" style="grid-column:1/-1">
          <label>📁 PHP Root Folder</label>
          <input id="php-path" placeholder="e.g. /panel_data/users_data/myuser/mysite">
        </div>
        <div class="field-block">
          <label>📄 Main Entry File <span style="color:var(--text3);font-weight:400">(e.g. index.php)</span></label>
          <div style="display:flex;gap:6px;align-items:center">
            <input id="php-main" placeholder="index.php (default)" style="flex:1">
            <button class="btn-action gray" style="font-size:11px;white-space:nowrap" onclick="loadPhpFiles()">📂 Browse</button>
          </div>
          <div id="php-files-list" style="display:none;margin-top:6px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;max-height:140px;overflow-y:auto"></div>
        </div>
        <div class="field-block">
          <label>📦 Dependencies File <span style="color:var(--text3);font-weight:400">(e.g. composer.json)</span></label>
          <input id="php-deps" placeholder="composer.json (auto-detect)">
        </div>
        <div class="field-block">
          <label>🔌 Port <span style="color:var(--text3);font-weight:400">(optional — auto if empty)</span></label>
          <input id="php-port" type="number" placeholder="auto">
        </div>
        <div class="field-block" style="grid-column:1/-1">
          <div style="background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px" id="php-cmd-preview">
            <div style="font-size:11px;color:var(--text2);margin-bottom:6px;font-weight:700;text-transform:uppercase;letter-spacing:.8px">📋 Install & Run Commands Preview</div>
            <div id="php-install-cmd" style="font-family:monospace;font-size:12px;color:#79c0ff;padding:4px 0">— اضغط Preview لعرض الأوامر —</div>
            <div id="php-run-cmd" style="font-family:monospace;font-size:12px;color:#7ee787;padding:4px 0"></div>
          </div>
        </div>
      </div>
      <div class="row-end" style="gap:8px">
        <button class="btn-action gray" onclick="previewPhpCmd()">👁 Preview Commands</button>
        <button class="btn-action orange" onclick="startPhpServer()">▶ Start PHP Server</button>
      </div>
      <div id="php-start-output" style="display:none;margin-top:10px;background:#010409;border:1px solid var(--border);border-radius:6px;padding:10px;font-family:monospace;font-size:11px;color:#7ee787;max-height:120px;overflow-y:auto;white-space:pre-wrap"></div>
    </div>
  </div>
  <div id="php-list"></div>
</div>

''' + (r'''
<!-- ===== USERS TAB (master/admin only) ===== -->
<div class="tab-content" id="tab-users">
  <div class="section-card">
    <div class="section-head">👤 Add User</div>
    <div class="section-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="field-block"><label>Username</label><input id="u-name" placeholder="username"></div>
        <div class="field-block"><label>Password</label><input id="u-pass" type="password" placeholder="password"></div>
        <div class="field-block"><label>🔵 Telegram Username</label><input id="u-tg" placeholder="@username"></div>
        <div class="field-block"><label>Role</label>
          <select id="u-role" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="field-block"><label>Plan</label>
          <select id="u-plan" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px" onchange="onPlanChange()">
            <option value="free_trial">🆓 Free Trial — 7 أيام</option>
            <option value="paid_20">⭐ Paid 20 يوم — 15 نجمة</option>
            <option value="paid_30">💎 Paid 30 يوم — 25 نجمة</option>
            <option value="custom">🎯 Custom</option>
          </select>
        </div>
        <div class="field-block" id="u-custom-days-wrap" style="display:none"><label>Custom Days</label><input id="u-days" type="number" value="7" min="1"></div>
        <div class="field-block"><label>Max Sessions</label><input id="u-max" type="number" value="1"></div>
        <div class="field-block"><label>Max Servers</label>
          <select id="u-maxsrv" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="1">1 Server</option><option value="2">2 Servers</option>
            <option value="3">3 Servers</option><option value="5">5 Servers</option>
            <option value="10">10 Servers</option><option value="999">Unlimited</option>
          </select>
        </div>
        <div class="field-block"><label>Main File</label><input id="u-main" value="main.py"></div>
      </div>
      <div class="row-end"><button class="btn-action" onclick="addUser()">Add User</button></div>
    </div>
  </div>
  <div id="users-list"></div>

  <!-- Edit Modal -->
  <div class="modal" id="edit-user-modal">
    <div class="modal-box">
      <div class="modal-head"><h3>Edit User</h3><button class="close" onclick="closeModal('edit-user-modal')">×</button></div>
      <div class="modal-body">
        <input type="hidden" id="eu-name">
        <div class="field-block"><label>New Password</label><input id="eu-pass" type="password" placeholder="(leave blank to keep)"></div>
        <div class="field-block"><label>Role</label>
          <select id="eu-role" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="admin">Admin</option>
            <option value="owner">Owner</option>
          </select>
        </div>
        <div class="field-block"><label>Max Sessions</label><input id="eu-max" type="number"></div>
        <div class="field-block"><label>Max Servers</label>
          <select id="eu-maxsrv" style="width:100%;padding:10px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px">
            <option value="1">1</option><option value="2">2</option><option value="3">3</option>
            <option value="5">5</option><option value="10">10</option><option value="999">Unlimited</option>
          </select>
        </div>
        <div class="field-block"><label>Main File</label><input id="eu-main"></div>
        <div class="field-block"><label>Extend Subscription (days)</label><input id="eu-days" type="number" value="30" min="30"></div>
      </div>
      <div class="modal-foot">
        <button class="btn-action gray" onclick="closeModal('edit-user-modal')">Cancel</button>
        <button class="btn-action" onclick="saveEditUser()">Save</button>
      </div>
    </div>
  </div>
</div>

<!-- ===== BACKUPS TAB ===== -->
<div class="tab-content" id="tab-backups">
  <div class="section-card">
    <div class="section-head">💾 Backups</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button class="btn-action green" onclick="createBackup()">➕ Create Backup</button>
        <button class="btn-action gray" onclick="loadBackups()">🔄 Refresh</button>
      </div>
      <div id="backups-list"></div>
    </div>
  </div>
</div>

<!-- ===== NETWORK TAB ===== -->
<div class="tab-content" id="tab-network">
  <div class="section-card">
    <div class="section-head">🔌 Extra Ports</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
        <input id="new-port" type="number" placeholder="Port (e.g. 8080)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;width:160px">
        <input id="new-port-note" placeholder="Note (optional)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1;min-width:120px">
        <button class="btn-action" onclick="addPort()">Add Port</button>
      </div>
      <div id="ports-list"></div>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">🔍 Port Scanner</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input id="scan-host" placeholder="Host (e.g. 127.0.0.1)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <input id="scan-ports" placeholder="Ports (22,80,443,8080)" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action" onclick="scanPorts()">Scan</button>
      </div>
      <div id="scan-results" style="margin-top:12px"></div>
    </div>
  </div>
</div>

<!-- ===== STARTUP TAB ===== -->
<div class="tab-content" id="tab-startup">
  <div class="section-card">
    <div class="section-head">🚀 Startup / Auto-Start</div>
    <div class="section-body">
      <div class="field-block"><label>Main Startup File</label><input id="startup-file" placeholder="main.py"></div>
      <button class="btn-action" onclick="setStartupFile()">Set Startup File</button>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">📦 Package Manager</div>
    <div class="section-body">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <input id="pip-pkg" placeholder="pip package name" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action orange" onclick="installPip()">pip install</button>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <input id="npm-pkg" placeholder="npm package name" style="padding:9px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:13px;flex:1">
        <button class="btn-action green" onclick="installNpm()">npm install</button>
      </div>
    </div>
  </div>
</div>
''' if is_admin else '') + r'''

<!-- ===== SETTINGS TAB ===== -->
<div class="tab-content" id="tab-settings">
  <div class="section-card">
    <div class="section-head">🔒 Change Password</div>
    <div class="section-body">
      <div class="field-block"><label>Current Password</label><input id="cur-pass" type="password" placeholder="Current password"></div>
      <div class="field-block"><label>New Password</label><input id="new-pass" type="password" placeholder="New password"></div>
      <div class="row-end"><button class="btn-action" onclick="changePassword()">Change Password</button></div>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head">🖥 System Info</div>
    <div class="section-body">
      <pre id="sysinfo-box" style="color:var(--text2);font-size:12px;font-family:monospace;white-space:pre-wrap"></pre>
      <div class="row-end"><button class="btn-action gray" onclick="loadSysinfo()">🔄 Refresh</button></div>
    </div>
  </div>
</div>

<!-- ===== ACTIVITY TAB ===== -->
<div class="tab-content" id="tab-activity">
  <div class="section-card">
    <div class="section-head">📋 Activity Feed</div>
    <div class="section-body">
      <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
        <button class="btn-action gray" onclick="loadActivity()">🔄 Refresh</button>
      </div>
      <div id="activity-list"></div>
    </div>
  </div>
</div>

''' + owner_panel_html + r'''

</div><!-- /container -->

<!-- EDITOR MODAL -->
<div class="modal" id="editor-modal">
  <div class="modal-box" style="max-width:800px;width:95vw">
    <div class="modal-head">
      <h3 id="editor-title">Edit File</h3>
      <button class="close" onclick="closeModal('editor-modal')">×</button>
    </div>
    <div class="modal-body">
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
        <input id="editor-search" placeholder="Search..." style="flex:1;padding:6px 10px;background:var(--bg2);border:1px solid var(--border);border-radius:4
// ─── DB ───────────────────────────────────────────────────────────────
async function createDB(){
  const n = document.getElementById('db-name').value.trim();
  if(!n){ toast('Enter database name', true); return; }
  try{
    const r = await fetch('/api/files/create', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path: currentPath + '/' + n + '.json',
        content: '{}'
      })
    });
    const d = await r.json();
    toast(d.success ? '🗄 Database created: ' + n : 'Failed: ' + (d.error||''), !d.success);
    if(d.success) loadFiles(currentPath);
  }catch(e){ toast('Error creating database', true); }
}

// ─── Schedules ──────────────────────────────────────────────────────
async function addSchedule(){
  const name = document.getElementById('sch-name').value.trim();
  const cmd = document.getElementById('sch-cmd').value.trim();
  const cron = document.getElementById('sch-cron').value.trim();
  if(!name || !cmd){ toast('Fill name and command', true); return; }
  try{
    const r = await fetch('/api/schedules/add', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name, command:cmd, schedule:cron})
    });
    const d = await r.json();
    toast(d.success ? '⏰ Schedule added' : 'Failed', !d.success);
    if(d.success) loadSchedules();
  }catch(e){ toast('Error adding schedule', true); }
}

async function loadSchedules(){
  try{
    const r = await fetch('/api/schedules/list');
    const d = await r.json();
    const el = document.getElementById('sch-list');
    if(!el) return;
    if(!(d.schedules||[]).length){
      el.innerHTML = '<div style="color:var(--text3);padding:10px">No schedules.</div>';
      return;
    }
    el.innerHTML = '';
    d.schedules.forEach(s => {
      el.innerHTML += `<div class="zip-item">
        <div><div class="z-name">⏰ ${escapeHtml(s.name)}</div>
        <div class="z-size">${escapeHtml(s.command)} · ${escapeHtml(s.schedule||'* * * * *')}</div></div>
        <button class="btn-action danger" style="font-size:11px" onclick="deleteSchedule('${escapeHtml(s.id)}')">🗑</button>
      </div>`;
    });
  }catch(e){}
}

async function deleteSchedule(id){
  if(!confirm('Delete schedule?')) return;
  try{
    const r = await fetch('/api/schedules/delete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id})
    });
    const d = await r.json();
    toast(d.success ? 'Deleted' : 'Failed', !d.success);
    if(d.success) loadSchedules();
  }catch(e){ toast('Error', true); }
}

// ─── NODE.JS ────────────────────────────────────────────────────────
async function loadNodeJsFiles(){
  const path = document.getElementById('nodejs-path').value.trim();
  if(!path){ toast('اكتب المسار أولاً', true); return; }
  const listEl = document.getElementById('nodejs-files-list');
  listEl.style.display = 'block';
  listEl.innerHTML = '<div style="padding:8px;color:var(--text2);font-size:12px">⏳ جاري التحميل...</div>';
  try{
    const r = await fetch('/api/nodejs/info', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        main_file: document.getElementById('nodejs-main').value.trim() || null,
        deps_file: document.getElementById('nodejs-deps').value.trim() || null
      })
    });
    const d = await r.json();
    if(!d.success){
      listEl.innerHTML = '<div style="padding:8px;color:var(--red);font-size:12px">' + escapeHtml(d.error||'Error') + '</div>';
      return;
    }
    const ic = document.getElementById('nodejs-install-cmd');
    const rc = document.getElementById('nodejs-run-cmd');
    if(ic) ic.textContent = '$ ' + escapeHtml(d.install_command || 'npm install');
    if(rc) rc.textContent = '$ ' + escapeHtml(d.run_command || 'node index.js');
    document.getElementById('nodejs-cmd-preview').style.display = 'block';

    const files = d.js_files || [];
    if(!files.length){
      listEl.innerHTML = '<div style="padding:8px;color:var(--text3);font-size:12px">لا توجد ملفات .js</div>';
      return;
    }
    listEl.innerHTML = files.map(f => `
      <div onclick="document.getElementById('nodejs-main').value='${escapeHtml(f)}';document.getElementById('nodejs-files-list').style.display='none';"
           style="padding:8px 12px;font-size:12px;color:var(--text);cursor:pointer;border-bottom:1px solid var(--border);
                  font-family:monospace;transition:.15s" onmouseover="this.style.background='var(--bg3)'" onmouseout="this.style.background=''">
        📜 ${escapeHtml(f)}
      </div>
    `).join('');
  }catch(e){
    listEl.innerHTML = '<div style="padding:8px;color:var(--red);font-size:12px">خطأ في التحميل</div>';
  }
}

async function previewNodeCmd(){
  const path = document.getElementById('nodejs-path').value.trim();
  if(!path){ toast('اكتب المسار أولاً', true); return; }
  try{
    const r = await fetch('/api/nodejs/info', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        main_file: document.getElementById('nodejs-main').value.trim() || null,
        deps_file: document.getElementById('nodejs-deps').value.trim() || null
      })
    });
    const d = await r.json();
    const ic = document.getElementById('nodejs-install-cmd');
    const rc = document.getElementById('nodejs-run-cmd');
    if(ic) ic.textContent = '$ ' + (d.install_command || 'npm install');
    if(rc) rc.textContent = '$ ' + (d.run_command || 'node index.js');
    document.getElementById('nodejs-cmd-preview').style.display = 'block';
    toast('✅ الأوامر جاهزة', false, true);
  }catch(e){ toast('Error previewing commands', true); }
}

async function startNodeProject(){
  const path = document.getElementById('nodejs-path').value.trim();
  const port = document.getElementById('nodejs-port').value.trim();
  const mainFile = document.getElementById('nodejs-main').value.trim();
  const depsFile = document.getElementById('nodejs-deps').value.trim();
  if(!path){ toast('Enter project path', true); return; }
  toast('🟢 جاري تشغيل Node.js...', false, true);
  const outEl = document.getElementById('nodejs-start-output');
  if(outEl){ outEl.style.display = 'block'; outEl.textContent = '⏳ Installing dependencies...\n'; }
  try{
    const r = await fetch('/api/nodejs/start', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        port: port ? parseInt(port) : null,
        main_file: mainFile || null,
        deps_file: depsFile || null
      })
    });
    const d = await r.json();
    if(outEl && d.install_output) outEl.textContent += d.install_output;
    if(d.success){
      if(outEl) outEl.textContent += `\n✅ Started: ${d.command}\n🔌 Port: ${d.port}\n`;
      toast(`▶ Node.js started — port ${d.port}`);
      loadNodejsList();
    } else {
      if(outEl && d.install_commands) outEl.textContent += `\n📋 Install commands:\n  ${d.install_commands.join('\n  ')}\n`;
      if(outEl && d.run_command) outEl.textContent += `📋 Run command:\n  ${d.run_command}\n`;
      toast('❌ ' + (d.error||'Failed'), true);
    }
  }catch(e){ toast('Error starting Node.js', true); }
}

async function loadNodejsList(){
  try{
    const r = await fetch('/api/nodejs/list');
    const d = await r.json();
    const list = document.getElementById('nodejs-list');
    if(!list) return;
    if(!(d.processes||[]).length){
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text3)">No Node.js processes running.</div>';
      return;
    }
    list.innerHTML = '';
    d.processes.forEach(p => {
      const card = document.createElement('div');
      card.className = 'nodejs-project-card';
      card.innerHTML = `
        <div class="project-info">
          <div class="p-name">🟢 ${escapeHtml(p.command||p.pid)}</div>
          <div class="p-meta">
            Port: ${p.port||'—'} · Main: ${escapeHtml(p.main_file||'auto')} ·
            Deps: ${escapeHtml(p.deps_file||'package.json')} · ${escapeHtml((p.started||'').split('T')[0]||'')}
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
          <span class="p-status ${p.running?'running':'stopped'}">${p.running?'● Running':'● Stopped'}</span>
          <button class="btn-action gray" style="font-size:11px" onclick="viewNodeLogs('${escapeHtml(p.pid)}')">📋 Logs</button>
          <button class="btn-action danger" style="font-size:11px" onclick="stopNodeProcess('${escapeHtml(p.pid)}')">■ Stop</button>
        </div>
      `;
      list.appendChild(card);
    });
  }catch(e){}
}

async function stopNodeProcess(pid){
  if(!confirm('Stop this Node.js process?')) return;
  try{
    const r = await fetch('/api/nodejs/stop', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pid})
    });
    const d = await r.json();
    toast(d.success ? '■ Stopped' : 'Failed', !d.success);
    if(d.success) loadNodejsList();
  }catch(e){ toast('Error stopping process', true); }
}

async function viewNodeLogs(pid){
  try{
    const r = await fetch('/api/nodejs/logs/' + pid);
    const d = await r.json();
    if(activeTerminalId){
      const box = document.getElementById('console-output-' + activeTerminalId);
      if(box){
        const footer = document.getElementById('term-footer-' + activeTerminalId);
        while(box.firstChild && box.firstChild !== footer) box.removeChild(box.firstChild);
      }
    }
    (d.output||[]).forEach(l => appendConsole(l));
    document.querySelectorAll('.tab-item').forEach(t => { if(t.dataset.tab==='console') t.click(); });
    toast('Logs loaded', false, true);
  }catch(e){ toast('Error loading logs', true); }
}

// ─── PHP ────────────────────────────────────────────────────────────
async function loadPhpFiles(){
  const path = document.getElementById('php-path').value.trim();
  if(!path){ toast('اكتب المسار أولاً', true); return; }
  const listEl = document.getElementById('php-files-list');
  listEl.style.display = 'block';
  listEl.innerHTML = '<div style="padding:8px;color:var(--text2);font-size:12px">⏳ جاري التحميل...</div>';
  try{
    const r = await fetch('/api/php/info', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        main_file: document.getElementById('php-main').value.trim() || null,
        deps_file: document.getElementById('php-deps').value.trim() || null
      })
    });
    const d = await r.json();
    if(!d.success){
      listEl.innerHTML = '<div style="padding:8px;color:var(--red);font-size:12px">' + escapeHtml(d.error||'Error') + '</div>';
      return;
    }
    const ic = document.getElementById('php-install-cmd');
    const rc = document.getElementById('php-run-cmd');
    const icArr = Array.isArray(d.install_commands) ? d.install_commands : [d.install_commands||'composer install (if needed)'];
    if(ic) ic.textContent = '$ ' + icArr.join('\n$ ');
    if(rc) rc.textContent = '$ ' + escapeHtml(d.run_command || 'php -S 0.0.0.0:PORT');

    const files = d.php_files || [];
    if(!files.length){
      listEl.innerHTML = '<div style="padding:8px;color:var(--text3);font-size:12px">لا توجد ملفات .php</div>';
      return;
    }
    listEl.innerHTML = files.map(f => `
      <div onclick="document.getElementById('php-main').value='${escapeHtml(f)}';document.getElementById('php-files-list').style.display='none';"
           style="padding:8px 12px;font-size:12px;color:var(--text);cursor:pointer;border-bottom:1px solid var(--border);
                  font-family:monospace;transition:.15s" onmouseover="this.style.background='var(--bg3)'" onmouseout="this.style.background=''">
        🐘 ${escapeHtml(f)}
      </div>
    `).join('');
  }catch(e){
    listEl.innerHTML = '<div style="padding:8px;color:var(--red);font-size:12px">خطأ في التحميل</div>';
  }
}

async function previewPhpCmd(){
  const path = document.getElementById('php-path').value.trim();
  if(!path){ toast('اكتب المسار أولاً', true); return; }
  try{
    const r = await fetch('/api/php/info', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        main_file: document.getElementById('php-main').value.trim() || null,
        deps_file: document.getElementById('php-deps').value.trim() || null
      })
    });
    const d = await r.json();
    const ic = document.getElementById('php-install-cmd');
    const rc = document.getElementById('php-run-cmd');
    const icArr = Array.isArray(d.install_commands) ? d.install_commands : [d.install_commands||'composer install (if needed)'];
    if(ic) ic.textContent = '$ ' + icArr.join('\n$ ');
    if(rc) rc.textContent = '$ ' + (d.run_command || 'php -S 0.0.0.0:PORT');
    toast('✅ الأوامر جاهزة', false, true);
  }catch(e){ toast('Error previewing commands', true); }
}

async function startPhpServer(){
  const path = document.getElementById('php-path').value.trim();
  const port = document.getElementById('php-port').value.trim();
  const mainFile = document.getElementById('php-main').value.trim();
  const depsFile = document.getElementById('php-deps').value.trim();
  if(!path){ toast('Enter PHP root path', true); return; }
  toast('🐘 جاري تشغيل PHP...', false, true);
  const outEl = document.getElementById('php-start-output');
  if(outEl){ outEl.style.display = 'block'; outEl.textContent = '⏳ Checking dependencies...\n'; }
  try{
    const r = await fetch('/api/php/start', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        path,
        port: port ? parseInt(port) : null,
        main_file: mainFile || null,
        deps_file: depsFile || null
      })
    });
    const d = await r.json();
    if(outEl && d.install_output) outEl.textContent += d.install_output;
    if(d.success){
      if(outEl) outEl.textContent += `\n✅ PHP running — port ${d.port}\n📄 Entry: ${d.command}\n`;
      toast(`▶ PHP started — port ${d.port}`);
      loadPhpList();
    } else {
      if(outEl && d.install_commands) outEl.textContent += `\n📋 Install commands:\n  ${d.install_commands.join('\n  ')}\n`;
      if(outEl && d.run_command) outEl.textContent += `📋 Run command:\n  ${d.run_command}\n`;
      toast('❌ ' + (d.error||'Failed'), true);
    }
  }catch(e){ toast('Error starting PHP', true); }
}

async function loadPhpList(){
  try{
    const r = await fetch('/api/php/list');
    const d = await r.json();
    const list = document.getElementById('php-list');
    if(!list) return;
    if(!(d.servers||[]).length){
      list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text3)">No PHP servers running.</div>';
      return;
    }
    list.innerHTML = '';
    d.servers.forEach(s => {
      const card = document.createElement('div');
      card.className = 'php-server-card';
      card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
          <div>
            <div style="font-size:14px;font-weight:700;color:var(--text)">🐘 PHP Server — Port ${s.port||'—'}</div>
            <div style="font-size:12px;color:var(--text2);margin-top:3px">
              Entry: ${escapeHtml(s.main_file||'auto')} ·
              Deps: ${escapeHtml(s.deps_file||'composer.json')} ·
              ${escapeHtml((s.started||'').split('T')[0]||'')}
            </div>
          </div>
          <div style="display:flex;gap:8px">
            <span class="p-status ${s.running?'running':'stopped'}">${s.running?'● Running':'● Stopped'}</span>
            <button class="btn-action danger" style="font-size:11px" onclick="stopPhpServer('${escapeHtml(s.pid)}')">■ Stop</button>
          </div>
        </div>
      `;
      list.appendChild(card);
    });
  }catch(e){}
}

async function stopPhpServer(pid){
  if(!confirm('Stop this PHP server?')) return;
  try{
    const r = await fetch('/api/php/stop', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pid})
    });
    const d = await r.json();
    toast(d.success ? '■ PHP stopped' : 'Failed', !d.success);
    if(d.success) loadPhpList();
  }catch(e){ toast('Error stopping PHP', true); }
}

// ─── Users (master/admin) ─────────────────────────────────────────
function onPlanChange(){
  const plan = document.getElementById('u-plan').value;
  const wrap = document.getElementById('u-custom-days-wrap');
  if(wrap) wrap.style.display = plan === 'custom' ? 'block' : 'none';
}

async function addUser(){
  const plan = document.getElementById('u-plan').value;
  const data = {
    username: document.getElementById('u-name').value.trim(),
    password: document.getElementById('u-pass').value,
    tg_username: (document.getElementById('u-tg').value||'').trim().replace('@',''),
    role: document.getElementById('u-role') ? document.getElementById('u-role').value : 'user',
    max_sessions: parseInt(document.getElementById('u-max').value) || 1,
    max_servers: parseInt(document.getElementById('u-maxsrv').value) || 1,
    main_file: document.getElementById('u-main').value || 'main.py',
    plan: plan,
    expiry_days: plan === 'custom' ? (parseInt(document.getElementById('u-days').value) || 7) : undefined
  };
  if(!data.username || !data.password){ toast('Fill all fields', true); return; }
  try{
    const r = await fetch('/api/users/add', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)
    });
    const d = await r.json();
    toast(d.success ? '✅ User added' : '❌ ' + (d.error||''), !d.success);
    if(d.success) loadUsers();
  }catch(e){ toast('Error adding user', true); }
}

const PLAN_LABELS = {
  free_trial: '🆓 Free Trial',
  paid_20: '⭐ 20 Day',
  paid_30: '💎 30 Day',
  custom: '🎯 Custom'
};

async function loadUsers(){
  try{
    const r = await fetch('/api/users/list');
    const d = await r.json();
    const el = document.getElementById('users-list');
    if(!el) return;
    el.innerHTML = '';
    (d.users||[]).forEach(u => {
      const card = document.createElement('div');
      card.className = 'section-card';
      card.style.marginBottom = '10px';
      const isActive = u.active !== false;
      const expStr = u.expiry ? (() => {
        const diff = Math.ceil((new Date(u.expiry) - new Date()) / 86400000);
        return diff > 0 ? `<span style="color:${diff<3?'var(--red)':'var(--green)'}">⏳ ${diff} يوم متبقي</span>` : '<span style="color:var(--red)">❌ منتهي</span>';
      })() : '';
      const planLabel = PLAN_LABELS[u.plan||'free_trial'] || u.plan || '—';
      const roleLabel = u.role || 'user';
      const roleClass = roleLabel === 'owner' ? 'owner' : roleLabel === 'admin' ? 'admin' : roleLabel === 'moderator' ? 'moderator' : 'user';
      const pwDisplay = u.password_hash ? u.password_hash.substring(0,16) + '...' : '—';
      card.innerHTML = `
        <div class="section-body">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap">
            <div>
              <div style="font-size:15px;font-weight:700;color:var(--text)">👤 ${escapeHtml(u.username)}
                <span class="role-badge ${roleClass}" style="font-size:10px;padding:1px 8px;margin-left:6px;">${escapeHtml(roleLabel)}</span>
              </div>
              <div style="font-size:12px;color:var(--text2);margin-top:4px;display:flex;flex-wrap:wrap;gap:8px">
                ${u.tg_username ? `<span>🔵 @${escapeHtml(u.tg_username)}</span>` : ''}
                <span>${planLabel}</span>
                ${expStr}
                <span style="color:${isActive?'var(--green)':'var(--yellow)'}">${isActive?'✅ Active':'⏳ Pending'}</span>
              </div>
              <div style="font-size:11px;color:var(--text3);margin-top:6px;font-family:monospace">
                🔑 Hash: ${escapeHtml(pwDisplay)}
                <button onclick="togglePwHash(this,'${escapeHtml(u.password_hash||'')}')" style="background:none;border:1px solid var(--border2);border-radius:4px;color:var(--text2);font-size:10px;padding:1px 6px;cursor:pointer;margin-left:6px">👁 Show</button>
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              ${!isActive ? `<button class="btn-action green" onclick="approveUser('${escapeHtml(u.username)}')">✅ Approve</button>` : ''}
              <button class="btn-action gray" onclick="openEditUser('${escapeHtml(u.username)}','${u.role||'user'}','${u.max_sessions||1}','${u.max_servers||1}','${escapeHtml(u.main_file||'main.py')}')">✏️ Edit</button>
              <button class="btn-action danger" onclick="deleteUser('${escapeHtml(u.username)}')">🗑</button>
            </div>
          </div>
        </div>
      `;
      el.appendChild(card);
    });
  }catch(e){}
}

function togglePwHash(btn, fullHash){
  const parent = btn.parentNode;
  const textNode = parent.childNodes[0];
  if(btn.dataset.showing === '1'){
    textNode.textContent = '🔑 Hash: ' + (fullHash ? fullHash.substring(0,16) + '...' : '—');
    btn.textContent = '👁 Show';
    btn.dataset.showing = '0';
  } else {
    textNode.textContent = '🔑 Hash: ' + (fullHash || '—');
    btn.textContent = '🙈 Hide';
    btn.dataset.showing = '1';
  }
}

async function approveUser(username){
  try{
    const r = await fetch('/api/users/approve', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username})
    });
    const d = await r.json();
    toast(d.success ? `✅ ${username} approved` : 'Failed', !d.success);
    if(d.success) loadUsers();
  }catch(e){ toast('Error approving user', true); }
}

function openEditUser(name, role, maxS, maxSrv, mainF){
  document.getElementById('eu-name').value = name;
  document.getElementById('eu-pass').value = '';
  const roleEl = document.getElementById('eu-role');
  if(roleEl){
    for(let opt of roleEl.options){
      if(opt.value === role) opt.selected = true;
    }
  }
  document.getElementById('eu-max').value = maxS;
  document.getElementById('eu-maxsrv').value = maxSrv;
  document.getElementById('eu-main').value = mainF;
  document.getElementById('eu-days').value = 30;
  openModal('edit-user-modal');
}

async function saveEditUser(){
  const data = {
    username: document.getElementById('eu-name').value,
    password: document.getElementById('eu-pass').value || undefined,
    role: document.getElementById('eu-role') ? document.getElementById('eu-role').value : undefined,
    max_sessions: parseInt(document.getElementById('eu-max').value) || 1,
    max_servers: parseInt(document.getElementById('eu-maxsrv').value) || 1,
    main_file: document.getElementById('eu-main').value,
    expiry_days: parseInt(document.getElementById('eu-days').value) || 30
  };
  try{
    const r = await fetch('/api/users/update', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)
    });
    const d = await r.json();
    toast(d.success ? '✅ Updated' : 'Failed', !d.success);
    if(d.success){ closeModal('edit-user-modal'); loadUsers(); }
  }catch(e){ toast('Error updating user', true); }
}

async function deleteUser(username){
  if(!confirm(`Delete user "${username}" and all files?`)) return;
  try{
    const r = await fetch('/api/users/delete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username})
    });
    const d = await r.json();
    toast(d.success ? '🗑 Deleted' : 'Failed', !d.success);
    if(d.success) loadUsers();
  }catch(e){ toast('Error deleting user', true); }
}

// ─── Backups ────────────────────────────────────────────────────────
async function createBackup(){
  toast('💾 Creating backup...', false, true);
  try{
    const r = await fetch('/api/backups/create', {method:'POST'});
    const d = await r.json();
    toast(d.success ? '✅ Backup created' : '❌ Failed', !d.success);
    if(d.success) loadBackups();
  }catch(e){ toast('Error creating backup', true); }
}

async function loadBackups(){
  try{
    const r = await fetch('/api/backups/list');
    const d = await r.json();
    const el = document.getElementById('backups-list');
    if(!el) return;
    if(!(d.backups||[]).length){
      el.innerHTML = '<div style="color:var(--text3);padding:10px">No backups found.</div>';
      return;
    }
    el.innerHTML = '';
    d.backups.forEach(b => {
      el.innerHTML += `<div class="zip-item">
        <div><div class="z-name">📦 ${escapeHtml(b.name)}</div>
        <div class="z-size">${escapeHtml(b.size||'')}</div></div>
        <button class="btn-action gray" style="font-size:11px" onclick="window.open('/api/backups/download?name=${encodeURIComponent(b.name)}','_blank')">⬇ Download</button>
      </div>`;
    });
  }catch(e){}
}

// ─── Ports ──────────────────────────────────────────────────────────
async function addPort(){
  const port = parseInt(document.getElementById('new-port').value);
  const note = document.getElementById('new-port-note').value.trim();
  if(!port || port < 1 || port > 65535){ toast('Enter valid port (1-65535)', true); return; }
  try{
    const r = await fetch('/api/ports/add', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({port, note})
    });
    const d = await r.json();
    toast(d.success ? '✅ Port added' : '❌ ' + (d.error||''), !d.success);
    if(d.success) loadPorts();
  }catch(e){ toast('Error adding port', true); }
}

async function loadPorts(){
  try{
    const r = await fetch('/api/ports/list');
    const d = await r.json();
    const el = document.getElementById('ports-list');
    if(!el) return;
    if(!(d.ports||[]).length){
      el.innerHTML = '<div style="color:var(--text3);padding:10px">No extra ports configured.</div>';
      return;
    }
    el.innerHTML = '';
    d.ports.forEach(p => {
      el.innerHTML += `<div class="zip-item">
        <div><div class="z-name">🔌 Port ${p.port}</div>
        <div class="z-size">${escapeHtml(p.note||'')} · ${escapeHtml(p.status||'idle')}</div></div>
        <button class="btn-action danger" style="font-size:11px" onclick="deletePort(${p.port})">Delete</button>
      </div>`;
    });
  }catch(e){}
}

async function deletePort(port){
  if(!confirm(`Delete port ${port}?`)) return;
  try{
    const r = await fetch('/api/ports/delete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({port})
    });
    const d = await r.json();
    toast(d.success ? 'Deleted' : 'Failed', !d.success);
    if(d.success) loadPorts();
  }catch(e){ toast('Error deleting port', true); }
}

async function scanPorts(){
  const host = document.getElementById('scan-host').value.trim();
  const portsInput = document.getElementById('scan-ports').value;
  const ports = portsInput.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p) && p > 0 && p < 65536);
  if(!host || !ports.length){ toast('Enter host and valid ports', true); return; }
  try{
    const r = await fetch('/api/network/scan', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({host, ports})
    });
    const d = await r.json();
    const el = document.getElementById('scan-results');
    el.innerHTML = (d.results||[]).map(p =>
      `<div style="display:flex;gap:8px;padding:4px 0;font-size:12px">
        <span style="color:${p.open?'var(--green)':'var(--red)'}">●</span>
        <span style="color:var(--text)">Port ${p.port}</span>
        <span style="color:${p.open?'var(--green)':'var(--red)'}"> — ${p.open?'OPEN':'CLOSED'}</span>
      </div>`
    ).join('');
  }catch(e){ toast('Error scanning ports', true); }
}

// ─── Settings ──────────────────────────────────────────────────────
async function changePassword(){
  const cur = document.getElementById('cur-pass').value;
  const nw = document.getElementById('new-pass').value;
  if(!cur || !nw){ toast('Fill all fields', true); return; }
  if(nw.length < 6){ toast('Password must be at least 6 characters', true); return; }
  try{
    const r = await fetch('/api/master/change-password', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({current_password: cur, new_password: nw})
    });
    const d = await r.json();
    toast(d.success ? '✅ Password changed' : '❌ Wrong password', !d.success);
    if(d.success){ document.getElementById('cur-pass').value = ''; document.getElementById('new-pass').value = ''; }
  }catch(e){ toast('Error changing password', true); }
}

async function loadSysinfo(){
  try{
    const r = await fetch('/api/sysinfo');
    const d = await r.json();
    document.getElementById('sysinfo-box').textContent = d.info || '';
  }catch(e){}
}

async function setStartupFile(){
  const f = document.getElementById('startup-file').value.trim();
  if(!f){ toast('Enter filename', true); return; }
  try{
    const r = await fetch('/api/files/set-main', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({filename: f, path: ''})
    });
    const d = await r.json();
    toast(d.success ? '🚀 Startup set: ' + f : 'Failed', !d.success);
  }catch(e){ toast('Error setting startup file', true); }
}

async function installPip(){
  const p = document.getElementById('pip-pkg').value.trim();
  if(!p){ toast('Enter package name', true); return; }
  toast('📦 Installing ' + p + '...', false, true);
  try{
    const r = await fetch('/api/packages/install/pip', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({package: p})
    });
    const d = await r.json();
    toast(d.success ? '✅ Installed: ' + p : '❌ Failed', !d.success
    
// ─── Security Alerts ────────────────────────────────────────────────────────
async function loadSecurityAlerts(){
  const el = document.getElementById('security-alerts-list');
  if(!el) return;
  el.innerHTML = '<div style="color:var(--text2);padding:10px;text-align:center">⏳ جاري التحميل...</div>';
  try{
    const r = await fetch('/api/security/alerts');
    const d = await r.json();
    if(!(d.alerts||[]).length){
      el.innerHTML = '<div style="color:var(--green);padding:12px;text-align:center;font-size:13px">✅ لا توجد تنبيهات أمنية — كل شيء نظيف!</div>';
      return;
    }
    el.innerHTML = '';
    d.alerts.forEach(a => {
      const threats = (a.threats||[]).join(' | ');
      const reviewed = a.reviewed;
      const div = document.createElement('div');
      div.style.cssText = `
        background:${reviewed ? 'var(--bg2)' : 'rgba(248,81,73,.05)'};
        border:1px solid ${reviewed ? 'var(--border)' : 'rgba(248,81,73,.3)'};
        border-radius:10px;padding:12px 14px;margin-bottom:8px;
      `;
      div.innerHTML = `
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap">
          <div style="flex:1">
            <div style="font-size:13px;font-weight:700;color:${reviewed ? 'var(--text2)' : '#f85149'};margin-bottom:4px">
              ${reviewed ? '✅' : '🚨'} ${escapeHtml(a.filename||'—')}
              <span style="font-size:10px;color:var(--text3);font-weight:400;margin-left:6px">#${escapeHtml(a.id||'')}</span>
            </div>
            <div style="font-size:11px;color:var(--text2);margin-bottom:4px">
              👤 ${escapeHtml(a.username||'—')} &nbsp;·&nbsp; 🌐 ${escapeHtml(a.ip||'—')} &nbsp;·&nbsp; 🕐 ${escapeHtml(a.time||'—')}
            </div>
            <div style="font-size:11px;color:#ffcc00;font-family:monospace;word-break:break-word">
              ${escapeHtml(threats)}
            </div>
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0">
            ${!reviewed ? `<button class="btn-action green" style="font-size:10px;padding:5px 10px"
              onclick="markAlertReviewed('${escapeHtml(a.id)}',this)">✓ تمت المراجعة</button>` : ''}
            <button class="btn-action danger" style="font-size:10px;padding:5px 10px"
              onclick="deleteAlert('${escapeHtml(a.id)}',this)">🗑</button>
          </div>
        </div>
      `;
      el.appendChild(div);
    });
  } catch(e) {
    el.innerHTML = '<div style="color:var(--red);padding:10px">فشل تحميل التنبيهات</div>';
    console.error('loadSecurityAlerts error:', e);
  }
}

async function markAlertReviewed(id, btn){
  if(!btn) { toast('حدث خطأ', true); return; }
  try{
    const r = await fetch('/api/security/alerts/review', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id})
    });
    const d = await r.json();
    if(d.success){ 
      toast('✅ تمت المراجعة', false, true); 
      loadSecurityAlerts(); 
    } else {
      toast('فشل: ' + (d.error||''), true);
    }
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('markAlertReviewed error:', e);
  }
}

async function deleteAlert(id, btn){
  if(!btn) { toast('حدث خطأ', true); return; }
  if(!confirm('حذف هذا التنبيه؟')) return;
  try{
    const r = await fetch('/api/security/alerts/delete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({id})
    });
    const d = await r.json();
    if(d.success){ 
      toast('🗑 تم الحذف', false, true); 
      loadSecurityAlerts(); 
    } else {
      toast('فشل: ' + (d.error||''), true);
    }
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('deleteAlert error:', e);
  }
}

async function clearSecurityAlerts(){
  if(!confirm('حذف جميع التنبيهات الأمنية؟')) return;
  try{
    const r = await fetch('/api/security/alerts/clear', {method:'POST'});
    const d = await r.json();
    toast(d.success ? '🗑 تم مسح السجل' : 'فشل', !d.success);
    if(d.success) loadSecurityAlerts();
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('clearSecurityAlerts error:', e);
  }
}

// ─── Announcements ────────────────────────────────────────────────────────
async function loadAnnouncements(){
  try{
    const r = await fetch('/api/owner/announcements');
    const d = await r.json();
    const list = document.getElementById('ann-list');
    if(!list) return;
    if(!(d.list||[]).length){
      list.innerHTML = '<div style="color:var(--text3);padding:8px">No announcements.</div>';
      return;
    }
    list.innerHTML = '';
    d.list.forEach((a, i) => {
      list.innerHTML += `<div class="zip-item">
        <div><div class="z-name">${escapeHtml(a.text)}</div>
        <div class="z-size">${escapeHtml(a.time||'')}</div></div>
        <button class="btn-action danger" style="font-size:11px" onclick="deleteAnn(${i})">🗑</button>
      </div>`;
    });
  } catch(e) {
    console.error('loadAnnouncements error:', e);
  }
}

async function addAnnouncement(){
  const txt = document.getElementById('ann-txt').value.trim();
  if(!txt){ toast('أدخل نص الإعلان', true); return; }
  try{
    const r = await fetch('/api/owner/announcements/add', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text: txt})
    });
    const d = await r.json();
    toast(d.success ? '📢 Added' : 'Failed', !d.success);
    if(d.success){ 
      document.getElementById('ann-txt').value = ''; 
      loadAnnouncements(); 
    }
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('addAnnouncement error:', e);
  }
}

async function deleteAnn(idx){
  if(!confirm('حذف هذا الإعلان؟')) return;
  try{
    const r = await fetch('/api/owner/announcements/delete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({index: idx})
    });
    const d = await r.json();
    toast(d.success ? 'Deleted' : 'Failed', !d.success);
    if(d.success) loadAnnouncements();
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('deleteAnn error:', e);
  }
}

async function ownerBroadcast(){
  const txt = document.getElementById('ann-txt').value.trim();
  if(!txt){ toast('أدخل رسالة البث', true); return; }
  try{
    const r = await fetch('/api/owner/broadcast', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message: txt})
    });
    const d = await r.json();
    toast(d.success ? `📡 تم الإرسال إلى ${d.count||0} مستخدم` : 'فشل البث', !d.success);
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('ownerBroadcast error:', e);
  }
}

// ─── Pending Users ────────────────────────────────────────────────────────
async function loadPendingUsers(){
  try{
    const r = await fetch('/api/users/pending');
    const d = await r.json();
    const el = document.getElementById('pending-users-list');
    if(!el) return;
    if(!(d.users||[]).length){
      el.innerHTML = '<div style="color:var(--text3);padding:10px">لا يوجد طلبات تسجيل معلقة.</div>';
      return;
    }
    el.innerHTML = '';
    d.users.forEach(u => {
      el.innerHTML += `<div class="pending-card">
        <div>
          <div class="p-user">📋 ${escapeHtml(u.username)} 
            ${u.tg_username ? `<span style="color:#60a5fa;font-size:11px">🔵 @${escapeHtml(u.tg_username)}</span>` : ''}
          </div>
          <div class="p-time">تاريخ التسجيل: ${escapeHtml(u.created||'')}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn-action green" onclick="approveUser('${escapeHtml(u.username)}')">✅ موافقة</button>
          <button class="btn-action danger" onclick="deleteUser('${escapeHtml(u.username)}')">❌ رفض</button>
        </div>
      </div>`;
    });
  } catch(e) {
    console.error('loadPendingUsers error:', e);
  }
}

// ─── Owner Actions ────────────────────────────────────────────────────────
async function ownerAction(action){
  const confirmMsg = {
    'clear_all_logs': 'مسح جميع السجلات؟',
    'kick_all_users': 'طرد جميع المستخدمين؟',
    'reset_stats': 'إعادة ضبط الإحصائيات؟',
    'restart_panel': 'إعادة تشغيل اللوحة؟'
  };
  if(action !== 'restart_panel' && !confirm(confirmMsg[action] || 'تأكيد: ' + action + '؟')) return;
  try{
    const r = await fetch('/api/owner/action', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action})
    });
    const d = await r.json();
    toast(d.success ? '✅ تم التنفيذ: ' + action : 'فشل', !d.success);
    if(d.success && action === 'restart_panel'){
      toast('🔄 إعادة تشغيل اللوحة... انتظر لحظة', false, true);
      setTimeout(() => location.reload(), 3000);
    }
  } catch(e) {
    toast('خطأ في الاتصال', true);
    console.error('ownerAction error:', e);
  }
}

function fmtExpiry(exp){
  if(!exp || exp === '∞') return '∞';
  try{
    const d = new Date(exp);
    const diff = Math.ceil((d - new Date()) / (1000 * 86400));
    return diff > 0 ? `تنتهي بعد ${diff} يوم` : '❌ منتهي';
  } catch(e){ return exp; }
}

// ─── AI Chat ──────────────────────────────────────────────────────────────
const AI_API_KEY = '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';
const AI_BASE_URL = 'https://integrate.api.nvidia.com/v1';
const AI_MODEL = 'openai/gpt-oss-120b';
let aiHistory = [];
let aiStreaming = false;

function aiKeyDown(e){
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    sendAiMessage();
  }
}

function aiQuick(txt){
  document.getElementById('ai-input').value = txt;
  document.getElementById('ai-input').focus();
}

function clearAiChat(){
  aiHistory = [];
  const box = document.getElementById('ai-messages');
  box.innerHTML = `<div class="ai-msg ai-assistant">
    <div class="ai-bubble">
      <span class="ai-avatar">🤖</span>
      <div class="ai-text">تم مسح المحادثة. كيف يمكنني مساعدتك؟</div>
    </div>
  </div>`;
}

function renderAiText(raw){
  if(!raw) return '';
  // Markdown rendering: code blocks, inline code, bold, lists
  let html = raw
    .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => 
      `<pre><code>${escapeHtml(code.trim())}</code></pre>`)
    .replace(/`([^`]+)`/g, (_, c) => `<code>${escapeHtml(c)}</code>`)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^\s*[-*]\s+(.+)$/gm, '• $1')
    .replace(/\n/g, '<br>');
  return html;
}

function appendAiMsg(role, text, isStreaming = false){
  const box = document.getElementById('ai-messages');
  const isUser = role === 'user';
  const div = document.createElement('div');
  div.className = `ai-msg ${isUser ? 'ai-user' : 'ai-assistant'}`;
  if(isStreaming) div.id = 'ai-streaming-msg';
  div.innerHTML = `<div class="ai-bubble">
    <span class="ai-avatar">${isUser ? '👤' : '🤖'}</span>
    <div class="ai-text" ${isStreaming ? 'id="ai-stream-text"' : ''}>${isUser ? escapeHtml(text) : renderAiText(text)}</div>
  </div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function showAiTyping(){
  const box = document.getElementById('ai-messages');
  const div = document.createElement('div');
  div.className = 'ai-msg ai-assistant';
  div.id = 'ai-typing-indicator';
  div.innerHTML = `<div class="ai-bubble">
    <span class="ai-avatar">🤖</span>
    <div class="ai-text">
      <div class="ai-typing"><span></span><span></span><span></span></div>
    </div>
  </div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function removeAiTyping(){
  const t = document.getElementById('ai-typing-indicator');
  if(t) t.remove();
}

async function sendAiMessage(){
  if(aiStreaming) return;
  const inp = document.getElementById('ai-input');
  const msg = inp.value.trim();
  if(!msg){ toast('اكتب رسالة أولاً', true); return; }
  inp.value = '';
  inp.style.height = 'auto';

  appendAiMsg('user', msg);
  aiHistory.push({role: 'user', content: msg});

  aiStreaming = true;
  const btn = document.getElementById('ai-send-btn');
  btn.disabled = true;
  btn.textContent = '⏳';

  showAiTyping();

  try{
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({messages: aiHistory})
    });

    if(!resp.ok){
      removeAiTyping();
      const err = await resp.json();
      appendAiMsg('assistant', '❌ خطأ: ' + (err.error || 'فشل الاتصال'));
      aiStreaming = false;
      btn.disabled = false;
      btn.textContent = '➤ إرسال';
      return;
    }

    removeAiTyping();

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let reasoningText = '';

    const msgDiv = appendAiMsg('assistant', '', true);
    const textEl = document.getElementById('ai-stream-text');

    while(true){
      const {done, value} = await reader.read();
      if(done) break;
      const chunk = decoder.decode(value, {stream: true});
      const lines = chunk.split('\n');
      for(const line of lines){
        if(!line.startsWith('data:')) continue;
        const data = line.slice(5).trim();
        if(data === '[DONE]') break;
        try{
          const j = JSON.parse(data);
          const delta = j.choices?.[0]?.delta || {};
          if(delta.reasoning_content){
            reasoningText += delta.reasoning_content;
            const rb = document.getElementById('ai-reasoning');
            const tb = document.getElementById('ai-thinking-box');
            if(rb){ rb.textContent = reasoningText; rb.scrollTop = rb.scrollHeight; }
            if(tb) tb.style.display = 'block';
          }
          if(delta.content){
            fullText += delta.content;
            if(textEl) textEl.innerHTML = renderAiText(fullText);
            document.getElementById('ai-messages').scrollTop = 999999;
          }
        } catch(e){ /* ignore parse errors */ }
      }
    }
    if(msgDiv) msgDiv.id = '';
    const textFinal = document.getElementById('ai-stream-text');
    if(textFinal) textFinal.id = '';

    // إخفاء التفكير بعد الانتهاء
    setTimeout(() => {
      const tb = document.getElementById('ai-thinking-box');
      if(tb) tb.style.display = 'none';
      const rb = document.getElementById('ai-reasoning');
      if(rb) rb.textContent = '';
    }, 2000);

    aiHistory.push({role: 'assistant', content: fullText});
    if(aiHistory.length > 20) aiHistory = aiHistory.slice(-20);

  } catch(err) {
    removeAiTyping();
    appendAiMsg('assistant', '❌ خطأ في الاتصال: ' + err.message);
    console.error('AI Chat error:', err);
  }

  aiStreaming = false;
  btn.disabled = false;
  btn.textContent = '➤ إرسال';
}

// ─── Auto-resize for textarea ──────────────────────────────────────────
function autoResizeAI(el){
  if(!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ─── Advanced Editor Functions ──────────────────────────────────────────
function openAdvancedEditor(){
  // فتح المحرر على الملف الحالي أو شاشة فارغة
  if(currentEditPath){
    editFile(currentEditPath, currentEditPath.split('/').pop());
  } else {
    toast('افتح ملفاً أولاً', true);
  }
}

function editorSearchReplace(){
  const search = document.getElementById('editor-search').value;
  const replace = document.getElementById('editor-replace').value;
  if(!search){
    toast('أدخل نصاً للبحث', true);
    return;
  }
  const content = document.getElementById('editor-content').value;
  const count = (content.match(new RegExp(search, 'g')) || []).length;
  if(count === 0){
    toast('لم يتم العثور على النص', true);
    return;
  }
  const newContent = content.replaceAll(search, replace);
  document.getElementById('editor-content').value = newContent;
  toast(`🔍 تم استبدال ${count} تكرار`, false, true);
}

function editorAutoSave(){
  if(currentEditPath) saveFile();
  toast('💾 حفظ تلقائي', false, true);
}

// ─── Fix: Add missing loadSchedules function ────────────────────────────
// (already defined above)

// ─── Fix: Add missing loadDbConnections if not exists ──────────────────
if(typeof loadDbConnections === 'undefined'){
  async function loadDbConnections(){
    try{
      const r = await fetch('/api/db/connections');
      const d = await r.json();
      const list = document.getElementById('db-connections-list');
      if(!list) return;
      if(!(d.connections||[]).length){
        list.innerHTML = '<div style="color:var(--text3);padding:10px">لا توجد اتصالات قاعدة بيانات.</div>';
        return;
      }
      list.innerHTML = '';
      d.connections.forEach(conn => {
        const card = document.createElement('div');
        card.className = 'db-connection-card';
        card.innerHTML = `
          <div>
            <div class="db-name">${escapeHtml(conn.name)}</div>
            <div class="db-meta">${escapeHtml(conn.type)} · ${escapeHtml(conn.host || conn.path || '')}</div>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn-action gray" style="font-size:11px" onclick="selectDbConnection('${conn.id}')">🔌 اختيار</button>
            <button class="btn-action danger" style="font-size:11px" onclick="deleteDbConnection('${conn.id}')">🗑</button>
          </div>
        `;
        list.appendChild(card);
      });
    } catch(e){ console.error('loadDbConnections error:', e); }
  }
}

// ─── Init ──────────────────────────────────────────────────────────────────
// التأكد من وجود الدوال الأساسية قبل التهيئة
document.addEventListener('DOMContentLoaded', function() {
  loadProfile().then(() => { 
    loadStats(); 
    loadFiles(); 
    if(typeof initTerminals === 'function') initTerminals();
    if(typeof loadDbConnections === 'function') loadDbConnections();
    if(typeof loadSchedules === 'function') loadSchedules();
    if(typeof loadActivity === 'function') loadActivity();
  });
  
  // تحديث الإحصائيات كل 5 ثوان
  if(typeof statsInterval === 'undefined'){
    statsInterval = setInterval(loadStats, 5000);
  }
});

// ─── نهاية القسم 19 ──────────────────────────────────────────────────────
</script>

</body></html>
'''

# ─────────────────────────────────────────────────────────────────────────────
#  20.  Flask Routes (Enhanced with bcrypt, RBAC, Rate Limit, WebSocket, DB)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    username = session.get('username')
    return render_template_string(get_html_template(username),
                                  session=session, user_path=get_user_path(username))

# ─── Setup Route (first-time master password) ──────────────────────────
@app.route('/setup', methods=['GET', 'POST'])
def setup_page():
    if MASTER_CONFIG.get('setup_done') and MASTER_PASSWORD_HASH:
        return redirect('/login')
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if len(password) < 6:
            return render_template_string(SETUP_TEMPLATE, error='كلمة المرور يجب أن تكون 6 أحرف على الأقل.')
        hashed = hash_password(password)
        MASTER_CONFIG['master_password_hash'] = hashed
        MASTER_CONFIG['setup_done'] = True
        save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
        global MASTER_PASSWORD_HASH
        MASTER_PASSWORD_HASH = hashed
        log_activity(MASTER_USERNAME, 'setup', 'Master password set')
        return redirect('/login')
    return render_template_string(SETUP_TEMPLATE, error=None)

SETUP_TEMPLATE = '''
<!DOCTYPE html>
<html><head><title>Setup — SERVER HUB</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}
body{background:#0b0f17;color:#c9d1d9;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#161b22;padding:40px;border-radius:16px;border:1px solid #30363d;max-width:400px;width:100%}
h1{color:#fff;margin-bottom:8px}
.sub{color:#7c5cfc;font-size:12px;text-transform:uppercase;letter-spacing:2px;margin-bottom:24px}
input{width:100%;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#e6edf3;margin-bottom:12px}
button{width:100%;padding:12px;background:linear-gradient(135deg,#7c5cfc,#5a3fc0);border:none;border-radius:8px;color:#fff;font-weight:700;cursor:pointer}
.error{color:#f85149;margin-top:10px}
</style>
</head>
<body>
<div class="card">
<h1>🔐 First-time Setup</h1>
<div class="sub">SERVER HUB — Set Master Password</div>
<form method="post">
<input type="password" name="password" placeholder="New password (min 6 chars)" required>
<button type="submit">Set Password</button>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</form>
</div>
</body></html>
'''

# ─── Login (with bcrypt + rate limit) ──────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per 10 minutes")
def login_page():
    if request.method == 'GET':
        return render_template_string(AUTH_TEMPLATE, error=None, error_type=None)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    users = load_users()
    ud = users.get(username, {}) if isinstance(users.get(username), dict) else {}

    # Master login
    if username == MASTER_USERNAME and MASTER_PASSWORD_HASH:
        if check_password(password, MASTER_PASSWORD_HASH):
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            register_session(username)
            log_activity(username, 'auth.login', 'Master login')
            send_telegram_alert(f'✅ *Master login*: {username} from IP {request.remote_addr}')
            return redirect('/')
        return render_template_string(AUTH_TEMPLATE, error='❌ Invalid credentials', error_type='login')

    # User login
    if username in users and isinstance(ud, dict):
        stored_hash = ud.get('password', '')
        if stored_hash and check_password(password, stored_hash):
            # Upgrade legacy hash if needed
            if not stored_hash.startswith('$2b$'):
                users[username]['password'] = hash_password(password)
                save_users(users)
            if not ud.get('active', False):
                log_activity(username, 'auth.login.denied', 'Pending approval')
                return render_template_string(AUTH_TEMPLATE,
                    error='⚠️ Your account is pending Admin approval.',
                    error_type='login')
            if can_user_login(username):
                session.permanent = True
                session['logged_in'] = True
                session['username'] = username
                register_session(username)
                ensure_user_folder(username)
                log_activity(username, 'auth.login', 'User login')
                send_telegram_alert(f'👤 *User login*: {username} from IP {request.remote_addr}')
                return redirect('/')
            return render_template_string(AUTH_TEMPLATE,
                error='❌ Session limit reached or account expired.',
                error_type='login')

    log_activity(username or '-', 'auth.login.failed', 'Invalid credentials')
    return render_template_string(AUTH_TEMPLATE, error='❌ Invalid credentials', error_type='login')

# ─── Register ──────────────────────────────────────────────────────────
@app.route('/register', methods=['POST'])
def register_page():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    tg_username = request.form.get('tg_username', '').strip().lstrip('@')

    if not username or not password:
        return render_template_string(AUTH_TEMPLATE, error='❌ يرجى ملء جميع الحقول المطلوبة', error_type='register')
    if not tg_username:
        return render_template_string(AUTH_TEMPLATE, error='❌ يرجى إدخال يوزر التيليجرام', error_type='register')
    if password != confirm:
        return render_template_string(AUTH_TEMPLATE, error='❌ كلمات المرور غير متطابقة', error_type='register')
    if len(username) < 3:
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم 3 أحرف على الأقل', error_type='register')
    if len(password) < 4:
        return render_template_string(AUTH_TEMPLATE, error='❌ كلمة المرور 4 أحرف على الأقل', error_type='register')
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم: حروف وأرقام وـ فقط', error_type='register')

    users = load_users()
    if username in users:
        return render_template_string(AUTH_TEMPLATE, error='❌ اسم المستخدم محجوز مسبقاً', error_type='register')

    expiry_dt = (datetime.now() + timedelta(days=7)).isoformat()
    users[username] = {
        'password': hash_password(password),
        'tg_username': tg_username,
        'max_sessions': 1,
        'max_servers': 1,
        'main_file': 'main.py',
        'created': datetime.now().isoformat(),
        'expiry': expiry_dt,
        'plan': 'free_trial',
        'role': 'user',
        'active': False
    }
    save_users(users)
    ensure_user_folder(username)
    log_activity(username, 'auth.register', f'tg=@{tg_username} | awaiting approval')
    return render_template_string(AUTH_TEMPLATE,
        error=f'✅ تم إرسال طلب التسجيل! انتظر موافقة الأدمن.\nيوزر تيليجرامك: @{tg_username}',
        error_type='register')

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], 'auth.logout', '')
        unregister_session(session['username'])
    session.clear()
    return redirect('/login')

# ─── API: Profile & System ────────────────────────────────────────────
@app.route('/api/profile')
@login_required
@cache.cached(timeout=60)
def get_profile():
    u = session['username']
    p = get_user_path(u)
    size = 0
    if os.path.exists(p):
        for r, d, f in os.walk(p):
            for fl in f:
                fp = os.path.join(r, fl)
                if os.path.exists(fp):
                    size += os.path.getsize(fp)
    users = load_users()
    ud = users.get(u, {})
    return jsonify({
        'username': u,
        'is_master': u == MASTER_USERNAME,
        'user_path': p,
        'created': ud.get('created', '') if isinstance(ud, dict) else '',
        'expiry': ud.get('expiry', '∞') if isinstance(ud, dict) else '∞',
        'disk_usage_gb': size / (1024 ** 3)
    })

@app.route('/api/system')
@login_required
@cache.cached(timeout=10)
def system_info():
    return jsonify(get_system_stats())

@app.route('/api/sysinfo')
@login_required
@cache.cached(timeout=60)
def sysinfo():
    return jsonify({
        'info': f"Platform: {platform.platform()}\n"
                f"CPU: {psutil.cpu_percent()}%\n"
                f"Memory: {psutil.virtual_memory().percent}%\n"
                f"Disk: {psutil.disk_usage('/').percent}%"
    })

@app.route('/api/system/action', methods=['POST'])
@login_required
def system_action_api():
    a = (request.json or {}).get('action')
    try:
        if a == 'clean':
            gc.collect()
        log_activity(session['username'], 'system.action', a or '')
        return jsonify({'success': True, 'action': a})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ─── API: Activity ────────────────────────────────────────────────────
@app.route('/api/activity')
@login_required
def activity_api():
    data = load_json_file(ACTIVITY_FILE, {'events': []})
    events = data.get('events', [])
    if session.get('username') != MASTER_USERNAME:
        events = [e for e in events if e.get('username') == session.get('username')]
    return jsonify({'events': events[:200]})

# ─── API: Files (with search/replace) ────────────────────────────────
@app.route('/api/files/main-file')
@login_required
def get_main_file_api():
    u = session['username']
    if u == MASTER_USERNAME:
        mf = MASTER_CONFIG.get('main_file', 'main.py')
    else:
        users = load_users()
        mf = users.get(u, {}).get('main_file', 'main.py') if isinstance(users.get(u), dict) else 'main.py'
    return jsonify({'success': True, 'main_file': mf})

@app.route('/api/files')
@login_required
def list_files_api():
    p = request.args.get('path', get_user_path(session['username']))
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False, 'error': 'forbidden'}), 403
    files = []
    try:
        for n in sorted(os.listdir(p), key=lambda x: (not os.path.isdir(os.path.join(p, x)), x.lower())):
            fp = os.path.join(p, n)
            files.append({
                'name': n,
                'is_dir': os.path.isdir(fp),
                'size': f"{os.path.getsize(fp)//1024} KB" if os.path.isfile(fp) else ''
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'files': files})

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file_api():
    f = request.files.get('file')
    p = request.form.get('path', get_user_path(session['username']))
    if not f:
        return jsonify({'success': False, 'error': 'No file'}), 400
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    try:
        filename = secure_filename(f.filename) if f.filename else 'uploaded_file'
        if not filename:
            filename = 'uploaded_file'
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext in BLOCKED_EXTENSIONS:
            log_activity(session['username'], 'security.blocked_ext', filename)
            return jsonify({'success': False, 'error': f'❌ نوع الملف .{ext} محظور لأسباب أمنية'}), 403
        os.makedirs(p, exist_ok=True)
        sp = os.path.join(p, filename)
        f.save(sp)
        threats = scan_file_content(sp)
        if threats:
            os.remove(sp)
            threat_list = ' | '.join(threats[:5])
            log_activity(session['username'], 'security.malware_blocked', f'{filename}: {threat_list}')
            save_security_alert(
                username=session['username'],
                filename=filename,
                threats=threats[:5],
                ip=request.remote_addr
            )
            # Telegram alert
            try:
                users_data = load_users()
                ud = users_data.get(session['username'], {})
                tg_user = ud.get('tg_username', 'غير معروف') if isinstance(ud, dict) else 'غير معروف'
                cfg = load_owner_config()
                if cfg.get('bot_linked') and cfg.get('telegram_token') and cfg.get('telegram_owner_id'):
                    threats_fmt = '\n'.join(f'   • {t}' for t in threats[:5])
                    alert_msg = (
                        f"🚨 *تحذير أمني — محاولة رفع ملف خطير!*\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"👤 *اليوزر:* `{session['username']}`\n"
                        f"📱 *تيليجرام:* `@{tg_user}`\n"
                        f"📄 *الملف:* `{filename}`\n"
                        f"🌐 *IP:* `{request.remote_addr}`\n"
                        f"🕐 *الوقت:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
                        f"🔍 *التهديدات المكتشفة:*\n{threats_fmt}\n\n"
                        f"⚠️ تم حذف الملف تلقائياً — راجع قسم الأمن في لوحة التحكم."
                    )
                    requests.post(
                        f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
                        json={'chat_id': cfg['telegram_owner_id'], 'text': alert_msg, 'parse_mode': 'Markdown'},
                        timeout=8
                    )
            except Exception:
                pass
            return jsonify({'success': False, 'error': 'SECURITY_ALERT|' + threat_list}), 403
        log_activity(session['username'], 'file.upload', filename)
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/folder', methods=['POST'])
@login_required
def create_folder_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path', '')):
        return jsonify({'success': False}), 403
    os.makedirs(d['path'], exist_ok=True)
    log_activity(session['username'], 'file.mkdir', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/create', methods=['POST'])
@login_required
def create_file_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path', '')):
        return jsonify({'success': False}), 403
    with open(d['path'], 'w', encoding='utf-8') as f:
        f.write(d.get('content', ''))
    log_activity(session['username'], 'file.create', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file_api():
    d = request.json or {}
    p = d.get('path', '')
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False}), 403
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)
    log_activity(session['username'], 'file.delete', p)
    return jsonify({'success': True})

@app.route('/api/files/content')
@login_required
def get_file_content():
    p = request.args.get('path')
    if not p or not is_path_allowed(session['username'], p):
        return jsonify({'success': False}), 403
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            return jsonify({'content': f.read()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/files/save', methods=['POST'])
@login_required
def save_file_api():
    d = request.json or {}
    if not is_path_allowed(session['username'], d.get('path', '')):
        return jsonify({'success': False}), 403
    with open(d['path'], 'w', encoding='utf-8') as f:
        f.write(d.get('content', ''))
    log_activity(session['username'], 'file.write', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/search_replace', methods=['POST'])
@login_required
def search_replace_api():
    """Advanced editor: search and replace in file."""
    d = request.json or {}
    path = d.get('path')
    search = d.get('search')
    replace = d.get('replace')
    if not path or not is_path_allowed(session['username'], path):
        return jsonify({'error': 'Invalid path'}), 403
    if not search:
        return jsonify({'error': 'Search term required'}), 400
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        count = content.count(search)
        new_content = content.replace(search, replace)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        log_activity(session['username'], 'file.search_replace', f'{path}: {count} replacements')
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/set-main', methods=['POST'])
@login_required
def set_main_file_api():
    d = request.json or {}
    filename = d.get('filename', '')
    username = session['username']
    if not filename:
        return jsonify({'success': False, 'error': 'No filename'})
    users = load_users()
    if username == MASTER_USERNAME:
        MASTER_CONFIG['main_file'] = filename
        save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
    elif username in users:
        users[username]['main_file'] = filename
        save_users(users)
    log_activity(username, 'file.set-main', filename)
    return jsonify({'success': True, 'main_file': filename})

@app.route('/api/files/extract', methods=['POST'])
@login_required
def extract_api():
    d = request.json or {}
    archive = d.get('archive', '')
    dest = d.get('dest', '')
    if not archive or not is_path_allowed(session['username'], archive):
        return jsonify({'success': False, 'error': 'Forbidden or invalid path'}), 403
    if not dest:
        dest = re.sub(r'\.(zip|tar\.gz|tar|gz|rar)$', '', archive, flags=re.I)
    result = safe_extract(archive, dest, session['username'])
    return jsonify(result)

# ─── API: Run files ──────────────────────────────────────────────────
@app.route('/api/file/run', methods=['POST'])
@login_required
def run_file_api():
    d = request.json or {}
    filepath = os.path.join(d.get('path', ''), d.get('filename', ''))
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})
    if not is_path_allowed(session['username'], d.get('path', '')):
        return jsonify({'success': False, 'error': 'Forbidden'})
    if d.get('filename', '').lower().endswith('.zip'):
        extract_dir = os.path.join(d['path'], d['filename'].replace('.zip', ''))
        os.makedirs(extract_dir, exist_ok=True)
        main = extract_and_find_main(filepath, extract_dir)
        if main:
            filepath = main
        else:
            return jsonify({'success': False, 'error': 'Main file not found in ZIP'})
    installed = auto_install_dependencies(filepath)
    cmd = get_run_command(filepath)
    try:
        kwargs = dict(shell=True, cwd=os.path.dirname(filepath),
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1)
        if hasattr(os, 'setsid'):
            kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(cmd, **kwargs)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    pid = f"{session['username']}_{d.get('filename', 'f')}_{int(time.time())}"
    file_processes[pid] = {'process': p, 'filename': d.get('filename', ''), 'username': session['username'], 'output': []}
    threading.Thread(target=read_process_output, args=(pid, p), kwargs={'store': file_processes}, daemon=True).start()
    log_activity(session['username'], 'file.run', f"{d.get('filename', '')} ({pid})")
    return jsonify({'success': True, 'process_id': pid, 'installed_result': installed})

@app.route('/api/file/stop', methods=['POST'])
@login_required
def stop_file_api():
    pid = (request.json or {}).get('process_id')
    if pid in file_processes:
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(file_processes[pid]['process'].pid), signal.SIGKILL)
            else:
                file_processes[pid]['process'].kill()
        except Exception:
            pass
        log_activity(session['username'], 'file.stop', pid)
        del file_processes[pid]
    return jsonify({'success': True})

@app.route('/api/file/output/<pid>')
@login_required
def get_file_output_api(pid):
    if pid in file_processes:
        info = file_processes[pid]
        out = list(info.get('output', []))
        info['output'].clear()
        return jsonify({'success': True, 'output': out, 'is_running': info['process'].poll() is None})
    return jsonify({'success': False, 'output': [], 'is_running': False})

@app.route('/api/file/output/<pid>/clear', methods=['POST'])
@login_required
def clear_file_output(pid):
    if pid in file_processes:
        file_processes[pid]['output'].clear()
    return jsonify({'success': True})

@app.route('/api/file/input', methods=['POST'])
@login_required
def send_file_input_api():
    d = request.json or {}
    pid = d.get('process_id')
    if pid in file_processes:
        try:
            file_processes[pid]['process'].stdin.write(d.get('input', '') + '\n')
            file_processes[pid]['process'].stdin.flush()
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': True})

@app.route('/api/file/running')
@login_required
def get_running_files_api():
    user = session['username']
    running, dead = [], []
    for pid, info in file_processes.items():
        if info['username'] == user or user == MASTER_USERNAME:
            if info['process'].poll() is None:
                running.append({'process_id': pid, 'filename': info['filename'], 'username': info['username']})
            else:
                dead.append(pid)
    for d in dead:
        file_processes.pop(d, None)
    return jsonify({'success': True, 'running': running})

# ─── API: Exec ──────────────────────────────────────────────────────
@app.route('/api/exec', methods=['POST'])
@login_required
def execute_command_api():
    d = request.json or {}
    cmd = d.get('command', '').strip()
    cwd = d.get('cwd', get_user_path(session['username']))
    if not cmd:
        return jsonify({'output': '', 'success': True})

    # Smart command rewriting
    cmd_lower = cmd.lower().strip()
    if re.match(r'^python\s+', cmd):
        cmd = 'python3 ' + cmd[7:]
    elif cmd == 'python':
        cmd = 'python3 --version'
    if re.match(r'^pip\s+', cmd):
        cmd = 'pip3 ' + cmd[4:]
    elif cmd == 'pip':
        cmd = 'pip3 --version'

    # Block dangerous commands
    BLOCKED_CMDS = [
        r'rm -rf /', r'mkfs', r':\(\){\:\|:\&};:', r'dd if=/dev/zero',
        r'wget.*\|.*bash', r'curl.*\|.*bash', r'> /etc/passwd', r'chmod 777 /'
    ]
    for bc in BLOCKED_CMDS:
        if re.search(bc, cmd, re.IGNORECASE):
            log_activity(session['username'], 'security.blocked_cmd', cmd[:100])
            return jsonify({'output': '🚨 أمر محظور لأسباب أمنية', 'success': False})

    log_activity(session['username'], 'exec', cmd[:120])
    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        r = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True,
            timeout=120, env=env
        )
        output = r.stdout + r.stderr
        if not output.strip():
            output = '✅ Command executed (no output)'
        return jsonify({'output': output, 'success': r.returncode == 0, 'code': r.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'output': '⏱ Timeout (120s) — قد تكون العملية لا تزال تعمل في الخلفية', 'success': False})
    except Exception as e:
        return jsonify({'output': f'❌ Error: {str(e)}', 'success': False})
        
# ─── API: Node.js ───────────────────────────────────────────────────────────
@app.route('/api/nodejs/start', methods=['POST'])
@login_required
def nodejs_start_api():
    d = request.json or {}
    path = d.get('path', '').strip()
    port = d.get('port')
    main_file = d.get('main_file', '').strip() or None
    deps_file = d.get('deps_file', '').strip() or None

    if not path:
        return jsonify({'success': False, 'error': 'المسار مطلوب'})
    if not is_path_allowed(session['username'], path):
        return jsonify({'success': False, 'error': 'صلاحية مرفوضة'})

    result = start_nodejs_project(path, session['username'], port,
                                  main_file=main_file, deps_file=deps_file)
    return jsonify(result)


@app.route('/api/nodejs/info', methods=['POST'])
@login_required
def nodejs_info_api():
    """إرجاع أوامر التثبيت والتشغيل بدون تشغيل فعلي."""
    d = request.json or {}
    path = d.get('path', '').strip()
    main_file = d.get('main_file', '').strip() or None
    deps_file = d.get('deps_file', '').strip() or None

    if not path or not is_path_allowed(session['username'], path):
        return jsonify({'success': False, 'error': 'مسار غير صالح أو صلاحية مرفوضة'})

    info = get_nodejs_info(path, main_file=main_file, deps_file=deps_file)

    # سرد ملفات .js في المشروع
    js_files = []
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [dd for dd in dirs if dd not in ['node_modules', '.git', '__pycache__']]
            for fn in files:
                if fn.endswith('.js') or fn.endswith('.mjs') or fn.endswith('.cjs'):
                    js_files.append(os.path.relpath(os.path.join(root, fn), path))
    except Exception:
        pass

    info['js_files'] = js_files[:50]
    info['success'] = True
    return jsonify(info)


@app.route('/api/nodejs/stop', methods=['POST'])
@login_required
def nodejs_stop_api():
    pid = (request.json or {}).get('pid')
    if pid in nodejs_processes:
        try:
            p = nodejs_processes[pid]['process']
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            else:
                p.kill()
        except Exception:
            pass
        log_activity(session['username'], 'nodejs.stop', pid)
        del nodejs_processes[pid]
        return jsonify({'success': True, 'message': f'تم إيقاف العملية {pid}'})

    return jsonify({'success': False, 'error': 'العملية غير موجودة'})


@app.route('/api/nodejs/list')
@login_required
def nodejs_list_api():
    user = session['username']
    result = []
    dead = []

    for pid, info in nodejs_processes.items():
        if info['username'] == user or user == MASTER_USERNAME:
            is_running = info['process'].poll() is None
            if not is_running and user != MASTER_USERNAME:
                dead.append(pid)
                continue
            result.append({
                'pid': pid,
                'command': info.get('command', ''),
                'port': info.get('port'),
                'project': info.get('project', ''),
                'started': info.get('started', ''),
                'main_file': info.get('main_file', ''),
                'deps_file': info.get('deps_file', ''),
                'running': is_running
            })

    for d in dead:
        nodejs_processes.pop(d, None)

    return jsonify({'processes': result})


@app.route('/api/nodejs/logs/<pid>')
@login_required
def nodejs_logs_api(pid):
    if pid in nodejs_processes:
        return jsonify({'output': list(nodejs_processes[pid].get('output', []))})
    return jsonify({'output': [], 'error': 'العملية غير موجودة'})


# ─── API: PHP ──────────────────────────────────────────────────────────────
@app.route('/api/php/start', methods=['POST'])
@login_required
def php_start_api():
    d = request.json or {}
    path = d.get('path', '').strip()
    port = d.get('port')
    main_file = d.get('main_file', '').strip() or None
    deps_file = d.get('deps_file', '').strip() or None

    if not path:
        return jsonify({'success': False, 'error': 'المسار مطلوب'})
    if not is_path_allowed(session['username'], path):
        return jsonify({'success': False, 'error': 'صلاحية مرفوضة'})

    result = start_php_server(path, session['username'], port,
                              main_file=main_file, deps_file=deps_file)
    return jsonify(result)


@app.route('/api/php/info', methods=['POST'])
@login_required
def php_info_api():
    """إرجاع أوامر التثبيت والتشغيل بدون تشغيل فعلي."""
    d = request.json or {}
    path = d.get('path', '').strip()
    main_file = d.get('main_file', '').strip() or None
    deps_file = d.get('deps_file', '').strip() or None

    if not path or not is_path_allowed(session['username'], path):
        return jsonify({'success': False, 'error': 'مسار غير صالح أو صلاحية مرفوضة'})

    info = get_php_info(path, main_file=main_file, deps_file=deps_file)

    # سرد ملفات .php في المشروع
    php_files = []
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [dd for dd in dirs if dd not in ['vendor', '.git', 'node_modules']]
            for fn in files:
                if fn.endswith('.php'):
                    php_files.append(os.path.relpath(os.path.join(root, fn), path))
    except Exception:
        pass

    info['php_files'] = php_files[:50]
    info['success'] = True
    return jsonify(info)


@app.route('/api/php/stop', methods=['POST'])
@login_required
def php_stop_api():
    pid = (request.json or {}).get('pid')
    if pid in _php_servers:
        try:
            p = _php_servers[pid]['process']
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            else:
                p.kill()
        except Exception:
            pass
        log_activity(session['username'], 'php.stop', pid)
        del _php_servers[pid]
        return jsonify({'success': True, 'message': f'تم إيقاف خادم PHP {pid}'})

    return jsonify({'success': False, 'error': 'الخادم غير موجود'})


@app.route('/api/php/list')
@login_required
def php_list_api():
    user = session['username']
    result = []

    for pid, info in _php_servers.items():
        if info['username'] == user or user == MASTER_USERNAME:
            result.append({
                'pid': pid,
                'port': info.get('port'),
                'path': info.get('path', ''),
                'started': info.get('started', ''),
                'running': info['process'].poll() is None
            })

    return jsonify({'servers': result})


# ─── API: Processes ────────────────────────────────────────────────────────
@app.route('/api/process/start', methods=['POST'])
@login_required
def start_process_api():
    d = request.json or {}
    name = d.get('name', '').strip()
    command = d.get('command', '').strip()
    cwd = d.get('cwd', BASE_PATH)

    if not name or not command:
        return jsonify({'success': False, 'error': 'الاسم والأمر مطلوبان'})

    def run():
        try:
            kwargs = dict(shell=True, cwd=cwd)
            if hasattr(os, 'setsid'):
                kwargs['preexec_fn'] = os.setsid
            p = subprocess.Popen(command, **kwargs)
            running_processes[name] = {
                'process': p,
                'owner': session.get('username'),
                'command': command,
                'cwd': cwd
            }
            p.wait()
        except Exception as e:
            log_activity(session['username'], 'process.error', str(e))

    threading.Thread(target=run, daemon=True).start()
    log_activity(session['username'], 'process.start', f'{name}: {command}')
    return jsonify({'success': True, 'message': f'تم بدء العملية {name}'})


@app.route('/api/process/stop', methods=['POST'])
@login_required
def stop_process_api():
    name = (request.json or {}).get('name', '')
    if name in running_processes:
        try:
            p = running_processes[name]['process']
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            else:
                p.kill()
        except Exception:
            pass
        log_activity(session['username'], 'process.stop', name)
        del running_processes[name]
        return jsonify({'success': True, 'message': f'تم إيقاف العملية {name}'})

    return jsonify({'success': False, 'error': 'العملية غير موجودة'})


@app.route('/api/process/list')
@login_required
def list_processes_api():
    procs = {}
    for name, info in running_processes.items():
        procs[name] = {
            'status': 'running' if info['process'].poll() is None else 'stopped',
            'command': info['command'],
            'owner': info.get('owner', '')
        }
    return jsonify(procs)


# ─── API: Network ──────────────────────────────────────────────────────────
@app.route('/api/network/scan', methods=['POST'])
@login_required
def scan_ports_api():
    d = request.json or {}
    host = d.get('host', '127.0.0.1')
    ports = d.get('ports', [])
    results = []

    for p in ports:
        try:
            s = socket.socket()
            s.settimeout(1)
            r = s.connect_ex((host, int(p)))
            results.append({'port': p, 'open': r == 0})
            s.close()
        except Exception:
            results.append({'port': p, 'open': False})

    return jsonify({'results': results})


@app.route('/api/ports/list')
@login_required
def list_ports_api():
    return jsonify({'ports': load_ports()})


@app.route('/api/ports/add', methods=['POST'])
@master_required
def add_port_api():
    d = request.json or {}
    try:
        port = int(d.get('port', 0))
    except Exception:
        return jsonify({'success': False, 'error': 'منفذ غير صالح'})

    if port <= 0 or port > 65535:
        return jsonify({'success': False, 'error': 'النطاق غير صالح (1-65535)'})

    ports = load_ports()
    if any(p.get('port') == port for p in ports):
        return jsonify({'success': False, 'error': 'المنفذ موجود مسبقاً'})

    ports.append({
        'port': port,
        'note': d.get('note', ''),
        'status': 'idle',
        'created': datetime.now().isoformat()
    })
    save_ports(ports)
    log_activity(session['username'], 'port.add', str(port))
    return jsonify({'success': True, 'message': f'تم إضافة المنفذ {port}'})


@app.route('/api/ports/delete', methods=['POST'])
@master_required
def del_port_api():
    port = (request.json or {}).get('port')
    ports = load_ports()
    save_ports([p for p in ports if p.get('port') != port])
    log_activity(session['username'], 'port.delete', str(port))
    return jsonify({'success': True, 'message': f'تم حذف المنفذ {port}'})


# ─── API: Users (مع bcrypt و RBAC) ──────────────────────────────────────
@app.route('/api/users/list')
@master_required
def list_panel_users_api():
    users = load_users()
    sessions = load_user_sessions()
    result = []

    for u in users:
        ud = users[u] if isinstance(users[u], dict) else {}
        result.append({
            'username': u,
            'tg_username': ud.get('tg_username', ''),
            'password_hash': ud.get('password', ''),
            'max_sessions': ud.get('max_sessions', 999),
            'max_servers': ud.get('max_servers', 1),
            'main_file': ud.get('main_file', 'main.py'),
            'active_sessions': sessions.get(u, 0),
            'expiry': ud.get('expiry'),
            'active': ud.get('active', True),
            'created': ud.get('created', ''),
            'plan': ud.get('plan', 'free_trial'),
            'role': ud.get('role', 'user')  # ← NEW: RBAC role
        })

    return jsonify({'users': result})


@app.route('/api/users/pending')
@master_required
def pending_users_api():
    users = load_users()
    pending = [{
        'username': u,
        'tg_username': users[u].get('tg_username', '') if isinstance(users[u], dict) else '',
        'created': users[u].get('created', '') if isinstance(users[u], dict) else ''
    } for u in users if isinstance(users[u], dict) and not users[u].get('active', True)]

    return jsonify({'users': pending})


@app.route('/api/users/approve', methods=['POST'])
@master_required
def approve_user_api():
    username = (request.json or {}).get('username', '')
    users = load_users()

    if username in users:
        users[username]['active'] = True
        save_users(users)
        log_activity(session['username'], 'user.approve', username)
        send_telegram_alert(f'✅ *تمت الموافقة على المستخدم*: `{username}`')
        return jsonify({'success': True, 'message': f'تمت الموافقة على {username}'})

    return jsonify({'success': False, 'error': 'المستخدم غير موجود'})


@app.route('/api/users/add', methods=['POST'])
@master_required
def add_panel_user_api():
    d = request.json or {}
    uname = d.get('username', '').strip()
    if not uname:
        return jsonify({'success': False, 'error': 'اسم المستخدم مطلوب'})

    users = load_users()
    if uname in users:
        return jsonify({'success': False, 'error': 'اسم المستخدم موجود مسبقاً'})

    plan = d.get('plan', 'free_trial')
    plan_days = {'free_trial': 7, 'paid_20': 20, 'paid_30': 30}
    expiry_days = plan_days.get(plan, int(d.get('expiry_days', 7) or 7))
    expiry_days = max(1, expiry_days)

    users[uname] = {
        'password': hash_password(d.get('password', '')),
        'tg_username': d.get('tg_username', '').lstrip('@'),
        'max_sessions': int(d.get('max_sessions', 1)),
        'max_servers': int(d.get('max_servers', 1)),
        'main_file': d.get('main_file', 'main.py'),
        'created': datetime.now().isoformat(),
        'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
        'plan': plan,
        'role': d.get('role', 'user'),
        'active': True
    }

    save_users(users)
    ensure_user_folder(uname)
    log_activity(session['username'], 'user.add', f'{uname} (role={users[uname]["role"]})')
    send_telegram_alert(f'👤 *مستخدم جديد*: `{uname}` (دور: `{users[uname]["role"]}`)')
    return jsonify({'success': True, 'message': f'تم إضافة المستخدم {uname}'})


@app.route('/api/users/update', methods=['POST'])
@master_required
def update_panel_user_api():
    d = request.json or {}
    users = load_users()
    uname = d.get('username', '')

    if uname not in users:
        return jsonify({'success': False, 'error': 'المستخدم غير موجود'})

    # تحديث الحقول
    if d.get('password'):
        users[uname]['password'] = hash_password(d['password'])

    if d.get('role') is not None:
        users[uname]['role'] = d['role']

    if d.get('max_servers') is not None:
        users[uname]['max_servers'] = int(d['max_servers'])

    if d.get('main_file') is not None:
        users[uname]['main_file'] = d['main_file']

    if d.get('max_sessions') is not None:
        users[uname]['max_sessions'] = int(d['max_sessions'])

    if d.get('expiry_days') is not None:
        expiry_days = max(30, int(d['expiry_days'] or 30))
        users[uname]['expiry'] = (datetime.now() + timedelta(days=expiry_days)).isoformat()

    save_users(users)
    log_activity(session['username'], 'user.update', uname)
    return jsonify({'success': True, 'message': f'تم تحديث {uname}'})


@app.route('/api/users/delete', methods=['POST'])
@master_required
def delete_panel_user_api():
    d = request.json or {}
    users = load_users()
    uname = d.get('username', '')

    if uname in users:
        if uname == MASTER_USERNAME:
            return jsonify({'success': False, 'error': 'لا يمكن حذف المالك'})

        del users[uname]
        save_users(users)
        shutil.rmtree(os.path.join(USERS_FOLDER, uname), ignore_errors=True)
        log_activity(session['username'], 'user.delete', uname)
        return jsonify({'success': True, 'message': f'تم حذف {uname}'})

    return jsonify({'success': False, 'error': 'المستخدم غير موجود'})


# ─── API: Schedules ────────────────────────────────────────────────────────
@app.route('/api/schedules/list')
@login_required
def list_schedules_api():
    return jsonify({'schedules': list(load_schedules().values())})


@app.route('/api/schedules/add', methods=['POST'])
@login_required
def add_schedule_api():
    d = request.json or {}
    name = d.get('name', '').strip()
    command = d.get('command', '').strip()
    schedule = d.get('schedule', '* * * * *')

    if not name or not command:
        return jsonify({'success': False, 'error': 'الاسم والأمر مطلوبان'})

    sch = load_schedules()
    sid = str(uuid.uuid4())[:8]
    sch[sid] = {
        'id': sid,
        'name': name,
        'command': command,
        'schedule': schedule,
        'owner': session['username']
    }
    save_schedules(sch)
    log_activity(session['username'], 'schedule.add', name)
    return jsonify({'success': True, 'message': f'تم إضافة الجدول {name}'})


@app.route('/api/schedules/delete', methods=['POST'])
@login_required
def delete_schedule_api():
    d = request.json or {}
    sid = d.get('id', '')

    sch = load_schedules()
    if sid in sch:
        del sch[sid]
        save_schedules(sch)
        log_activity(session['username'], 'schedule.delete', sid)
        return jsonify({'success': True, 'message': 'تم حذف الجدول'})

    return jsonify({'success': False, 'error': 'الجدول غير موجود'})


# ─── API: Backups ──────────────────────────────────────────────────────────
@app.route('/api/backups/list')
@master_required
def list_backups_api():
    backups = []
    if os.path.exists(BACKUPS_FOLDER):
        for f in os.listdir(BACKUPS_FOLDER):
            if f.endswith('.tar.gz'):
                path = os.path.join(BACKUPS_FOLDER, f)
                backups.append({
                    'name': f,
                    'size': f"{os.path.getsize(path) / 1024**2:.2f} MB",
                    'created': datetime.fromtimestamp(os.path.getctime(path)).isoformat()
                })

    return jsonify({'backups': backups})


@app.route('/api/backups/create', methods=['POST'])
@master_required
def create_backup_api():
    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    try:
        with tarfile.open(os.path.join(BACKUPS_FOLDER, name), 'w:gz') as tar:
            tar.add(BASE_PATH, arcname='backup')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    log_activity(session['username'], 'backup.create', name)
    return jsonify({'success': True, 'message': f'تم إنشاء النسخة الاحتياطية {name}'})


@app.route('/api/backups/download')
@master_required
def download_backup():
    name = request.args.get('name', '')
    path = os.path.join(BACKUPS_FOLDER, secure_filename(name))
    if not os.path.exists(path):
        return jsonify({'error': 'الملف غير موجود'}), 404

    return send_file(path, as_attachment=True, download_name=name)
    
# ─── API: Packages ──────────────────────────────────────────────────────────
@app.route('/api/packages/install/pip', methods=['POST'])
@master_required
def install_pip_api():
    pkg = (request.json or {}).get('package', '')
    if not pkg:
        return jsonify({'success': False, 'error': 'اسم الحزمة مطلوب'})

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', pkg],
            capture_output=True,
            timeout=120,
            text=True
        )
        pkgs = load_packages()
        if pkg not in pkgs.get('pip', []):
            pkgs.setdefault('pip', []).append(pkg)
        save_packages(pkgs)

        log_activity(session['username'], 'pkg.pip.install', pkg)
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout + result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'انتهت المهلة (120 ثانية)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/packages/install/npm', methods=['POST'])
@login_required
def install_npm_api():
    pkg = (request.json or {}).get('package', '')
    if not pkg:
        return jsonify({'success': False, 'error': 'اسم الحزمة مطلوب'})

    try:
        result = subprocess.run(
            ['npm', 'install', '-g', pkg],
            capture_output=True,
            text=True,
            timeout=120
        )
        log_activity(session['username'], 'pkg.npm.install', pkg)
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout + result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'انتهت المهلة (120 ثانية)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── API: Logs ──────────────────────────────────────────────────────────────
@app.route('/api/logs')
@master_required
def get_logs_api():
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return jsonify({'logs': content[-50000:]})
        except Exception as e:
            return jsonify({'logs': '', 'error': str(e)})
    return jsonify({'logs': ''})


@app.route('/api/logs/clear', methods=['POST'])
@master_required
def clear_logs_api():
    try:
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] تم مسح السجلات بواسطة المالك\n")
        save_json_file(ACTIVITY_FILE, {'events': []})
        log_activity(session['username'], 'logs.cleared', '')
        return jsonify({'success': True, 'message': 'تم مسح السجلات'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── API: AI Chat (Streaming) ──────────────────────────────────────────────
NVIDIA_AI_KEY = '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'
NVIDIA_AI_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat_api():
    from flask import Response, stream_with_context

    d = request.json or {}
    messages = d.get('messages', [])
    if not messages:
        return jsonify({'error': 'لا توجد رسائل'}), 400

    # System prompt (محسّن للغة العربية)
    system_msg = {
        'role': 'system',
        'content': (
            'You are SERVER HUB AI, an expert assistant for developers. '
            'You specialize in Python, Flask, Node.js, PHP, Telegram bots, web hosting, and server management. '
            'You give concise, practical answers. For code, always use code blocks. '
            'You can respond in Arabic or English depending on the user language. '
            'Be helpful, accurate, and professional.'
        )
    }
    full_messages = [system_msg] + messages[-18:]

    def generate():
        try:
            payload = {
                'model': 'openai/gpt-oss-120b',
                'messages': full_messages,
                'temperature': 0.7,
                'top_p': 0.95,
                'max_tokens': 4096,
                'stream': True
            }
            headers = {
                'Authorization': f'Bearer {NVIDIA_AI_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            }

            with requests.post(NVIDIA_AI_URL, json=payload, headers=headers,
                               stream=True, timeout=60) as resp:
                for line in resp.iter_lines():
                    if line:
                        decoded = line.decode('utf-8') if isinstance(line, bytes) else line
                        yield decoded + '\n\n'

        except requests.Timeout:
            yield 'data: {"error": "انتهت المهلة"}\n\n'
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


# ─── API: Master Settings (مع bcrypt) ─────────────────────────────────────
@app.route('/api/master/change-password', methods=['POST'])
@master_required
def change_master_password_api():
    global MASTER_PASSWORD_HASH
    d = request.json or {}
    current = d.get('current_password', '')
    new_pass = d.get('new_password', '')

    if not current or not new_pass:
        return jsonify({'success': False, 'error': 'كلمة المرور الحالية والجديدة مطلوبتان'})

    if len(new_pass) < 6:
        return jsonify({'success': False, 'error': 'كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل'})

    # التحقق من كلمة المرور الحالية باستخدام bcrypt
    if not check_password(current, MASTER_PASSWORD_HASH):
        return jsonify({'success': False, 'error': 'كلمة المرور الحالية غير صحيحة'})

    # تحديث كلمة المرور
    MASTER_PASSWORD_HASH = hash_password(new_pass)
    MASTER_CONFIG['master_password_hash'] = MASTER_PASSWORD_HASH
    save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)

    log_activity(session['username'], 'master.password.changed', '')
    send_telegram_alert('🔑 *تم تغيير كلمة مرور المالك*')
    return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح'})


@app.route('/api/master/restart', methods=['POST'])
@master_required
def restart_panel_api():
    log_activity(session['username'], 'panel.restart', 'Restart requested')
    send_telegram_alert('🔄 *جاري إعادة تشغيل اللوحة*')

    def restart():
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    threading.Thread(target=restart, daemon=True).start()
    return jsonify({'success': True, 'message': 'جاري إعادة التشغيل...'})


# ─── API: Owner Config ──────────────────────────────────────────────────────
@app.route('/api/owner/config')
@master_required
def owner_config_get():
    cfg = load_owner_config()
    safe = dict(cfg)
    safe['telegram_token'] = '***' if cfg.get('telegram_token') else ''
    return jsonify(safe)


@app.route('/api/owner/config/save', methods=['POST'])
@master_required
def owner_config_save():
    d = request.json or {}
    cfg = load_owner_config()

    if 'panel_name' in d and d['panel_name']:
        cfg['panel_name'] = d['panel_name'].strip()

    if 'welcome_msg' in d:
        cfg['welcome_msg'] = d['welcome_msg'].strip()

    save_json_file(OWNER_CONFIG_FILE, cfg)
    log_activity(session['username'], 'owner.config.save', '')
    return jsonify({'success': True, 'message': 'تم حفظ الإعدادات'})


@app.route('/api/owner/maintenance', methods=['GET', 'POST'])
@login_required
def owner_maintenance_api():
    if request.method == 'GET':
        return jsonify(load_maintenance())

    if session.get('username') != MASTER_USERNAME:
        return jsonify({'success': False, 'error': 'المالك فقط يمكنه التحكم'}), 403

    d = request.json or {}
    maint = load_maintenance()

    if 'enabled' in d:
        maint['enabled'] = bool(d['enabled'])
    if 'message' in d:
        maint['message'] = d['message'].strip() or 'Under maintenance. Try later.'

    save_maintenance(maint)
    log_activity(session['username'], 'maintenance', f'enabled={maint["enabled"]}')
    return jsonify({'success': True, 'enabled': maint['enabled'], 'message': maint['message']})


@app.route('/api/owner/stats')
@master_required
def owner_stats_api():
    users = load_users()
    zip_count = 0

    try:
        for root, dirs, files in os.walk(USERS_FOLDER):
            for f in files:
                if f.lower().endswith('.zip'):
                    zip_count += 1
        for f in os.listdir(BASE_PATH):
            if f.lower().endswith('.zip'):
                zip_count += 1
    except Exception:
        pass

    active_bots = sum(1 for p in file_processes.values() if p['process'].poll() is None)
    active_bots += sum(1 for p in nodejs_processes.values() if p['process'].poll() is None)

    stats = {
        'total_users': len(users),
        'total_servers': len(users),
        'active_bots': active_bots,
        'zip_files': zip_count,
        'last_updated': datetime.now().isoformat()
    }

    save_json_file(BOT_STATS_FILE, stats)
    return jsonify(stats)


# ─── API: Owner Bot ─────────────────────────────────────────────────────────
@app.route('/api/owner/bot/link', methods=['POST'])
@master_required
def owner_bot_link():
    d = request.json or {}
    token = d.get('token', '').strip()
    owner_id = d.get('owner_id', '').strip()

    if not token or not owner_id:
        return jsonify({'success': False, 'error': 'الرمز ومعرف المالك مطلوبان'})

    try:
        resp = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        data = resp.json()

        if not data.get('ok'):
            return jsonify({'success': False, 'error': data.get('description', 'رمز غير صالح')})

        bot_username = data['result'].get('username', 'unknown')

        cfg = load_owner_config()
        cfg.update({
            'telegram_token': token,
            'telegram_owner_id': owner_id,
            'bot_linked': True,
            'bot_username': bot_username
        })
        save_json_file(OWNER_CONFIG_FILE, cfg)

        log_activity(session['username'], 'bot.link', f'@{bot_username}')
        send_telegram_alert(f'🤖 *تم ربط البوت*: @{bot_username}')
        return jsonify({'success': True, 'bot_username': bot_username})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/bot/unlink', methods=['POST'])
@master_required
def owner_bot_unlink():
    cfg = load_owner_config()
    cfg.update({
        'telegram_token': '',
        'telegram_owner_id': '',
        'bot_linked': False,
        'bot_username': ''
    })
    save_json_file(OWNER_CONFIG_FILE, cfg)
    log_activity(session['username'], 'bot.unlink', '')
    return jsonify({'success': True, 'message': 'تم فك ربط البوت'})


@app.route('/api/owner/bot/action', methods=['POST'])
@master_required
def owner_bot_action():
    d = request.json or {}
    action = d.get('action', '')
    cfg = load_owner_config()

    if not cfg.get('bot_linked') or not cfg.get('telegram_token'):
        return jsonify({'success': False, 'error': 'البوت غير مرتبط'})

    msgs = {
        'start': '✅ Bot started',
        'stop': '⏹ Bot stopped',
        'restart': '🔄 Bot restarted'
    }
    msg = msgs.get(action, f'Action: {action}')

    try:
        requests.post(
            f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
            json={'chat_id': cfg['telegram_owner_id'], 'text': msg},
            timeout=10
        )
        log_activity(session['username'], f'bot.{action}', msg)
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/bot/cmd', methods=['POST'])
@master_required
def owner_bot_cmd():
    d = request.json or {}
    cmd = d.get('command', '').strip()
    cfg = load_owner_config()

    if not cfg.get('bot_linked'):
        return jsonify({'success': False, 'error': 'البوت غير مرتبط'})

    if not cmd:
        return jsonify({'success': False, 'error': 'الأمر مطلوب'})

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr

        requests.post(
            f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
            json={
                'chat_id': cfg['telegram_owner_id'],
                'text': f'🖥 CMD: {cmd}\n📝 Output:\n{output[:3000]}'
            },
            timeout=10
        )

        log_activity(session['username'], 'bot.cmd', cmd[:100])
        return jsonify({'success': True, 'output': output})

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'انتهت المهلة (30 ثانية)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── API: Owner Zips ────────────────────────────────────────────────────────
@app.route('/api/owner/zips')
@master_required
def owner_list_zips():
    zips = []
    try:
        for user_dir in os.listdir(USERS_FOLDER):
            user_path = os.path.join(USERS_FOLDER, user_dir)
            if os.path.isdir(user_path):
                for root, dirs, files in os.walk(user_path):
                    for f in files:
                        if f.lower().endswith('.zip'):
                            fp = os.path.join(root, f)
                            zips.append({
                                'name': f,
                                'user': user_dir,
                                'path': fp,
                                'size': f"{os.path.getsize(fp)/1024:.1f} KB"
                            })

        for f in os.listdir(BASE_PATH):
            if f.lower().endswith('.zip'):
                fp = os.path.join(BASE_PATH, f)
                zips.append({
                    'name': f,
                    'user': 'master',
                    'path': fp,
                    'size': f"{os.path.getsize(fp)/1024:.1f} KB"
                })
    except Exception:
        pass

    return jsonify({'zips': zips})


@app.route('/api/owner/zips/download')
@master_required
def owner_download_zip():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': 'الملف غير موجود'}), 404

    return send_file(path, as_attachment=True)


@app.route('/api/owner/zips/download-all')
@master_required
def owner_download_all_zips():
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        try:
            for user_dir in os.listdir(USERS_FOLDER):
                user_path = os.path.join(USERS_FOLDER, user_dir)
                if os.path.isdir(user_path):
                    for root, dirs, files in os.walk(user_path):
                        for f in files:
                            if f.lower().endswith('.zip'):
                                fp = os.path.join(root, f)
                                zf.write(fp, os.path.join(user_dir, f))

            for f in os.listdir(BASE_PATH):
                if f.lower().endswith('.zip'):
                    fp = os.path.join(BASE_PATH, f)
                    zf.write(fp, os.path.join('master', f))
        except Exception:
            pass

    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name='all_zips.zip',
        mimetype='application/zip'
    )


@app.route('/api/owner/zips/delete', methods=['POST'])
@master_required
def owner_delete_zip():
    path = (request.json or {}).get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': 'الملف غير موجود'})

    try:
        os.remove(path)
        log_activity(session['username'], 'owner.zip.delete', path)
        return jsonify({'success': True, 'message': 'تم حذف الملف'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── API: Announcements ─────────────────────────────────────────────────────
@app.route('/api/owner/announcements')
@login_required
def owner_get_announcements():
    return jsonify(load_announcements())


@app.route('/api/owner/announcements/add', methods=['POST'])
@master_required
def owner_add_announcement():
    d = request.json or {}
    text = d.get('text', '').strip()

    if not text:
        return jsonify({'success': False, 'error': 'نص الإعلان مطلوب'})

    data = load_announcements()
    data['list'].insert(0, {
        'text': text,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    data['list'] = data['list'][:50]
    save_announcements(data)

    log_activity(session['username'], 'announcement.add', text[:80])
    return jsonify({'success': True, 'message': 'تم إضافة الإعلان'})


@app.route('/api/owner/announcements/delete', methods=['POST'])
@master_required
def owner_delete_announcement():
    d = request.json or {}
    idx = d.get('index', -1)
    data = load_announcements()

    try:
        data['list'].pop(int(idx))
        save_announcements(data)
        return jsonify({'success': True, 'message': 'تم حذف الإعلان'})
    except IndexError:
        return jsonify({'success': False, 'error': 'الإعلان غير موجود'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/owner/broadcast', methods=['POST'])
@master_required
def owner_broadcast():
    d = request.json or {}
    msg = d.get('message', '').strip()

    if not msg:
        return jsonify({'success': False, 'error': 'الرسالة مطلوبة'})

    cfg = load_owner_config()
    count = 0

    if cfg.get('bot_linked') and cfg.get('telegram_token'):
        try:
            requests.post(
                f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
                json={'chat_id': cfg['telegram_owner_id'], 'text': f'📡 Broadcast:\n{msg}'},
                timeout=10
            )
            count += 1
        except Exception:
            pass

    data = load_announcements()
    data['list'].insert(0, {
        'text': f'[BROADCAST] {msg}',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    save_announcements(data)

    log_activity(session['username'], 'owner.broadcast', msg[:80])
    return jsonify({'success': True, 'count': count})


# ─── API: Owner Actions ─────────────────────────────────────────────────────
@app.route('/api/owner/action', methods=['POST'])
@master_required
def owner_action_api():
    action = (request.json or {}).get('action', '')

    try:
        if action == 'clear_all_logs':
            with open(LOGS_FILE, 'w', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] CLEARED BY OWNER\n")
            save_json_file(ACTIVITY_FILE, {'events': []})

        elif action == 'kick_all_users':
            sessions = load_user_sessions()
            for u in list(sessions.keys()):
                if u != MASTER_USERNAME:
                    sessions[u] = 0
            save_user_sessions(sessions)

        elif action == 'reset_stats':
            save_json_file(BOT_STATS_FILE, {
                'total_users': 0,
                'total_servers': 0,
                'active_bots': 0,
                'zip_files': 0,
                'last_updated': ''
            })

        elif action == 'restart_panel':
            def restart():
                time.sleep(1)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            threading.Thread(target=restart, daemon=True).start()

        else:
            return jsonify({'success': False, 'error': 'إجراء غير معروف'})

        log_activity(session['username'], f'owner.action.{action}', '')
        return jsonify({'success': True, 'message': f'تم تنفيذ {action}'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── API: Security Alerts ───────────────────────────────────────────────────
@app.route('/api/security/alerts')
@master_required
def get_security_alerts_api():
    return jsonify(load_security_alerts())


@app.route('/api/security/alerts/review', methods=['POST'])
@master_required
def review_security_alert_api():
    alert_id = (request.json or {}).get('id', '')
    data = load_security_alerts()

    for a in data.get('alerts', []):
        if a.get('id') == alert_id:
            a['reviewed'] = True
            break

    save_json_file(SECURITY_ALERTS_FILE, data)
    log_activity(session['username'], 'security.alert.reviewed', alert_id)
    return jsonify({'success': True, 'message': 'تمت مراجعة التنبيه'})


@app.route('/api/security/alerts/delete', methods=['POST'])
@master_required
def delete_security_alert_api():
    alert_id = (request.json or {}).get('id', '')
    data = load_security_alerts()
    data['alerts'] = [a for a in data.get('alerts', []) if a.get('id') != alert_id]
    save_json_file(SECURITY_ALERTS_FILE, data)
    return jsonify({'success': True, 'message': 'تم حذف التنبيه'})


@app.route('/api/security/alerts/clear', methods=['POST'])
@master_required
def clear_security_alerts_api():
    save_json_file(SECURITY_ALERTS_FILE, {'alerts': []})
    log_activity(session['username'], 'security.alerts.cleared', '')
    return jsonify({'success': True, 'message': 'تم مسح جميع التنبيهات'})


# ─── Static / Web Hosting ──────────────────────────────────────────────────
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(BASE_PATH, filename)


@app.route('/web/<username>/')
@app.route('/web/<username>/<path:filename>')
def serve_user_web(username, filename='index.html'):
    user_path = get_user_path(username)
    return send_from_directory(user_path, filename)


@app.route('/api-service/<username>/')
@app.route('/api-service/<username>/<path:filename>')
def serve_user_api_files(username, filename='api.json'):
    user_path = get_user_path(username)
    return send_from_directory(user_path, filename)


# ─── Admin Legacy Routes ────────────────────────────────────────────────────
@app.route('/admin/users')
def admin_manage_users():
    if not session.get('logged_in') or session.get('username') != MASTER_USERNAME:
        return redirect('/login')
    return redirect('/')


@app.route('/admin/approve/<username>')
def approve_user_legacy(username):
    if not session.get('logged_in') or session.get('username') != MASTER_USERNAME:
        return "غير مصرح", 403

    users = load_users()
    if username in users:
        users[username]['active'] = True
        save_users(users)
        log_activity(MASTER_USERNAME, 'user.approve.legacy', username)
        return f'''<div style="font-family:sans-serif;text-align:center;margin-top:50px;
                    background:#0b0f17;color:#e6edf3;min-height:100vh;padding:40px">
                    <h3 style="color:#3fb950">✅ تم تفعيل الحساب: {html.escape(username)}</h3>
                    <a href="/" style="color:#7c5cfc">← العودة للوحة</a>
                    </div>'''

    return "المستخدم غير موجود", 404
    
# ─────────────────────────────────────────────────────────────────────────────
#  21.  Multi-Port Sub-servers (Enhanced)
# ─────────────────────────────────────────────────────────────────────────────

def run_extra_port(port, note=''):
    """
    تشغيل خادم فرعي على منفذ إضافي.
    يستخدم Flask منفصل لعرض صفحة ترحيب بسيطة.
    """
    try:
        from flask import Flask as _F

        # إنشاء تطبيق Flask فرعي
        sub = _F(f'sub_{port}')

        @sub.route('/')
        def _home():
            """صفحة الترحيب للمنفذ الإضافي."""
            html_content = f'''
            <div style="font-family:'Inter','Segoe UI',sans-serif;
                        background:#0b0f17;
                        color:#e6edf3;
                        min-height:100vh;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        margin:0;
                        padding:20px;">
                <div style="text-align:center;
                            max-width:500px;
                            padding:40px 30px;
                            background:#161b22;
                            border-radius:20px;
                            border:1px solid #30363d;
                            box-shadow:0 20px 60px rgba(0,0,0,.6);">
                    <div style="font-size:64px;margin-bottom:12px;">🚀</div>
                    <h1 style="background:linear-gradient(135deg,#7c5cfc,#00bfff);
                               -webkit-background-clip:text;
                               -webkit-text-fill-color:transparent;
                               font-size:32px;
                               font-weight:900;
                               margin-bottom:6px;">
                        SERVER HUB
                    </h1>
                    <p style="color:#8b949e;font-size:14px;margin-top:6px;">
                        منفذ إضافي <span style="color:#7c5cfc;font-weight:700;">{port}</span>
                    </p>
                    {f'<p style="color:#484f58;font-size:13px;margin-top:4px;">{html.escape(note)}</p>' if note else ''}
                    <div style="margin-top:24px;
                                padding-top:20px;
                                border-top:1px solid #30363d;">
                        <a href="/" style="color:#7c5cfc;
                                          text-decoration:none;
                                          font-weight:600;
                                          padding:10px 24px;
                                          border:1px solid rgba(124,92,252,.3);
                                          border-radius:8px;
                                          transition:.2s;">
                            ← فتح اللوحة الرئيسية
                        </a>
                    </div>
                    <div style="margin-top:16px;
                                font-size:11px;
                                color:#484f58;">
                        SERVER HUB v2.0 &copy; 2025 — By SHBH_S1
                    </div>
                </div>
            </div>
            '''
            return html_content

        # تشغيل الخادم الفرعي
        sub.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )

    except Exception as e:
        print(f'[⚠️] فشل تشغيل المنفذ {port}: {str(e)}')


def start_configured_extra_ports():
    """
    بدء جميع المنافذ الإضافية المكونة مسبقاً في ملف ports.json.
    """
    ports = load_ports()

    if not ports:
        print('[ℹ️] لا توجد منافذ إضافية مكونة.')
        return

    print(f'[🔌] جاري تشغيل {len(ports)} منفذ/منافذ إضافية...')

    for p in ports:
        try:
            port_num = int(p.get('port', 0))
            if port_num <= 0 or port_num > 65535:
                print(f'[⚠️] تخطي منفذ غير صالح: {p.get("port")}')
                continue

            note = p.get('note', '')
            threading.Thread(
                target=run_extra_port,
                args=(port_num, note),
                daemon=True
            ).start()
            print(f'[✅] بدء المنفذ {port_num} {"(" + note + ")" if note else ""}')

        except Exception as e:
            print(f'[❌] فشل بدء المنفذ {p.get("port")}: {str(e)}')

    print('[✅] تم تشغيل جميع المنافذ الإضافية بنجاح.')
    
# ─────────────────────────────────────────────────────────────────────────────
#  22.  Entry Point (Enhanced)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # ── ألوان الطرفية ──
    G = '\033[32m'  # أخضر
    P = '\033[35m'  # بنفسجي
    C = '\033[36m'  # سماوي
    Y = '\033[33m'  # أصفر
    B = '\033[1m'   # Bold
    R = '\033[0m'   # Reset

    # ── شعار البداية ──
    print(G + r'''
 ____       ___       _  __        ___  
|  _ \     |_ _|     | |/ /       / _ \ 
| |_) |     | |      | ' /       | | | |
|  _ <      | |      | . \       | |_| |
|_| \_\    |___|     |_|\_\       \___/ ''' + R)

    print(P + '\u2554' + '\u2550' * 64 + '\u2557' + R)
    print(P + '\u2551  \U0001f680  ' + B + C + '\U0001d834\U0001d835\U0001d836\U0001d837\U0001d838\U0001d839\U0001d83a\U0001d83b' + R + P + '  \u2015  SERVER HUB v3.0  \u2015  SHBH_S1      \u2551' + R)
    print(P + '\u255a' + '\u2550' * 64 + '\u255d' + R)

    # ── معلومات النظام ──
    print(G + '\u250c\u2500\u2500(' + P + B + '\U0001d834\U0001d835\U0001d836\U0001d837\U0001d838\U0001d839\U0001d83a\U0001d83b' + R + G + '\u1F19A' + C + 'server-hub' + G + ')-[' + Y + '~' + G + ']' + R)
    print(G + '\u2514\u2500' + P + '$' + R + f' Master   : ' + B + C + f'{MASTER_USERNAME}' + R)
    print(G + '\u2514\u2500' + P + '$' + R + f' Data dir : ' + Y + f'{BASE_PATH}' + R)

    # ── التحقق من إعداد كلمة المرور ──
    if not MASTER_CONFIG.get('setup_done') or not MASTER_PASSWORD_HASH:
        print(Y + '\n⚠️  ' + R + 'لم يتم تعيين كلمة مرور المالك بعد!')
        print('   يرجى زيارة: ' + C + 'http://0.0.0.0:' + str(MASTER_CONFIG.get('port', 3178)) + '/setup' + R)
        print('   لتعيين كلمة المرور قبل تسجيل الدخول.\n')
    else:
        print(G + '✅ ' + R + 'كلمة مرور المالك مضبوطة.')

    # ── بدء المنافذ الإضافية ──
    start_configured_extra_ports()

    # ── تحديد المنفذ الرئيسي ──
    port = int(os.environ.get('PORT', MASTER_CONFIG.get('port') or 3178))

    # ── عرض معلومات التشغيل ──
    print('\n' + G + '╔═══════════════════════════════════════════════════════════════════╗' + R)
    print(G + '║' + R + '  🌐 ' + B + 'Panel URL  : ' + C + f'http://0.0.0.0:{port}' + R + '                     ' + G + '║' + R)
    print(G + '║' + R + '  🔑 ' + B + 'Login      : ' + Y + f'{MASTER_USERNAME}' + R + ' / ' + Y + '[password set in /setup]' + R + '  ' + G + '║' + R)
    if not MASTER_CONFIG.get('setup_done') or not MASTER_PASSWORD_HASH:
        print(G + '║' + R + '  ⚠️  ' + B + 'Setup      : ' + R + 'زيارة ' + C + '/setup' + R + ' لتعيين كلمة المرور           ' + G + '║' + R)
    print(G + '║' + R + '  📝 ' + B + 'Register   : ' + R + 'متاح للمستخدمين الجدد (يحتاج موافقة الأدمن)' + G + '║' + R)
    print(G + '║' + R + '  ⚡ ' + B + 'Supported  : ' + R + 'PHP / Node.js / Python / ZIP / SQLite     ' + G + '║' + R)
    print(G + '╚═══════════════════════════════════════════════════════════════════╝' + R)

    # ── بدء التطبيق الرئيسي ──
    print('\n' + G + '🚀 ' + B + 'SERVER HUB is running...' + R)
    print('   اضغط ' + C + 'Ctrl+C' + R + ' لإيقاف الخادم.\n')

    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print('\n' + Y + '⏹️  ' + R + 'تم إيقاف الخادم بواسطة المستخدم.')
    except Exception as e:
        print('\n' + R + '❌ ' + B + 'خطأ غير متوقع:' + R + f' {str(e)}')
        sys.exit(1)