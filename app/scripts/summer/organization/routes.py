import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


import app.api_1_0 as api  #


@scripts.route("/summer/organization")
def return_summer_school_organization_routes():
    reports = [
        {
            "report_title": "Generate Paper Bathroom Passes",
            "report_function": "scripts.return_summer_school_bathroom_passes",
            "report_description": "Generate paper bathroom passes",
        },
    ]
    return render_template(
        "summer/templates/summer/organization/index.html", reports=reports
    )


from app.scripts.summer.organization.forms import BathroomPassesForm

import json

import app.scripts.summer.organization.generate_bathroom_passes as generate_bathroom_passes


@scripts.route("/summer/organization/bathroom_passes", methods=["GET", "POST"])
def return_summer_school_bathroom_passes():
    if request.method == "GET":
        form = BathroomPassesForm()
        teachers = json.loads(api.teachers.return_teachers().get_data().decode("utf-8"))
        form.teacher.choices = [(i, i) for i in teachers]
        form.teacher.choices.insert(0, ("ALL", "ALL"))
        return render_template(
            "/summer/templates/summer/organization/bathroom_passes_form.html",
            form=form,
        )
    else:
        form = BathroomPassesForm(request.form)
        school_year = session["school_year"]
        f = generate_bathroom_passes.main(form, request)
        download_name = f"Bathroom_Passes_Summer{school_year+1}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
