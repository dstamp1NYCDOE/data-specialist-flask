import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.attendance.confirmation_sheets.forms import ConfirmationSheetsCoverPageForm
from app.scripts.attendance.confirmation_sheets import main as confirmation_sheets


@scripts.route("/attendance/confirmation_sheets", methods=["GET", "POST"])
def return_confirmation_sheets_cover_page():
    if request.method == "GET":
        form = ConfirmationSheetsCoverPageForm()
        return render_template(
            "attendance/templates/attendance/confirmation_sheets/form.html",
            form=form,
        )
    else:

        form = ConfirmationSheetsCoverPageForm(request.form)
        f, download_name = confirmation_sheets.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
