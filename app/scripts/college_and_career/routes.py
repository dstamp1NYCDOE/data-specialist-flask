import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename


import app.scripts.utils as utils
from app.scripts import scripts, files_df



@scripts.route("/college_and_career")
def return_college_and_career_reports():
    reports = [
        {
            "report_title": "IPR Monitoring",
            "report_function": "scripts.return_IPR_monitoring",
            "report_description": "Upload report 1.73 to determine IPR monitoring data",
        },
    ]
    return render_template("college_and_career/templates/college_and_career/index.html", reports=reports)


from app.scripts.college_and_career.scripts.IPR_monitoring import routes