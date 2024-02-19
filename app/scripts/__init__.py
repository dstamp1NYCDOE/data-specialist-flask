from flask import Blueprint

import app.scripts.utils as utils

scripts = Blueprint("scripts", __name__,template_folder='')
files_df = utils.return_dataframe_of_files()

from app.scripts.commutes import commutes
from app.scripts.programming import programming
from app.scripts.attendance import attendance
