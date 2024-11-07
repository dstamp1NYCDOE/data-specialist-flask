import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils as utils


from app.scripts import scripts, files_df


@scripts.route("/attendance/caass_reports")
def return_caass_reports():
    reports = [
        {
            "report_title": "Return Processed CAASS Swipes",
            "report_function": "scripts.return_processed_caass_data",
            "report_description": "",
        },
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )


from app.scripts.attendance.CAASS.main import process_CAASS


@scripts.route("/attendance/caass/processed")
def return_processed_caass_data():
    f, download_name = process_CAASS()
    return send_file(f, as_attachment=True, download_name=download_name)
