import os
from dotenv import load_dotenv
from flask import Flask

from routes.main import main_bp
from routes.api import api_bp
from utils.logging import setup_logging


def _env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name, default):
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default

def _clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def create_app():
    load_dotenv()

    app = Flask(__name__)

    max_prompt_len = _env_int("MAX_PROMPT_LEN", 500)
    app.config["MAX_PROMPT_LEN"] = _clamp(max_prompt_len, 1, 5000)
    app.config["IMAGEN_TIMEOUT"] = _env_int("IMAGEN_TIMEOUT", 60)
    app.config["DEBUG"] = _env_bool("FLASK_DEBUG", False)

    setup_logging(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config["DEBUG"])
