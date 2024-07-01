import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/summer/programming")
def return_summer_school_programming_routes():
    reports = [
        {
            "report_title": "Check If Taking Prior Passed Course",
            "report_function": "scripts.return_summer_school_check_if_passed_course",
            "report_description": "Process current student programs to see if they are taking a course they've already passed",
        },
    ]
    return render_template(
        "summer/templates/summer/programming/index.html", reports=reports
    )


import app.scripts.summer.programming.check_if_retaking_passed_course as check_if_retaking_passed_course


@scripts.route("/summer/programming/check_if_enrolled_in_passed_course")
def return_summer_school_check_if_passed_course():
    school_year = session["school_year"]
    f = check_if_retaking_passed_course.main()

    download_name = f"PassedPriorCourse_Summer_{school_year+1}.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )
