from flask import Flask
from .routes import bp
from .monitor import start_monitoring

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    start_monitoring()  # Starts background ping thread
    return app