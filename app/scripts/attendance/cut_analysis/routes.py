import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file


import app.scripts.utils as utils


from app.scripts import scripts, files_df



@scripts.route("/attendance/cut_analysis")
def return_jupiter_cut_analysis_reports():
    reports = [
        {
            "report_title": "Return Top 27 Cutting Students by Class Period",
            "report_function": "scripts.return_jupiter_cut_analysis_by_period_with_pictures",
            "report_description": "Returns PDF of top 27 cutting students by period",
        },
    ]
    return render_template(
        "attendance/templates/attendance/index.html", reports=reports
    )

from app.scripts.attendance.cut_analysis import top_cutters_by_period
@scripts.route("/attendance/cut_analysis/by_period/pictures")
def return_jupiter_cut_analysis_by_period_with_pictures():
    f, download_name = top_cutters_by_period.main()
    return send_file(f, as_attachment=True, download_name=download_name)