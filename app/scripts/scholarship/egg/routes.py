import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for

from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils


@scripts.route("/scholarship/egg/", methods=["GET", "POST"])
def return_egg_reports():
    reports = [
        {
            "report_title": "Return EGG From Jupiter",
            "report_function": "scripts.return_egg_from_jupiter",
            "report_description": "Combined Jupiter grade file with EGG to upload into STARS Admin",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/egg/index.html", reports=reports
    )


from app.scripts.scholarship.egg.forms import EggUploadForm
from app.scripts.scholarship.egg.main import main


@scripts.route(
    "/scholarship/egg/jupiter_to_egg", methods=["GET", "POST"]
)
def return_egg_from_jupiter():
    if request.method == "GET":
        form = EggUploadForm()
        return render_template(
            "scholarship/templates/scholarship/egg/egg_form.html",
            form=form,
        )
    else:

        form = EggUploadForm(request.form)
        f, download_name = main(form, request)

        # return redirect(url_for('scripts.return_egg_from_jupiter'))
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
