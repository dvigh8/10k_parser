from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import log
from pathlib import Path
import os

# Initialize extensions
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config['HOST'] = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    try:
        
        log.instrument_flask(app)
    except Exception:
        log.exception("Failed to instrument logfire Flask app")
    # Configuration
    app.config["SECRET_KEY"] = "your-secret-key-here"  # IMPORTANT: Change this!
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # File upload configuration
    app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)

    # Import and register blueprints
    from webview10k.views.main_bp import main_bp
    from webview10k.views.api_bp import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    log.info("App created successfully")
    return app