import subprocess
import time
import sys
import os


PYTHON_EXEC = sys.executable

SCRIPTS = [
    "event_monitor.py",
    "defender_monitor.py",
    "client_heartbeat.py",
    "software_monitor.py",
    "port_monitor.py"
]

def start_script(script_name):
    try:
        subprocess.Popen([PYTHON_EXEC, script_name])
        print(f"[INFO] {script_name} başlatıldı.")
    except Exception as e:
        print(f"[ERROR] {script_name} başlatılamadı: {e}")

def main():
    print("[INFO] Servis başlatılıyor...")

    start_script("hardware_monitor.py")

    print("[INFO] 30 saniye bekleniyor...")
    time.sleep(30)

    for script in SCRIPTS:
        start_script(script)

    print("[INFO] Tüm scriptler başlatıldı. Servis çalışıyor...")

if __name__ == "__main__":
    main()
