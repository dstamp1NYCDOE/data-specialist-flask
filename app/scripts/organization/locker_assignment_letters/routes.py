import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.locker_assignment_letters.forms import (
    LockerAssignmentFileUploadForm,
)


from app.scripts.organization.locker_assignment_letters.main import return_locker_assignment_letters

@scripts.route("/organization/lockers")
def return_lockers_reports():
    reports = [
        {
            "report_title": "Return Locker Assignment Letters",
            "report_function": "scripts.return_locker_assignment_letters_pdf",
            "report_description": "Report MetroCard labels by organization File",
        },
    ]
    return render_template(
        "organization/templates/organization/lockers/index.html", reports=reports
    )


@scripts.route("/organization/lockers/letters", methods=["GET", "POST"])
def return_locker_assignment_letters_pdf():
    if request.method == "GET":
        form = LockerAssignmentFileUploadForm()
        return render_template(
            "organization/templates/organization/lockers/lockers_assignment_file_form.html",
            form=form,
        )
    else:

        form = LockerAssignmentFileUploadForm(request.form)

        f, download_name = return_locker_assignment_letters(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )

