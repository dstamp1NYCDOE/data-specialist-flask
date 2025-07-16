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
        {
            "report_title": "iLog Student Absences",
            "report_function": "scripts.return_summer_school_ilog_absences",
            "report_description": "Log student absences in iLog",
        },
        {
            "report_title": "Update Attendance Spreadsheets",
            "report_function": "scripts.return_summer_school_update_rdal_spreadsheets",
            "report_description": "Process current batch of RDAL spreadsheets",
        },
        {
            "report_title": "Return No Show List as CSV",
            "report_function": "scripts.return_summer_school_no_show_list",
            "report_description": "Processes current RDAL files and return no shows",
        },
    ]


    return render_template(
        "summer/templates/summer/attendance/index.html", reports=reports
    )


import app.scripts.summer.attendance.update_RDAL_spreadsheets as update_rdal_spreadsheets


@scripts.route("/summer/attendance/update_rdal_spreadsheets")
def return_summer_school_update_rdal_spreadsheets():
    update_rdal_spreadsheets.main()
    return ""



import app.scripts.summer.attendance.return_no_show_list as return_no_show_list

@scripts.route("/summer/attendance/return_no_show_lst", methods=["GET", "POST"])
def return_summer_school_no_show_list():

    f = return_no_show_list.main()
    download_name = "No Show List.csv"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
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

from app.scripts.summer.attendance.ilog_absences import main as ilog_absences_main
@scripts.route("/summer/attendance/ilog_absences", methods=["GET", "POST"])
def return_summer_school_ilog_absences():
    if request.method == "GET":
        form = RDALUploadForm()
        return render_template(
            "/summer/templates/summer/attendance/ilog_absences.html",
            form=form,
        )
    else:
        form = RDALUploadForm(request.form)
        ilog_absences_main(form, request)
        return 'Absences logged successfully.'