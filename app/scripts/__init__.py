from flask import Blueprint

import app.scripts.utils as utils

scripts = Blueprint("scripts", __name__, template_folder="")
files_df = utils.return_dataframe_of_files()

from app.scripts.commutes import commutes
from app.scripts.programming import routes
from app.scripts.attendance import attendance
from app.scripts.organization import routes
from app.scripts.testing import routes
from app.scripts.scholarship import routes
from app.scripts.pbis import routes
from app.scripts.privileges import routes
from app.scripts.classwork import routes
from app.scripts.progress_towards_graduation import routes
from app.scripts.officialclass import routes

from app.scripts.summer import routes
from app.scripts.summer.testing import routes
from app.scripts.summer.programming import routes
