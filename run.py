"""
run.py - Starts the whole system with ONE command:   python run.py

Starts (each as a separate operating-system process):
    1. Mosquitto MQTT broker  (only if it is not already running)
    2. Cloud server
    3. Fog node A, Fog node B, Fog node C
    4. Sensor simulator (9 IoT sensors)
    5. Web dashboard  ->  http://127.0.0.1:5000

Options:
    --keep-data   do not wipe the previous run's databases
    --no-browser  do not open the browser automatically
"""

import glob
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser

import config

PROCESSES = [
    ("CLOUD", ["-m", "cloud.cloud_server"]),
    ("FOG-A", ["-m", "fog.fog_node", "A"]),
    ("FOG-B", ["-m", "fog.fog_node", "B"]),
    ("FOG-C", ["-m", "fog.fog_node", "C"]),
    ("SENSORS", ["-m", "sensors.simulator"]),
    ("WEB", ["-m", "web.app"]),
]

MOSQUITTO_PATHS = [
    r"C:\Program Files\mosquitto\mosquitto.exe",
    r"C:\Program Files (x86)\mosquitto\mosquitto.exe",
    "/usr/sbin/mosquitto", "/usr/local/sbin/mosquitto", "/opt/homebrew/sbin/mosquitto",
]


def broker_running():
    try:
        with socket.create_connection((config.MQTT_HOST, config.MQTT_PORT), timeout=1):
            return True
    except OSError:
        return False


def start_broker():
    exe = shutil.which("mosquitto") or next((p for p in MOSQUITTO_PATHS if os.path.exists(p)), None)
    if not exe:
        print("\n  Mosquitto was not found and no broker is running on port 1883.")
        print("  Install it from https://mosquitto.org/download/ and run this script again.\n")
        sys.exit(1)
    print(f"[RUN] starting Mosquitto broker: {exe}")
    proc = subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if broker_running():
            return proc
        time.sleep(0.25)
    print("[RUN] Mosquitto did not start. Try running it manually: mosquitto -v")
    sys.exit(1)


def main():
    os.chdir(config.BASE_DIR)
    os.makedirs(config.RUNTIME_DIR, exist_ok=True)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    if "--keep-data" not in sys.argv:
        for f in glob.glob(os.path.join(config.RUNTIME_DIR, "*.db")):
            os.remove(f)

    broker = None
    if broker_running():
        print("[RUN] MQTT broker already running on port 1883")
    else:
        broker = start_broker()

    children = []
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    for name, args in PROCESSES:
        print(f"[RUN] starting {name}")
        children.append((name, subprocess.Popen([sys.executable] + args, cwd=config.BASE_DIR, env=env)))
        time.sleep(0.4)

    url = f"http://{config.WEB_HOST}:{config.WEB_PORT}"
    print(f"\n[RUN] all components started. Dashboard: {url}   (press Ctrl+C to stop)\n")
    if "--no-browser" not in sys.argv:
        time.sleep(2)
        webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
            for name, p in children:
                if p.poll() is not None and not getattr(p, "_reported", False):
                    p._reported = True
                    print(f"[RUN] WARNING: {name} stopped (exit code {p.returncode})")
    except KeyboardInterrupt:
        print("\n[RUN] stopping ...")
    finally:
        for _, p in children:
            if p.poll() is None:
                p.terminate()
        for _, p in children:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        if broker:
            broker.terminate()
        print("[RUN] stopped.")


if __name__ == "__main__":
    main()
