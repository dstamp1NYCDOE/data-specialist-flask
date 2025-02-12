import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils as utils


from app.scripts import scripts, files_df
from app.scripts.attendance.jupiter import process as process_jupiter_data


@scripts.route("/attendance/jupiter2")
def return_jupiter2_attd_reports():
    reports = [
        {
            "report_title": "Return Processed Jupiter File",
            "report_function": "scripts.return_jupiter2_processed_data",
            "report_description": "Return processed Jupiter file",
        },
        {
            "report_title": "Return Jupiter Attendance Stats By Teacher",
            "report_function": "scripts.return_jupiter2_attd_stats_by_teacher",
            "report_description": "",
        },
        {
            "report_title": "Return Jupiter Attendance Stats By Student",
            "report_function": "scripts.return_jupiter2_attd_stats_by_student",
            "report_description": "",
        },
        {
            "report_title": "Return Student Attendance Report By Teacher",
            "report_function": "scripts.return_jupiter2_attd_student_report_by_teacher",
            "report_description": "",
        },


        
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )

@scripts.route("/attendance/jupiter2/processed")
def return_jupiter2_processed_data():
    df = process_jupiter_data.main()
    df = df.head(100)
    df = df.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )
    df_html = df.to_html(classes=["table", "table-sm"])

    data = {
        "reports": [
            {
                "html": df_html,
                "title": 'Processed Jupiter Data',
            },
        ]
    }
    return render_template("viewReport.html", data=data)


from app.scripts.attendance.jupiter import stats_by_teacher as jupiter_attd_stats_by_teacher
@scripts.route("/attendance/jupiter2/stats_by_teacher")
def return_jupiter2_attd_stats_by_teacher():
    df = jupiter_attd_stats_by_teacher.main()
    
    df = df.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )
    df_html = df.to_html(classes=["table", "table-sm"])

    data = {
        "reports": [
            {
                "html": df_html,
                "title": 'Jupiter Attendance Stats By Teacher',
            },
        ]
    }
    return render_template("viewReport.html", data=data)

from app.scripts.attendance.jupiter import stats_by_student as jupiter_attd_stats_by_student
@scripts.route("/attendance/jupiter2/stats_by_student")
def return_jupiter2_attd_stats_by_student():
    df = jupiter_attd_stats_by_student.main()
    
    df = df.style.set_table_attributes(
        'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
    )
    df_html = df.to_html(classes=["table", "table-sm"])

    data = {
        "reports": [
            {
                "html": df_html,
                "title": 'Jupiter Attendance Stats By Student',
            },
        ]
    }
    return render_template("viewReport.html", data=data)


from app.scripts.attendance.jupiter import student_report_by_teacher as jupiter_attd_student_report_by_teacher
@scripts.route("/attendance/jupiter2/student_report_by_teacher")
def return_jupiter2_attd_student_report_by_teacher():
    f, download_name = jupiter_attd_student_report_by_teacher.main()
    return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )



from app.scripts.attendance.jupiter.midday_analysis import main as jupiter_midday_analysis
from app.scripts.attendance.jupiter.forms import JupiterAttdUpload
@scripts.route("/attendance/jupiter2/midday_analysis", methods=['GET','POST'])
def return_jupiter_midday_analysis():
    if request.method == "GET":
        form = JupiterAttdUpload()
        return render_template(
            "attendance/jupiter/templates/midday_analysis/form.html", form=form
        )
    else:
        form = JupiterAttdUpload(request.form)
        f, download_name = jupiter_midday_analysis(request, form)
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
