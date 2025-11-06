import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.attendance.rdal_analysis.forms import RDALUploadForm
from app.scripts.attendance.rdal_analysis import main as rdal_analysis


@scripts.route("/attendance/rdal/analysis", methods=["GET", "POST"])
def return_rdal_analysis_spreadsheet():
    if request.method == "GET":
        form = RDALUploadForm()
        return render_template(
            "attendance/templates/attendance/rdal_analysis/rdal_analysis_form.html",
            form=form,
        )
    else:
        form = RDALUploadForm(request.form)
        f, download_name = rdal_analysis.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
