from flask import Flask, request, jsonify, send_from_directory, Response, send_file
import subprocess
from pathlib import Path
import json
import tempfile
import sys
import uuid
import time
import threading
import signal
import psutil
import logging
from typing import Optional, Dict, Any
from werkzeug.utils import secure_filename

from .config import Config
from ..utils.dialogs import FileDialog

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='')

# Initialize configuration
config = Config()

# Global process tracking
current_process: Optional[subprocess.Popen] = None

# Load paths from config
HASHCAT_PATH = Path(config.paths.hashcat_path)
HASHCAT_DIR = HASHCAT_PATH.parent
WORDLISTS_PATH = Path(config.paths.wordlists_path)
RULES_PATH = Path(config.paths.rules_path)
TEMP_DIR = Path(config.paths.temp_path)
POTFILE_PATH = Path(config.paths.potfile_path)

# Default hash file name
DEFAULT_HASH_FILE = "crackme.txt"

# Initialize GUI dialog
file_dialog = FileDialog()

def load_hash_types() -> Dict[str, Any]:
    """Load hash types from hash_types.txt file"""
    hash_types = {}
    try:
        hash_types_path = Path(config.paths.hash_types_path)
        with hash_types_path.open('r') as f:
            for line in f:
                if line.strip():
                    mode_id, name, category = line.strip().split('|')
                    hash_types[mode_id] = {
                        "name": name,
                        "category": category,
                        "example": get_example_hash(mode_id)
                    }
    except Exception as e:
        logger.error(f"Error loading hash types: {e}")
        # Fallback to basic hash types
        hash_types = {
            "0": {"name": "MD5", "category": "Raw Hash", "example": "8743b52063cd84097a65d1633f5c74f5"},
            "100": {"name": "SHA1", "category": "Raw Hash", "example": "b89eaac7e61417341b710b727768294d0e6a277b"},
            "1000": {"name": "NTLM", "category": "Operating System", "example": "b4b9b02e6f09a9bd760f388b67351e2b"}
        }
    return hash_types

def save_config(config):
    """Save configuration to config file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {str(e)}", file=sys.stderr)
        return False

# Update global variables from config
config = load_config()
HASHCAT_PATH = config['hashcatPath']
HASHCAT_DIR = os.path.dirname(HASHCAT_PATH)
WORDLISTS_PATH = config['wordlistsPath']
RULES_PATH = config['rulesPath']
POTFILE_PATH = config['potfilePath']
TEMP_DIR = config['tempPath']

def load_hash_types():
    """Load hash types from hash_types.txt file"""
    hash_types = {}
    try:
        with open('hash_types.txt', 'r') as f:
            for line in f:
                if line.strip():
                    mode_id, name, category = line.strip().split('|')
                    hash_types[mode_id] = {
                        "name": name,
                        "category": category,
                        "example": get_example_hash(mode_id)
                    }
    except Exception as e:
        print(f"Error loading hash types: {str(e)}", file=sys.stderr)
        # Fallback to basic hash types if file can't be loaded
        hash_types = {
            "0": {"name": "MD5", "category": "Raw Hash", "example": "8743b52063cd84097a65d1633f5c74f5"},
            "100": {"name": "SHA1", "category": "Raw Hash", "example": "b89eaac7e61417341b710b727768294d0e6a277b"},
            "1000": {"name": "NTLM", "category": "Operating System", "example": "b4b9b02e6f09a9bd760f388b67351e2b"}
        }
    return hash_types

def get_example_hash(mode_id):
    """Return an example hash for the given mode ID"""
    examples = {
        "0": "8743b52063cd84097a65d1633f5c74f5",
        "100": "b89eaac7e61417341b710b727768294d0e6a277b",
        "1000": "b4b9b02e6f09a9bd760f388b67351e2b",
        "1800": "$6$52450745$k5ka2p8bFuSmoVT1tzOyyuaREkkKBcCNqoDKzYiJL9RaE8yMnPgh2XzzF0NDrUhgrcLwg78xs1w5pJiypEdFX/",
        "3200": "$2a$05$LhayLxezLhK1LhWvKxCyLOj0j1u.Kj0jZ0pEmm134uzrQlFvQJLF6"
    }
    return examples.get(mode_id, "Example hash not available")

# Load hash types on startup
HASH_TYPES = load_hash_types()

class PotfileMonitor:
    def __init__(self, potfile_path):
        self.potfile_path = potfile_path
        self.last_position = 0
        self.last_size = 0
        self._stop = False

    def start_monitoring(self, callback):
        """Monitor the potfile for changes and call callback with new lines"""
        while not self._stop:
            try:
                if os.path.exists(self.potfile_path):
                    current_size = os.path.getsize(self.potfile_path)
                    if current_size > self.last_size:
                        with open(self.potfile_path, 'r') as f:
                            f.seek(self.last_position)
                            new_lines = f.readlines()
                            for line in new_lines:
                                callback(line.strip())
                            self.last_position = f.tell()
                        self.last_size = current_size
            except Exception as e:
                print(f"Error monitoring potfile: {str(e)}", file=sys.stderr)
            time.sleep(0.1)  # Check every 100ms

    def stop(self):
        """Stop monitoring"""
        self._stop = True

@app.route('/api/paths')
def get_paths():
    """Return paths for frontend use"""
    return jsonify({
        'hashcat': HASHCAT_PATH,
        'wordlists': WORDLISTS_PATH,
        'rules': RULES_PATH,
        'temp': TEMP_DIR
    })

def get_directory_files(directory: Path) -> list[str]:
    """Get list of files in directory"""
    try:
        files = [f.name for f in directory.iterdir() if f.is_file()]
        return sorted(files)
    except Exception as e:
        logger.error(f"Error reading directory {directory}: {e}")
        return []

def cleanup_temp_files() -> None:
    """Clean up old temporary files"""
    try:
        for file_path in TEMP_DIR.glob('hashcat_*'):
            if file_path.is_file():
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error during temp file cleanup: {e}")

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/hash_types')
def get_hash_types():
    return jsonify(HASH_TYPES)

@app.route('/api/wordlists')
def get_wordlists():
    return jsonify(get_directory_files(WORDLISTS_PATH))

@app.route('/api/rules')
def get_rules():
    return jsonify(get_directory_files(RULES_PATH))

@app.route('/api/save_hashes', methods=['POST'])
def save_hashes():
    """Save hashes to a temporary file and return the file path"""
    data = request.json
    hashes = data.get('hashes')
    
    if not hashes:
        return jsonify({"error": "No hashes provided"}), 400
    
    try:
        # Create a temporary file in Windows temp directory
        temp_path = os.path.join(TEMP_DIR, DEFAULT_HASH_FILE)
        with open(temp_path, 'w') as f:
            f.write(hashes)
        return jsonify({"file": temp_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop_hashcat', methods=['POST'])
def stop_hashcat():
    """Stop the currently running hashcat process"""
    global current_process
    try:
        if current_process:
            # Try to terminate hashcat gracefully first
            if sys.platform == 'win32':
                # On Windows, we need to send Ctrl+C signal
                current_process.send_signal(signal.CTRL_C_EVENT)
            else:
                current_process.terminate()
            
            # Give it a moment to stop gracefully
            time.sleep(1)
            
            # If still running, force kill
            if current_process.poll() is None:
                # Kill the process and any children
                parent = psutil.Process(current_process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    child.kill()
                parent.kill()
            
            current_process = None
            return jsonify({"status": "success", "message": "Hashcat stopped"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "No running process"}), 404

def validate_hashcat_args(args):
    """Validate hashcat command arguments for security"""
    # List of allowed hashcat arguments
    allowed_args = {
        '-m', '-a', '-w', '--status', '--hwmon-disable', '-O', '-r',
        # Add other allowed hashcat arguments here
    }
    
    # Check each argument
    for arg in args:
        if arg == args[0]:  # Skip executable path
            continue
        if arg.startswith('-'):
            arg_base = arg.split('=')[0] if '=' in arg else arg
            if arg_base not in allowed_args:
                raise ValueError(f"Invalid argument: {arg}")
        elif '..' in arg or '~' in arg:  # Prevent directory traversal
            raise ValueError(f"Invalid path in argument: {arg}")
    
    return True

@app.route('/api/run_hashcat', methods=['POST'])
def run_hashcat():
    global current_process
    
    data = request.json
    hash_type = data.get('hashType')
    hashes = data.get('hashes')
    wordlist = data.get('wordlist')
    ruleset = data.get('ruleset')
    custom_command = data.get('customCommand')
    hash_file = data.get('hashFile')
    
    if not hash_type or not (hashes or hash_file) or not wordlist:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Use provided hash file or create a new one
        if not hash_file:
            hash_file = os.path.join(TEMP_DIR, DEFAULT_HASH_FILE)
            with open(hash_file, 'w') as f:
                f.write(hashes)
        
        if custom_command:
            # Split the custom command and validate
            cmd = custom_command.split()
            
            # Ensure first argument is hashcat
            if not cmd[0].lower().endswith('hashcat.exe'):
                raise ValueError("Invalid executable specified")
            
            # Replace with configured hashcat path
            cmd[0] = HASHCAT_PATH
            
            # Validate and sanitize paths
            for i, arg in enumerate(cmd):
                if arg == "temp_hashes.txt" or arg == "crackme.txt":
                    cmd[i] = hash_file
                elif arg.startswith("wordlists/"):
                    wordlist_path = os.path.join(WORDLISTS_PATH, arg.replace("wordlists/", ""))
                    if not os.path.normpath(wordlist_path).startswith(os.path.normpath(WORDLISTS_PATH)):
                        raise ValueError("Invalid wordlist path")
                    cmd[i] = wordlist_path
                elif arg.startswith("rules/"):
                    rule_path = os.path.join(RULES_PATH, arg.replace("rules/", ""))
                    if not os.path.normpath(rule_path).startswith(os.path.normpath(RULES_PATH)):
                        raise ValueError("Invalid rule path")
                    cmd[i] = rule_path
            
            # Validate all arguments
            validate_hashcat_args(cmd)
        else:
            # Default command construction
            cmd = [
                HASHCAT_PATH,
                "-w2",
                "-m", hash_type,
                "-a", "0",
                "--status",
                "--hwmon-disable",
                "-O",
                hash_file,
                os.path.join(WORDLISTS_PATH, wordlist)
            ]

            # Add ruleset if specified
            if ruleset:
                rule_path = os.path.join(RULES_PATH, ruleset)
                if not os.path.normpath(rule_path).startswith(os.path.normpath(RULES_PATH)):
                    raise ValueError("Invalid rule path")
                cmd.extend(["-r", rule_path])

        # Validate final command
        validate_hashcat_args(cmd)
        
        print(f"Executing command: {' '.join(cmd)}", file=sys.stderr)
        
        # Run hashcat with process group
        if sys.platform == 'win32':
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=HASHCAT_DIR,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=HASHCAT_DIR,
                preexec_fn=os.setsid
            )

        current_process = process

        # Set up potfile monitoring
        monitor = PotfileMonitor(POTFILE_PATH)
        output_queue = []

        def potfile_callback(line):
            output_queue.append(json.dumps({"type": "cracked", "data": line}) + "\n")
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=monitor.start_monitoring,
            args=(potfile_callback,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        def generate():
            try:
                while True:
                    # Check for any cracked hashes first
                    while output_queue:
                        yield output_queue.pop(0)

                    # Then check hashcat output
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        yield json.dumps({"type": "output", "data": output.strip()}) + "\n"
                
                stderr_output = process.stderr.read()
                if stderr_output:
                    yield json.dumps({"type": "error", "data": stderr_output.strip()}) + "\n"
                
                rc = process.poll()
                if rc != 0:
                    yield json.dumps({"type": "error", "data": f"Process exited with code {rc}"}) + "\n"
            finally:
                monitor.stop()
                monitor_thread.join(timeout=1)
        
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        print(f"Error executing hashcat: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_config')
def get_config():
    """Return current configuration"""
    return jsonify(load_config())

@app.route('/api/save_config', methods=['POST'])
def save_configuration():
    """Save new configuration"""
    try:
        config = request.json
        if save_config(config):
            # Update global variables
            global HASHCAT_PATH, HASHCAT_DIR, WORDLISTS_PATH, RULES_PATH, POTFILE_PATH, TEMP_DIR
            HASHCAT_PATH = config['hashcatPath']
            HASHCAT_DIR = os.path.dirname(HASHCAT_PATH)
            WORDLISTS_PATH = config['wordlistsPath']
            RULES_PATH = config['rulesPath']
            POTFILE_PATH = config['potfilePath']
            TEMP_DIR = config['tempPath']
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to save configuration"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def create_file_dialog(title, filetypes=None, initialdir=None):
    """Create a file dialog with proper thread handling"""
    try:
        root = get_tk_root()
        if not root:
            raise Exception("Could not create Tkinter window")

        if initialdir is None:
            initialdir = os.path.expanduser('~')

        # Use a queue to get the result from the main thread
        result_queue = queue.Queue()
        
        def show_dialog():
            try:
                path = filedialog.askopenfilename(
                    parent=root,
                    title=title,
                    filetypes=filetypes if filetypes else [('All files', '*.*')],
                    initialdir=initialdir
                )
                result_queue.put(path)
            except Exception as e:
                result_queue.put(None)
                print(f"Error in file dialog: {str(e)}", file=sys.stderr)

        root.after(0, show_dialog)
        file_path = result_queue.get(timeout=300)  # 5 minute timeout
        
        if file_path:
            return os.path.normpath(file_path)
        return None
    except Exception as e:
        print(f"Error in file dialog: {str(e)}", file=sys.stderr)
        raise

def create_directory_dialog(title, initialdir=None):
    """Create a directory dialog with proper thread handling"""
    try:
        root = get_tk_root()
        if not root:
            raise Exception("Could not create Tkinter window")

        if initialdir is None:
            initialdir = os.path.expanduser('~')

        # Use a queue to get the result from the main thread
        result_queue = queue.Queue()
        
        def show_dialog():
            try:
                path = filedialog.askdirectory(
                    parent=root,
                    title=title,
                    initialdir=initialdir
                )
                result_queue.put(path)
            except Exception as e:
                result_queue.put(None)
                print(f"Error in directory dialog: {str(e)}", file=sys.stderr)

        root.after(0, show_dialog)
        dir_path = result_queue.get(timeout=300)  # 5 minute timeout
        
        if dir_path:
            return os.path.normpath(dir_path)
        return None
    except Exception as e:
        print(f"Error in directory dialog: {str(e)}", file=sys.stderr)
        raise

@app.route('/api/file_dialog', methods=['POST'])
def file_dialog():
    try:
        data = request.get_json()
        file_type = data.get('type', '')
        input_id = data.get('inputId', '')

        # Set up file type filters
        if file_type == 'exe':
            filetypes = [('Executable files', '*.exe')]
        elif file_type == 'txt':
            filetypes = [('Text files', '*.txt')]
        elif file_type == 'potfile':
            filetypes = [('Potfiles', '*.potfile'), ('All files', '*.*')]
        else:
            filetypes = [('All files', '*.*')]

        # Open the file dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        file_path = filedialog.askopenfilename(
            title=f'Select {file_type.upper()} file',
            filetypes=filetypes
        )
        
        root.destroy()

        if file_path:
            return jsonify({'path': file_path})
        return jsonify({'error': 'No file selected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/directory_dialog', methods=['POST'])
def directory_dialog():
    try:
        data = request.get_json()
        input_id = data.get('inputId', '')

        # Open the directory dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        dir_path = filedialog.askdirectory(
            title='Select Directory'
        )
        
        root.destroy()

        if dir_path:
            return jsonify({'path': dir_path})
        return jsonify({'error': 'No directory selected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_potfile', methods=['POST'])
def clear_potfile():
    """Clear the contents of the potfile"""
    try:
        # Check if potfile exists
        if not os.path.exists(POTFILE_PATH):
            return jsonify({"success": True, "message": "Potfile doesn't exist"})
        
        # Clear the potfile
        with open(POTFILE_PATH, 'w') as f:
            f.write('')  # Write empty string to clear the file
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error clearing potfile: {str(e)}", file=sys.stderr)
        return jsonify({"success": False, "error": str(e)})

@app.route('/<path:filename>.png')
def serve_png(filename):
    return send_file(f'{filename}.png', mimetype='image/png')

@app.route('/styles.css')
def serve_css():
    return send_file('styles.css', mimetype='text/css')

@app.teardown_request
def cleanup_request(exception=None):
    """Clean up temporary files after the request is done"""
    cleanup_temp_files()

if __name__ == '__main__':
    print(f"Starting server with following paths:")
    print(f"Hashcat: {HASHCAT_PATH}")
    print(f"Wordlists: {WORDLISTS_PATH}")
    print(f"Rules: {RULES_PATH}")
    print(f"Temp Directory: {TEMP_DIR}")
    print(f"Default Hash File: {os.path.join(TEMP_DIR, DEFAULT_HASH_FILE)}")
    
    # Initial cleanup of temp files
    cleanup_temp_files()
    
    # Run Flask with debug mode (Tkinter is now handled in a separate thread)
    app.run(host='0.0.0.0', port=5000, debug=True) 