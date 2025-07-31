import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils


@scripts.route("/pbis/phone_call_tracker/", methods=["GET", "POST"])
def return_phone_call_tracker_reports():
    reports = [
        {
            "report_title": "Phone Call Tracker Analysis",
            "report_function": "scripts.return_phone_call_tracker_analysis_spreadsheet",
            "report_description": "Analyze phone call tracker data",
        },
    ]
    return render_template(
        "PBIS/templates/phone_call_tracker/index.html", reports=reports
    )


from app.scripts.pbis.phone_call_tracker.forms import PhoneCallsUploadForm
from app.scripts.pbis.phone_call_tracker.main import main as analyze_phone_calls


@scripts.route("/pbis/phone_call_tracker/analysis", methods=["GET", "POST"])
def return_phone_call_tracker_analysis_spreadsheet():
    if request.method == "GET":
        form = PhoneCallsUploadForm()
        return render_template(
            "pbis/templates/phone_call_tracker/upload_form.html",
            form=form,
        )
    else:

        form = PhoneCallsUploadForm(request.form)
        f, download_name = analyze_phone_calls(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
