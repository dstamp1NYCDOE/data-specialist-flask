from dotenv import load_dotenv
from flask import Flask


load_dotenv()

from app.config import Config


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.main.routes import main
    app.register_blueprint(main)

    from app.api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix="/api/v1.0")

    return app
