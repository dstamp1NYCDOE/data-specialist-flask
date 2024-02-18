from dotenv import load_dotenv
from flask import Flask


load_dotenv()

from app.config import Config


from flask_executor import Executor
executor = Executor()

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    executor.init_app(app)

    from app.main.routes import main
    app.register_blueprint(main)

    from app.api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix="/api/v1.0")

    from app.scripts import scripts as scripts_blueprint
    app.register_blueprint(scripts_blueprint, url_prefix="/scripts")

    return app
