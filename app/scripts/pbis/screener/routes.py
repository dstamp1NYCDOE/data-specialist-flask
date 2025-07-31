import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils


@scripts.route("/pbis/screener/", methods=["GET", "POST"])
def return_screener_reports():
    reports = [
        {
            "report_title": "Universal Screener Analysis",
            "report_function": "scripts.return_screener_analysis_spreadsheet",
            "report_description": "Analyze universal screener data",
        },
        {
            "report_title": "Universal Screener Teacher Report",
            "report_function": "scripts.return_screener_analysis_teacher_report",
            "report_description": "Analyze universal screener data and report Teacher Report",
        }, 
        {
            "report_title": "Universal Screener Wellness Team Report",
            "report_function": "scripts.return_screener_analysis_wellness_report_report",
            "report_description": "Analyze universal screener data and Generate Wellness Team Report",
        },  
        {
            "report_title": "Universal Screener Classroom Report",
            "report_function": "scripts.return_screener_analysis_classroom_report",
            "report_description": "Analyze universal screener data and Generate Classroom Summary",
        },                        
    ]
    return render_template(
        "PBIS/templates/screener/index.html", reports=reports
    )

from app.scripts.pbis.screener.forms import ScreenerUploadForm
from app.scripts.pbis.screener.main import main as analyze_screener
@scripts.route("/pbis/screener/analysis", methods=["GET", "POST"])
def return_screener_analysis_spreadsheet():
    if request.method == "GET":
        form = ScreenerUploadForm()
        return render_template(
            "pbis/templates/screener/upload_form.html",
            form=form,
        )
    else:
        
        form = ScreenerUploadForm(request.form)
        f, download_name = analyze_screener(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
    

from app.scripts.pbis.screener.forms import ScreenerUploadForm
from app.scripts.pbis.screener.staff_summary import main as staff_summary
@scripts.route("/pbis/screener/analysis/teacherreport", methods=["GET", "POST"])
def return_screener_analysis_teacher_report():
    if request.method == "GET":
        form = ScreenerUploadForm()
        return render_template(
            "pbis/templates/screener/teacher_report_form.html",
            form=form,
        )
    else:
        
        form = ScreenerUploadForm(request.form)
        f, download_name = staff_summary(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )    
    

from app.scripts.pbis.screener.forms import ScreenerUploadForm
from app.scripts.pbis.screener.wellness_team_summary import main as wellness_team_summary
@scripts.route("/pbis/screener/analysis/wellness_team_report", methods=["GET", "POST"])
def return_screener_analysis_wellness_report_report():
    if request.method == "GET":
        form = ScreenerUploadForm()
        return render_template(
            "pbis/templates/screener/wellness_team_report_form.html",
            form=form,
        )
    else:
        
        form = ScreenerUploadForm(request.form)
        f, download_name = wellness_team_summary(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )        
    

from app.scripts.pbis.screener.forms import ScreenerUploadForm
from app.scripts.pbis.screener.class_summary import main as class_summary
@scripts.route("/pbis/screener/analysis/classroom_report", methods=["GET", "POST"])
def return_screener_analysis_classroom_report():
    if request.method == "GET":
        form = ScreenerUploadForm()
        return render_template(
            "pbis/templates/screener/classroom_report_form.html",
            form=form,
        )
    else:
        
        form = ScreenerUploadForm(request.form)
        f, download_name = class_summary(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )        