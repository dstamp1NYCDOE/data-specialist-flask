import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.testing.regents.scoring.forms import UploadREDS
from app.scripts.testing.regents.scoring.return_reds_error_analysis import main as return_reds_error_analysis
@scripts.route("/testing/regents/reds_error_check", methods=["GET", "POST"])
def return_reds_error_check():
    if request.method == "GET":
        form = UploadREDS()
        return render_template(
            "testing/regents/scoring/templates/reds_error_check.html",
            form=form,
        )
    else:

        form = UploadREDS(request.form)
        f, download_name = return_reds_error_analysis(form, request)

        return send_file(f, as_attachment=True, download_name=download_name)