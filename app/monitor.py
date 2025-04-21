import time
import logging
import json
from ping3 import ping
from threading import Thread
from tinydb import TinyDB, Query
import atexit
import os
from statistics import mean

# === CONFIGURATION ===

CONFIG_PATH = os.path.join("app", "config", "cameras.json")
LOG_DB = "status_log.json"
LOG_FILE = "camera_events.log"

# Load camera info (IP + group)
def load_camera_config():
    try:
        with open(CONFIG_PATH) as f:
            raw = json.load(f)
        cameras = {name: val["ip"] for name, val in raw.items()}
        camera_groups = {name: val["group"] for name, val in raw.items()}
        return cameras, camera_groups
    except Exception as e:
        logging.error(f"Error loading cameras configuration: {e}")
        return {}, {}

# Initial load
cameras, camera_groups = load_camera_config()

# Status data for each camera
status_data = {
    name: {
        "online": None,
        "last_seen": None,
        "online_since": None,
        "latency": None,
        "uptime": 0.0,
    }
    for name in cameras
}

# Ping history for charts (last 100)
ping_history = {name: [] for name in cameras}

# TinyDB for event logging
db = TinyDB(LOG_DB)

# Optional file-based log
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === UTILITY ===

def was_recently_logged(camera_name, status, seconds=3):
    """Prevent duplicate log entries within X seconds"""
    Camera = Query()
    entries = db.search((Camera.camera == camera_name) & (Camera.status == status))
    if not entries:
        return False
    last_entry = sorted(entries, key=lambda x: x["timestamp"])[-1]
    last_time = time.mktime(time.strptime(last_entry["timestamp"], "%Y-%m-%d %H:%M:%S"))
    return time.time() - last_time < seconds

# === MONITORING ===

def update_status():
    global cameras, camera_groups

    # Reload cameras.json dynamically (allows editing on the fly)
    cameras, camera_groups = load_camera_config()

    now = time.strftime('%Y-%m-%d %H:%M:%S')

    for name, ip in cameras.items():
        try:
            response = ping(ip, timeout=1)
        except OSError:
            response = None

        is_up = response is not None
        latency_ms = round(response * 1000, 2) if is_up else None

        entry = status_data.setdefault(name, {
            "online": None,
            "last_seen": None,
            "online_since": None,
            "latency": None,
            "uptime": 0.0
        })

        # Append to ping history (trim to 100)
        ping_history.setdefault(name, [])
        ping_history[name].append({
            "timestamp": now,
            "status": "online" if is_up else "offline",
            "latency": latency_ms
        })
        if len(ping_history[name]) > 100:
            ping_history[name].pop(0)

        # Detect state change
        if is_up and not entry["online"]:
            entry["online_since"] = time.time()
            entry["last_seen"] = now
            logging.info(f"{name} came ONLINE")
            if not was_recently_logged(name, "online"):
                db.insert({"camera": name, "status": "online", "timestamp": now})

        elif not is_up and entry["online"]:
            entry["online_since"] = None
            logging.info(f"{name} went OFFLINE")
            if not was_recently_logged(name, "offline"):
                db.insert({"camera": name, "status": "offline", "timestamp": now})

        entry["online"] = is_up

        # Update latency and uptime %
        latency_values = [p["latency"] for p in ping_history[name] if p.get("latency") is not None]
        online_count = sum(1 for p in ping_history[name] if p["status"] == "online")
        total = len(ping_history[name])

        entry["latency"] = round(mean(latency_values), 1) if latency_values else None
        entry["uptime"] = round((online_count / total) * 100, 1) if total > 0 else 0.0

# === BACKGROUND THREAD ===

def start_monitoring(interval=10):
    def loop():
        while True:
            update_status()
            time.sleep(interval)

    t = Thread(target=loop, daemon=True)
    t.start()
    atexit.register(lambda: logging.info("Camera monitor stopped."))