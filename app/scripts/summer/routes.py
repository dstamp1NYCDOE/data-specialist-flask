import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/summer")
def return_summer_school_routes():
    reports = [
        {
            "report_title": "Summer School Testing",
            "report_function": "scripts.return_summer_school_testing_routes",
            "report_description": "Return summer school testing reports",
        },
        {
            "report_title": "Summer School Programming",
            "report_function": "scripts.return_summer_school_programming_routes",
            "report_description": "Return summer school programming reports",
        },
        {
            "report_title": "Summer School Organization",
            "report_function": "scripts.return_summer_school_organization_routes",
            "report_description": "Return summer school organization reports",
        },
        {
            "report_title": "Summer School Attendance",
            "report_function": "scripts.return_summer_school_attendance_routes",
            "report_description": "Return summer school attendance reports",
        },        
    ]
    return render_template("summer/templates/summer/index.html", reports=reports)
