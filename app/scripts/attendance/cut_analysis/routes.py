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
        {
            "report_title": "Return Cutting Group Analysis",
            "report_function": "scripts.return_jupiter_cut_analysis_groups",
            "report_description": "Returns analysis of which students are cutting in groups",
        },
        {
            "report_title": "Return Cutting Analysis by Course",
            "report_function": "scripts.return_jupiter_cut_analysis_by_course",
            "report_description": "Returns analysis of cutting by course",
        },
        {
            "report_title": "Return Prospective Cutters Present In Building",
            "report_function": "scripts.return_jupiter_cut_analysis_in_building",
            "report_description": "Returns potential top cutters for a particular period based on CAASS Scan Data",
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


from app.scripts.attendance.cut_analysis import group_analysis


@scripts.route("/attendance/cut_analysis/group_analysis")
def return_jupiter_cut_analysis_groups():
    f, download_name = group_analysis.main()
    return send_file(f, as_attachment=True, download_name=download_name)


from app.scripts.attendance.cut_analysis import cut_analysis_by_course
@scripts.route("/attendance/cut_analysis/cut_analysis_by_course")
def return_jupiter_cut_analysis_by_course():
    f, download_name = cut_analysis_by_course.main()
    return send_file(f, as_attachment=True, download_name=download_name)

from app.scripts.attendance.cut_analysis.forms import ProspectiveCuttingFromCAASSForm
from app.scripts.attendance.cut_analysis import top_cutters_by_period_with_CAASS
@scripts.route("/attendance/cut_analysis/by_period_in_building", methods=["GET", "POST"])
def return_jupiter_cut_analysis_in_building():
    if request.method == "GET":
        form = ProspectiveCuttingFromCAASSForm()
        return render_template(
            "attendance/templates/attendance/CAASS/form.html",
            form=form,
        )
    else:
        form = ProspectiveCuttingFromCAASSForm(request.form)
        f, download_name = top_cutters_by_period_with_CAASS.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )        
