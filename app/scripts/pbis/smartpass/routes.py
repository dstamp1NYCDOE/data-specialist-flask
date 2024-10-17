import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.pbis.smartpass.forms import SmartPassDataUploadForm
from app.scripts.pbis.smartpass import main as smartpass
from app.scripts.pbis.smartpass import parent_letters as smartpass_parent_letters



@scripts.route("/pbis/smartpass/", methods=["GET", "POST"])
def return_smartpass_reports():
    reports = [
        {
            "report_title": "SmartPass Pass Analysis",
            "report_function": "scripts.return_smartpass_analysis_spreadsheet",
            "report_description": "Analyze passes written in SmartPass",
        },
        {
            "report_title": "SmartPass Parent Letter",
            "report_function": "scripts.return_smartpass_analysis_parent_letter",
            "report_description": "Return parent letter with SmartPass usage and sign up information",
        },
        {
            "report_title": "SmartPass Intervention Letter",
            "report_function": "scripts.return_smartpass_analysis_intervention_letter",
            "report_description": "Return parent letter with SmartPass usage and sign up information",
        },
    ]
    return render_template(
        "PBIS/templates/smartpass/index.html", reports=reports
    )

@scripts.route("/pbis/smartpass/analysis", methods=["GET", "POST"])
def return_smartpass_analysis_spreadsheet():
    if request.method == "GET":
        form = SmartPassDataUploadForm()
        return render_template(
            "pbis/templates/smartpass/smartpass_form.html",
            form=form,
        )
    else:
        
        form = SmartPassDataUploadForm(request.form)
        f, download_name = smartpass.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


@scripts.route("/pbis/smartpass/parent_letter", methods=["GET", "POST"])
def return_smartpass_analysis_parent_letter():
    if request.method == "GET":
        form = SmartPassDataUploadForm()
        return render_template(
            "pbis/templates/smartpass/smartpass_parent_letter_form.html",
            form=form,
        )
    else:
        
        form = SmartPassDataUploadForm(request.form)
        f, download_name = smartpass_parent_letters.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )

from app.scripts.pbis.smartpass import intervention_letters as smartpass_intervention_letters
@scripts.route("/pbis/smartpass/intervention_letter", methods=["GET", "POST"])
def return_smartpass_analysis_intervention_letter():
    if request.method == "GET":
        form = SmartPassDataUploadForm()
        return render_template(
            "pbis/templates/smartpass/smartpass_intervention_letter_form.html",
            form=form,
        )
    else:
        
        form = SmartPassDataUploadForm(request.form)
        f, download_name = smartpass_intervention_letters.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )    