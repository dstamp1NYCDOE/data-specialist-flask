import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.metrocards.forms import (
    MetroCardOrganizationFileUploadForm,
)


from app.scripts.organization.metrocards.main import (
    return_metrocard_labels_file,
    return_metrocard_signature_sheet_file,
)


@scripts.route("/organization/metrocards")
def return_metrocard_reports():
    reports = [
        {
            "report_title": "Download MetroCard Labels",
            "report_function": "scripts.return_metrocard_labels",
            "report_description": "Report MetroCard labels by organization File",
        },
        {
            "report_title": "Download MetroCard Signature Sheets",
            "report_function": "scripts.return_metrocard_signature_sheets",
            "report_description": "Return xlsx file with student metrocard assignments + signoff sheets",
        },
    ]
    return render_template(
        "organization/templates/organization/metrocards/index.html", reports=reports
    )


@scripts.route("/organization/metrocards/labels", methods=["GET", "POST"])
def return_metrocard_labels():
    if request.method == "GET":
        form = MetroCardOrganizationFileUploadForm()
        return render_template(
            "organization/templates/organization/metrocards/form_for_labels.html",
            form=form,
        )
    else:

        form = MetroCardOrganizationFileUploadForm(request.form)

        f, download_name = return_metrocard_labels_file(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


@scripts.route("/organization/metrocards/sheets", methods=["GET", "POST"])
def return_metrocard_signature_sheets():
    if request.method == "GET":
        form = MetroCardOrganizationFileUploadForm()
        return render_template(
            "organization/templates/organization/metrocards/form_for_signature_sheets.html",
            form=form,
        )
    else:
        form = MetroCardOrganizationFileUploadForm(request.form)
        f, download_name = return_metrocard_signature_sheet_file(form, request)
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
