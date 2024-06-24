from flask import Blueprint

import app.scripts.utils as utils

graduation = Blueprint("graduation", __name__, template_folder="")

from app.scripts.graduation import routes
from app.scripts.graduation.certification import routes
from app.scripts.graduation.diplomas import routes
