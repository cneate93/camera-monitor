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
    return jsonify({"success": True, "data": result})


# -----------------------
# API: Ping History (last 100 pings per camera)
@bp.route("/api/history")
def api_history():
    return jsonify({"success": True, "data": ping_history})


# -----------------------
# API: Recent Status Events (last 100 changes)
@bp.route("/api/events")
def api_events():
    try:
        all_logs = db.all()
        sorted_logs = sorted(all_logs, key=lambda x: x["timestamp"], reverse=True)
        return jsonify({"success": True, "data": sorted_logs[:100]})
    except Exception as e:
        logging.error(f"Error fetching event logs: {e}")
        return jsonify({"success": False, "error": f"Unable to fetch logs: {str(e)}"}), 500


# -----------------------
# API: Camera Groups (for filtering)
@bp.route("/api/camera-groups")
def api_camera_groups():
    return jsonify({"success": True, "data": camera_groups})


# -----------------------
# API: Full Camera List
@bp.route("/api/camera-list")
def api_camera_list():
    return jsonify({"success": True, "data": cameras})


# -----------------------
# API: Add a Camera
@bp.route("/api/cameras/add", methods=["POST"])
def add_camera():
    data = request.get_json()
    camera_name = data.get("name")
    camera_ip = data.get("ip")
    camera_group = data.get("group") or "Uncategorized"

    if not camera_name or not camera_ip:
        return jsonify({"success": False, "error": "Both name and IP are required"}), 400

    if camera_name in cameras:
        return jsonify({"success": False, "error": f"Camera '{camera_name}' already exists"}), 400

    cameras[camera_name] = {"ip": camera_ip, "group": camera_group}
    save_cameras_to_file()

    logging.info(f"Camera {camera_name} added successfully with IP {camera_ip} and Group {camera_group}")
    return jsonify({"success": True, "message": f"Camera '{camera_name}' added successfully"}), 200


# -----------------------
# API: Delete a Camera
@bp.route("/api/cameras/delete", methods=["POST"])
def delete_camera():
    data = request.get_json()
    camera_name = data.get("name")

    if not camera_name or camera_name not in cameras:
        return jsonify({"success": False, "error": "Camera not found"}), 404

    del cameras[camera_name]
    if camera_name in camera_groups:
        del camera_groups[camera_name]

    save_cameras_to_file()

    logging.info(f"Camera {camera_name} deleted successfully")
    return jsonify({"success": True, "message": f"Camera '{camera_name}' deleted successfully"}), 200


# -----------------------
# Route: Camera Management
@bp.route("/manage")
def manage_cameras():
    return render_template("manage_cameras.html")