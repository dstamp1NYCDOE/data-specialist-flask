from dotenv import load_dotenv
from flask import Flask

import os 
load_dotenv(override=True)

from app.config import Config



def create_app(config_class=Config):


    app = Flask(__name__)
    app.config.from_object(config_class)

    
    from app.main.routes import main

    app.register_blueprint(main)

    from app.api_1_0 import api as api_1_0_blueprint

    app.register_blueprint(api_1_0_blueprint, url_prefix="/api")

    from app.scripts import scripts as scripts_blueprint

    app.register_blueprint(scripts_blueprint, url_prefix="/scripts")

    from app.scripts.graduation import graduation as graduation_blueprint

    app.register_blueprint(graduation_blueprint, url_prefix="/graduation")

    return app
    with app.app_context():
        from app.scripts.attendance.dashboards.overall_daily import create_dashboard

        app = create_dashboard(app)

        return app
