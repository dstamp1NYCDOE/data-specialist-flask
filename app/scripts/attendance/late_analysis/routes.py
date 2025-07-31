import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df


@scripts.route("/attendance/late_analysis")
def return_jupiter_late_analysis_reports():
    reports = [
        {
            "report_title": "Return Top 30 Late Students by Class Period",
            "report_function": "scripts.return_jupiter_late_analysis_by_period_with_pictures",
            "report_description": "Returns PDF of top 30 late students by period",
        },
        {
            "report_title": "Return Lateness By Course with CAASS",
            "report_function": "scripts.return_jupiter_late_analysis_with_caass_by_course",
            "report_description": "",
        },
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )


from app.scripts.attendance.late_analysis import top_lates_by_period


@scripts.route("/attendance/late_analysis/by_period/pictures")
def return_jupiter_late_analysis_by_period_with_pictures():
    f, download_name = top_lates_by_period.main()
    return send_file(f, as_attachment=True, download_name=download_name)


from app.scripts.attendance.late_analysis import lateness_by_course


@scripts.route("/attendance/late_analysis/by_course")
def return_jupiter_late_analysis_with_caass_by_course():
    f, download_name = lateness_by_course.main()
    return send_file(f, as_attachment=True, download_name=download_name)
