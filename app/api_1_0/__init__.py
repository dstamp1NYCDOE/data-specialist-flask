from flask import Blueprint

import app.scripts.utils as utils

api = Blueprint("api", __name__)
files_df = utils.return_dataframe_of_files()

from . import teachers, classes, files, students
