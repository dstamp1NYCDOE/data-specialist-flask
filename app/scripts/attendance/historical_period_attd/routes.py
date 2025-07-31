import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils



@scripts.route("/attendance/historical/jupiter_reports")
def return_historical_jupiter_attd_reports():
    reports = [
        {
            "report_title": "Jupiter Historical Attendance Period Analysis",
            "report_function": "scripts.return_historical_jupiter_attd_spreadsheet",
            "report_description": "Analyze historical Jupiter Period Level Attendance",
        },
    ]
    return render_template(
        "attendance/templates/attendance/historical_jupiter_attd/index.html", reports=reports
    )

from app.scripts.attendance.historical_period_attd.main import create
@scripts.route("/attendance/historical/jupiter_reports/download", methods=["GET", "POST"])
def return_historical_jupiter_attd_spreadsheet():
    if request.method == "GET":
        f, download_name = create()
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            
        )