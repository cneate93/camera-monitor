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

CONFIG_PATH = os.path.join("app", "config", "cameras.json")  # Path to the cameras JSON configuration file
LOG_DB = "status_log.json"  # Path to TinyDB for status logs
LOG_FILE = "camera_events.log"  # Path to the camera events log file

# === UTILITY ===

def save_cameras_to_file():
    """Save the current cameras dictionary to a JSON file."""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cameras, f, indent=4)
        logging.info(f"Cameras saved successfully: {cameras}")
    except Exception as e:
        logging.error(f"Error saving cameras to file: {e}")

def load_camera_config():
    """Load camera configuration from the cameras.json file."""
    try:
        with open(CONFIG_PATH) as f:
            raw = json.load(f)
        cameras = {name: {"ip": val["ip"], "group": val["group"]} for name, val in raw.items()}  # Extract cameras with both IP and group
        camera_groups = {name: val["group"] for name, val in raw.items()}  # Extract camera groups
        return cameras, camera_groups
    except Exception as e:
        logging.error(f"Error loading cameras configuration: {e}")
        return {}, {}

# === MONITORING ===

def update_status():
    """Update the status of all cameras."""
    global cameras, camera_groups

    # Reload cameras.json dynamically (allows editing on the fly)
    cameras, camera_groups = load_camera_config()

    now = time.strftime('%Y-%m-%d %H:%M:%S')

    for name, data in cameras.items():
        ip = data["ip"]
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
            db.insert({"camera": name, "status": "online", "timestamp": now})

        elif not is_up and entry["online"]:
            entry["online_since"] = None
            logging.info(f"{name} went OFFLINE")
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
    """Start the background thread for monitoring camera status."""
    def loop():
        while True:
            update_status()
            time.sleep(interval)

    t = Thread(target=loop, daemon=True)
    t.start()
    atexit.register(lambda: logging.info("Camera monitor stopped."))

# === API FUNCTIONALITY ===

# Initialize camera list from the config file
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

def was_recently_logged(camera_name, status, seconds=3):
    """Prevent duplicate log entries within X seconds"""
    Camera = Query()
    entries = db.search((Camera.camera == camera_name) & (Camera.status == status))
    if not entries:
        return False
    last_entry = sorted(entries, key=lambda x: x["timestamp"])[-1]
    last_time = time.mktime(time.strptime(last_entry["timestamp"], "%Y-%m-%d %H:%M:%S"))
    return time.time() - last_time < seconds

def add_camera(name, ip, group="Uncategorized"):
    """Add a new camera to the system with optional group."""
    if name in cameras:
        logging.error(f"Camera with name {name} already exists.")
        return {"error": "Camera with this name already exists"}, 400

    # Add the new camera with its group
    cameras[name] = {"ip": ip, "group": group}
    save_cameras_to_file()  # Persist the change to the cameras.json file
    logging.info(f"Camera {name} added successfully with IP: {ip} and group: {group}")
    return {"message": f"Camera {name} added successfully."}, 200

def delete_camera(name):
    """Delete a camera from the system."""
    if name not in cameras:
        logging.error(f"Camera with name {name} not found.")
        return {"error": "Camera not found"}, 404

    # Remove the camera from the dictionary
    del cameras[name]
    save_cameras_to_file()  # Persist the change to the cameras.json file
    logging.info(f"Camera {name} deleted successfully.")
    return {"message": f"Camera {name} deleted successfully."}, 200

# === END OF SCRIPT ===