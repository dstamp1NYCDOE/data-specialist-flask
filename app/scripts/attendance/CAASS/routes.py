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
        {
            "report_title": "Return Students Not Yet Scanned Into Building",
            "report_function": "scripts.return_from_caass_not_yet_arrived",
            "report_description": "",
        },
        {
            "report_title": "Return CAASS Swipe Analysis",
            "report_function": "scripts.return_from_caass_swipe_time_analysis",
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


from app.scripts.attendance.CAASS.forms import caassSchoolMessengerAttendanceUpload
from app.scripts.attendance.CAASS import caass_have_not_scanned_in


@scripts.route("/attendance/caass/not_yet_arrived", methods=["GET", "POST"])
def return_from_caass_not_yet_arrived():
    if request.method == "GET":
        form = caassSchoolMessengerAttendanceUpload()
        return render_template(
            "attendance/templates/attendance/CAASS/form1.html",
            form=form,
        )
    else:
        form = caassSchoolMessengerAttendanceUpload(request.form)
        f, download_name = caass_have_not_scanned_in.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


from app.scripts.attendance.CAASS.forms import caassSchoolMessengerAttendanceUpload
from app.scripts.attendance.CAASS import cass_swipe_time_analysis


@scripts.route("/attendance/caass/swipe_time_analysis", methods=["GET", "POST"])
def return_from_caass_swipe_time_analysis():
    if request.method == "GET":
        form = caassSchoolMessengerAttendanceUpload()
        return render_template(
            "attendance/templates/attendance/CAASS/form2.html",
            form=form,
        )
    else:
        form = caassSchoolMessengerAttendanceUpload(request.form)
        f, download_name = cass_swipe_time_analysis.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
