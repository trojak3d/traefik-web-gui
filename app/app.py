#!/usr/bin/env python3
"""
Traefik Web GUI - Simple web interface for managing Traefik configs with authentication
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import os
import sys
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import yaml
import json
import hmac
import hashlib
import re
import subprocess

# Configuration
CONFIG_DIR = os.getenv('TRAEFIK_CONFIG_DIR', '/etc/traefik/dynamic')
ALLOWED_EXTENSIONS = {'yml', 'yaml'}
FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._\-]+\.(yml|yaml)$')  # Strict filename validation
LOG_FILE = '/var/log/traefik-web-gui.log'
PORT = int(os.getenv('GUI_PORT', '5000'))
HOST = os.getenv('GUI_HOST', '0.0.0.0')
USERNAME = os.getenv('GUI_USERNAME', 'admin')
DATA_DIR = os.getenv('GUI_DATA_DIR', '/var/lib/traefik-web-gui')
PASSWORD_FILE = os.path.join(DATA_DIR, 'password.json')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Generate or load the secret key securely
SECRET_KEY_FILE = os.path.join(DATA_DIR, '.secret_key')

def get_or_create_secret_key():
    """Get existing secret key or generate a new cryptographically secure one"""
    if os.path.exists(SECRET_KEY_FILE):
        try:
            with open(SECRET_KEY_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading secret key: {e}")
    
    # Generate a new secure random key
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    try:
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(secret_key)
        # Restrict permissions to owner only
        os.chmod(SECRET_KEY_FILE, 0o600)
        logger.info("Generated new secure secret key")
    except Exception as e:
        logger.error(f"Error saving secret key: {e}")
        # Fall back to environment variable if available
        return os.getenv('SECRET_KEY', secret_key)
    
    return secret_key

# Allow explicit override via SECRET_KEY environment variable for production deployments
app.secret_key = os.getenv('SECRET_KEY') or get_or_create_secret_key()

# Ensure data directory exists and is writable
os.makedirs(DATA_DIR, exist_ok=True)
try:
    # Restrict permissions to owner only for security
    os.chmod(DATA_DIR, 0o700)
except:
    pass  # May fail in containers with restrictions, but directory should still work

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def setup_required(f):
    """Decorator to require setup completion"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_setup_complete():
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function

def is_setup_complete():
    """Check if initial setup has been completed"""
    return os.path.exists(PASSWORD_FILE)

# Default password for initial setup
DEFAULT_PASSWORD = 'admin'

def verify_password(provided_password, stored_hash):
    """Verify password against hash using constant-time comparison"""
    if not stored_hash:
        # During initial setup, compare against default password using constant-time comparison
        # This prevents timing attacks on the default password
        return hmac.compare_digest(provided_password.encode('utf-8'), DEFAULT_PASSWORD.encode('utf-8'))
    # After setup, use proper hash comparison
    return check_password_hash(stored_hash, provided_password)

def get_password_hash():
    """Get stored password hash"""
    if not is_setup_complete():
        return None  # No hash yet, we'll use direct comparison
    
    try:
        with open(PASSWORD_FILE, 'r') as f:
            data = json.load(f)
            return data.get('hash', '')
    except:
        return ''

def save_password_hash(password_hash):
    """Save password hash to file"""
    try:
        with open(PASSWORD_FILE, 'w') as f:
            json.dump({'hash': password_hash, 'updated': datetime.now().isoformat()}, f)
        logger.info("Password updated")
    except Exception as e:
        logger.error(f"Error saving password: {e}")
        return False
    return True

def allowed_file(filename):
    """Check if file has allowed extension and matches safe filename pattern"""
    if not filename or '.' not in filename:
        return False
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    return FILENAME_PATTERN.match(filename) is not None and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup - change default password"""
    if is_setup_complete() and 'username' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate that username matches the configured username
        if username != USERNAME:
            logger.warning(f"Setup attempt with wrong username: {username}")
            return render_template('setup.html', error=f'Username must be: {USERNAME}'), 401
        
        # Validate old password using our custom verifier
        if not verify_password(old_password, get_password_hash()):
            logger.warning(f"Failed setup attempt - wrong password")
            return render_template('setup.html', error='Invalid current password'), 401
        
        # Validate new password
        if not new_password or new_password != confirm_password:
            return render_template('setup.html', error='Passwords do not match'), 400
        
        if len(new_password) < 6:
            return render_template('setup.html', error='Password must be at least 6 characters'), 400
        
        # Save new password
        new_hash = generate_password_hash(new_password)
        if save_password_hash(new_hash):
            session['username'] = USERNAME
            logger.info(f"Setup completed for user: {USERNAME}")
            return redirect(url_for('index'))
        else:
            return render_template('setup.html', error='Failed to save password'), 500
    
    return render_template('setup.html', setup_required=not is_setup_complete())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if not is_setup_complete():
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if username == USERNAME and verify_password(password, get_password_hash()):
            session['username'] = username
            logger.info(f"User logged in: {username}")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return render_template('login.html', error='Invalid credentials'), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    if 'username' in session:
        logger.info(f"User logged out: {session['username']}")
        session.pop('username', None)
    return redirect(url_for('login'))

def get_files_list():
    """Get list of YAML files in config directory"""
    if not os.path.exists(CONFIG_DIR):
        return []
    
    files = []
    try:
        for filename in os.listdir(CONFIG_DIR):
            filepath = os.path.join(CONFIG_DIR, filename)
            if os.path.isfile(filepath) and allowed_file(filename):
                try:
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'readable': os.access(filepath, os.R_OK),
                        'writable': os.access(filepath, os.W_OK)
                    })
                except OSError as e:
                    logger.warning(f"Error accessing file {filename}: {e}")
        
        return sorted(files, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return []

@app.route('/')
@login_required
@setup_required
def index():
    """Main page - file list"""
    files = get_files_list()
    username = session.get('username', 'User')
    return render_template('index.html', files=files, config_dir=CONFIG_DIR, username=username)

@app.route('/api/files')
@login_required
@setup_required
def api_files():
    """API endpoint - get file list"""
    return jsonify({'files': get_files_list()})

@app.route('/api/file/<filename>')
@login_required
@setup_required
def api_read_file(filename):
    """API endpoint - read file"""
    if not allowed_file(filename) or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(CONFIG_DIR, secure_filename(filename))
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return jsonify({
            'name': filename,
            'content': content,
            'size': os.path.getsize(filepath),
            'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return jsonify({'error': 'Error reading file'}), 500

@app.route('/api/file/<filename>', methods=['POST'])
@login_required
@setup_required
def api_save_file(filename):
    """API endpoint - save file"""
    if not allowed_file(filename) or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(CONFIG_DIR, secure_filename(filename))
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        content = request.json.get('content', '')
        
        # Validate YAML
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            return jsonify({'error': f'Invalid YAML: {str(e)}'}), 400
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        logger.info(f"File updated by {session.get('username', 'unknown')}: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'File {filename} saved successfully',
            'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        return jsonify({'error': 'Error saving file'}), 500

@app.route('/api/file', methods=['POST'])
@login_required
@setup_required
def api_create_file():
    """API endpoint - create file"""
    try:
        filename = request.json.get('filename', '')
        content = request.json.get('content', '')
        
        if not filename or not allowed_file(filename):
            return jsonify({'error': 'Invalid filename (must end in .yml or .yaml)'}), 400
        
        filepath = os.path.join(CONFIG_DIR, secure_filename(filename))
        
        try:
            # Validate YAML
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                logger.warning(f"Invalid YAML submitted for file creation: {e}")
                return jsonify({'error': 'Invalid YAML format'}), 400
        
            # Use exclusive creation mode (x) to prevent TOCTOU race condition
            # This atomically fails if the file already exists
            with open(filepath, 'x') as f:
                f.write(content)
        
            logger.info(f"File created by {session.get('username', 'unknown')}: {filename}")
        
            return jsonify({'success': True, 'message': f'File {filename} created successfully'})
        except FileExistsError:
            return jsonify({'error': 'File already exists'}), 400
        except OSError as e:
            logger.error(f"Error creating file {filename}: {e}")
            return jsonify({'error': 'Error creating file'}), 500
        except Exception as e:
            logger.error(f"Error creating file {filename}: {e}")
            return jsonify({'error': 'Error creating file'}), 500
    except Exception as e:
        logger.error(f"Error processing file creation request: {e}")
        return jsonify({'error': 'Error creating file'}), 500

@app.route('/api/file/<filename>', methods=['DELETE'])
@login_required
@setup_required
def api_delete_file(filename):
    """API endpoint - delete file"""
    if not allowed_file(filename) or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(CONFIG_DIR, secure_filename(filename))
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        os.remove(filepath)
        logger.info(f"File deleted by {session.get('username', 'unknown')}: {filename}")
        return jsonify({'success': True, 'message': f'File {filename} deleted'})
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        return jsonify({'error': 'Error deleting file'}), 500
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
@login_required
@setup_required
def api_status():
    """API endpoint - status"""
    try:
        file_count = len([f for f in os.listdir(CONFIG_DIR) if os.path.isfile(os.path.join(CONFIG_DIR, f)) and allowed_file(f)])
    except:
        file_count = 0
    
    return jsonify({
        'config_dir': CONFIG_DIR,
        'writable': os.access(CONFIG_DIR, os.W_OK),
        'file_count': file_count,
        'username': session.get('username', 'unknown')
    })

@app.route('/api/traefik/status', methods=['GET'])
@login_required
@setup_required
def api_traefik_status():
    """API endpoint - check if traefik service is running"""
    try:
        result = subprocess.run(
            ['sudo', '/bin/systemctl', 'is-active', 'traefik'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        is_running = result.returncode == 0
        return jsonify({
            'running': is_running,
            'status': result.stdout.strip() if is_running else result.stderr.strip()
        })
    except Exception as e:
        logger.error(f"Error checking traefik status: {e}")
        return jsonify({'running': False, 'status': 'unknown'}), 500

@app.route('/api/traefik/restart', methods=['POST'])
@login_required
@setup_required
def api_restart_traefik():
    """API endpoint - restart traefik service"""
    try:
        username = session.get('username', 'unknown')
        logger.info(f"Traefik restart requested by {username}")
        
        result = subprocess.run(
            ['sudo', '/bin/systemctl', 'restart', 'traefik'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Traefik restarted successfully by {username}")
            return jsonify({
                'success': True,
                'message': 'Traefik service restarted successfully'
            })
        else:
            error_msg = result.stderr if result.stderr else 'Unknown error'
            logger.error(f"Failed to restart traefik: {error_msg}")
            return jsonify({
                'error': f'Failed to restart traefik: {error_msg}'
            }), 500
    except subprocess.TimeoutExpired:
        logger.error("Traefik restart timeout")
        return jsonify({'error': 'Restart operation timed out'}), 500
    except Exception as e:
        logger.error(f"Error restarting traefik: {e}")
        return jsonify({'error': f'Error restarting traefik: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting Traefik Web GUI on {HOST}:{PORT}")
    logger.info(f"Config directory: {CONFIG_DIR}")
    logger.info(f"Setup complete: {is_setup_complete()}")
    
    if not os.path.exists(CONFIG_DIR):
        logger.error(f"Config directory not found: {CONFIG_DIR}")
        sys.exit(1)
    
    app.run(host=HOST, port=PORT, debug=False)
