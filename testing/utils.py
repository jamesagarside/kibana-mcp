import sys
import subprocess

# ==============================================================================
# --- Utilities ---
# ==============================================================================
def print_info(msg):
    print(f"[INFO] {msg}")

def print_warning(msg):
    print(f"[WARNING] {msg}", file=sys.stderr)

def print_error(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)

def command_exists(cmd):
    """Checks if a command exists on the system PATH."""
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False 