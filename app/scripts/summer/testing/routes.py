import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/summer/testing")
def return_summer_school_testing_routes():

    return ""
