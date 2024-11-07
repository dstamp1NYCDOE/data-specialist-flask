import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/pbis/screener/", methods=["GET", "POST"])
def return_screener_reports():
    reports = [
        {
            "report_title": "Universal Screener Analysis",
            "report_function": "scripts.return_screener_analysis_spreadsheet",
            "report_description": "Analyze universal screener data",
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