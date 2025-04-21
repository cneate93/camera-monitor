from flask import Blueprint, render_template, jsonify
from .monitor import status_data, cameras, ping_history, camera_groups, db
import time

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
    for name, ip in cameras.items():
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
        return jsonify({"error": f"Unable to fetch logs: {str(e)}"}), 500

# -----------------------
# API: Camera Groups (for filtering)
@bp.route("/api/cameras")
def api_cameras():
    return jsonify(camera_groups)