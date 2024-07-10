import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


import app.api_1_0 as api  #


@scripts.route("/summer/attendance")
def return_summer_school_attendance_routes():
    reports = [
        {
            "report_title": "Process RDAL",
            "report_function": "scripts.return_summer_school_processed_rdal",
            "report_description": "Process RDAL and return phone master for school messenger",
        },       
    ]

    return render_template(
        "summer/templates/summer/attendance/index.html", reports=reports
    )

import app.scripts.summer.attendance.process_RDAL as process_RDAL 
from app.scripts.summer.attendance.forms import RDALUploadForm

@scripts.route("/summer/attendance/process_rdal", methods=["GET", "POST"])
def return_summer_school_processed_rdal():
    if request.method == "GET":
        form = RDALUploadForm()
        return render_template(
            "/summer/templates/summer/attendance/process_RDAL_form.html",
            form=form,
        )
    else:
        form = RDALUploadForm(request.form)
        
        f, download_name = process_RDAL.main(form, request)
        

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )