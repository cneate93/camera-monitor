from flask import Blueprint, render_template, jsonify, request
from .monitor import status_data, cameras, ping_history, camera_groups, db, save_cameras_to_file
import time
import logging

bp = Blueprint("main", __name__)

# -----------------------
# Route: Home → Dashboard
@bp.route("/")
@bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -----------------------
# API: Live Status Snapshot
@bp.route("/api/status")
def api_status():
    result = {}
    for name, data in cameras.items():
        ip = data["ip"]
        entry = status_data.get(name, {})
        result[name] = {
            "ip": ip,
            "online": entry.get("online"),
            "last_seen": entry.get("last_seen"),
            "online_since": entry.get("online_since"),
            "latency": entry.get("latency"),
            "uptime": entry.get("uptime")
        }
    return jsonify(result)

# -----------------------
# API: Ping History (last 100 pings per camera)
@bp.route("/api/history")
def api_history():
    return jsonify(ping_history)

# -----------------------
# API: Recent Status Events (last 100 changes)
@bp.route("/api/events")
def api_events():
    try:
        all_logs = db.all()
        sorted_logs = sorted(all_logs, key=lambda x: x["timestamp"], reverse=True)
        return jsonify(sorted_logs[:100])
    except Exception as e:
        logging.error(f"Error fetching event logs: {e}")
        return jsonify({"error": f"Unable to fetch logs: {str(e)}"}), 500

# -----------------------
# API: Camera Groups (for filtering)
@bp.route("/api/cameras")
def api_cameras():
    return jsonify(camera_groups)

# -----------------------
# API: Add a Camera
@bp.route("/api/cameras/add", methods=["POST"])
def add_camera():
    data = request.get_json()
    camera_name = data.get("name")
    camera_ip = data.get("ip")
    camera_group = data.get("group")  # Optional group for the camera

    if not camera_name or not camera_ip:
        return jsonify({"error": "Both name and IP are required"}), 400

    # Check if the camera already exists
    if camera_name in cameras:
        return jsonify({"error": f"Camera {camera_name} already exists"}), 400

    # Add to cameras dict (with group included)
    cameras[camera_name] = {"ip": camera_ip, "group": camera_group if camera_group else "default"}
    
    # Save to file (persistent)
    save_cameras_to_file()

    logging.info(f"Camera {camera_name} added successfully with IP {camera_ip} and Group {camera_group}")
    return jsonify({"message": "Camera added successfully"}), 200

# -----------------------
# API: Delete a Camera
@bp.route("/api/cameras/delete", methods=["POST"])
def delete_camera():
    data = request.get_json()
    camera_name = data.get("name")

    # Check if the camera exists
    if camera_name not in cameras:
        return jsonify({"error": "Camera not found"}), 404

    # Delete from cameras dict and camera_groups
    del cameras[camera_name]
    if camera_name in camera_groups:
        del camera_groups[camera_name]

    # Save to file
    save_cameras_to_file()

    logging.info(f"Camera {camera_name} deleted successfully")
    return jsonify({"message": "Camera deleted successfully"}), 200

# -----------------------
# Route: Camera Management
@bp.route("/manage")
def manage_cameras():
    return render_template("manage_cameras.html")