from dotenv import load_dotenv
from flask import Flask

import os 
load_dotenv(override=True)

from app.config import Config



def create_app(config_class=Config):


    app = Flask(__name__)
    app.config.from_object(config_class)

    return app