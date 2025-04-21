# 📷 Camera Monitor

[![CI](https://github.com/cneate93/camera-monitor/actions/workflows/python-app.yml/badge.svg)](https://github.com/cneate93/camera-monitor/actions)

**Camera Monitor** is a lightweight Flask-based web dashboard for monitoring camera connectivity, latency, and uptime.  
It provides live status updates, logs status change events, and includes a clean, responsive front-end with useful metrics and customization options.

## 🚀 Features

- ✅ Real-time camera status (online/offline)  
- 📶 Ping latency and uptime metrics  
- 📜 Historical event log viewer  
- 🌗 Light/dark theme toggle  
- 🔔 Per-camera notification control  
- 🐋 Docker support for easy deployment  

## 🧪 Getting Started

Clone the repository:

```bash
git clone https://github.com/cneate93/camera-monitor.git
cd camera-monitor
```

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate      # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

Run the application:

```bash
python run.py
```

Once running, visit: [http://localhost:5000](http://localhost:5000)

## 🐳 Docker

To run the app using Docker:

```bash
docker-compose up --build
```

This will automatically build and start the Flask application and any defined services.

## 📁 Camera Configuration

Cameras are defined in the `camera_config.json` file like this:

```json
[
  {
    "name": "Cam 1",
    "ip": "192.168.1.10",
    "zone": "Garage",
    "enabled": true,
    "notify": true,
    "snapshot_url": "http://192.168.1.10/snapshot.jpg"
  }
]
```

Each camera supports the following fields:

- `name`: Display name  
- `ip`: IP address or hostname  
- `zone`: Optional grouping or location  
- `enabled`: Whether it's actively monitored  
- `notify`: Enable/disable Chrome notifications  
- `snapshot_url`: Optional snapshot URL  

## 🧰 Tech Stack

- Flask (Python)
- TinyDB
- HTML / CSS / JavaScript
- Docker & Docker Compose

## 🙌 Contributing

Pull requests are welcome!  
Please open an issue or submit a PR for improvements or features.

## 📄 License

MIT License – see the [LICENSE](LICENSE) file for details.