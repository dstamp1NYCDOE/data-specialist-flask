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

        {
            "report_title": "Return Possible Attendance Errors by Teacher by Week",
            "report_function": "scripts.return_weekly_jupiter_attendance_error_by_teacher",
            "report_description": "Send a Teams message to teachers with possible attendance errors for the week",
        },
        {
            "report_title": "Return Field Trip Notifications for Teacher By Day",
            "report_function": "scripts.return_daily_field_trip_notifications_in_jupiter",
            "report_description": "Send a Teams message to teachers with who is going on a field trip on that day",
        },  
        {
            "report_title": "Return Potential Cut Notifications for Teacher By Day",
            "report_function": "scripts.return_potential_cut_notifications_in_jupiter",
            "report_description": "Send a Teams message to teachers with which students may have cut their class on a particular day",
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

from app.scripts.attendance.cut_analysis.forms import AttendanceWeekOfForm
from app.scripts.attendance.jupiter import errors_by_week as jupiter_attd_errors_by_week
@scripts.route("/attendance/jupiter2/attendance_errors_by_teacher", methods=["GET", "POST"])
def return_weekly_jupiter_attendance_error_by_teacher():
    if request.method == "GET":
        form = AttendanceWeekOfForm()
        return render_template(
            "attendance/templates/attendance/jupiter_attd_errors_by_week/form.html",
            form=form,
        )
    else:
        form = AttendanceWeekOfForm(request.form)
        return jupiter_attd_errors_by_week.main(form, request)

from app.scripts.attendance.cut_analysis.forms import AttendanceDayOfForm
from app.scripts.attendance.jupiter import field_trip_by_day as jupiter_attd_field_trip_by_day
@scripts.route("/attendance/jupiter2/field_trips_notification", methods=["GET", "POST"])
def return_daily_field_trip_notifications_in_jupiter():
    if request.method == "GET":
        form = AttendanceDayOfForm()
        return render_template(
            "attendance/templates/attendance/jupiter_trips/form.html",
            form=form,
        )
    else:
        form = AttendanceDayOfForm(request.form)
        return jupiter_attd_field_trip_by_day.main(form, request)
    

from app.scripts.attendance.cut_analysis.forms import AttendanceDayOfForm
from app.scripts.attendance.jupiter import cuts_by_day as jupiter_attd_cuts_by_day
@scripts.route("/attendance/jupiter2/potential_cuts_notification", methods=["GET", "POST"])
def return_potential_cut_notifications_in_jupiter():
    if request.method == "GET":
        form = AttendanceDayOfForm()
        return render_template(
            "attendance/templates/attendance/potential_cuts/form.html",
            form=form,
        )
    else:
        form = AttendanceDayOfForm(request.form)
        return jupiter_attd_cuts_by_day.main(form, request)    

