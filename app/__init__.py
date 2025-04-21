from flask import Flask
from .routes import bp
from .monitor import start_monitoring

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(bp)
    start_monitoring()
    return app