import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils as utils


from app.scripts import scripts, files_df
import app.scripts.attendance.process_RATR as process_RATR

@scripts.route("/attendance")
def return_attendance_reports():
    reports = [
        {
            "report_title": "Student Commutes by Class",
            "report_function": "scripts.generate_commute_class_report",
            "report_description": "Select a class list to generate student commute info",
        },
        {
            "report_title": "Student Attendance",
            "report_function": "scripts.return_RATR_analysis",
            "report_description": "Analyze student daily attendance using ATS report RATR",
        },
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )

@scripts.route("/attendance/RATR_analysis")
def return_RATR_analysis():
    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)
    RATR_df = process_RATR.clean(RATR_df)

    student_pvt = process_RATR.student_attd_by_weekday(RATR_df)
    student_pvt = student_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    student_by_month_pvt = process_RATR.student_attd_by_month(RATR_df)
    student_by_month_pvt = student_by_month_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    overall_pvt = process_RATR.overall_attd_by_weekday(RATR_df)
    overall_pvt = overall_pvt.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )

    data = {
        "report_title": "RATR Analysis",
        "dfs": [student_pvt.to_html(), overall_pvt.to_html(), student_by_month_pvt.to_html()],
    }
    template_str = "templates/scripts/dataframes_generic.html"
    return render_template(template_str, data=data)
