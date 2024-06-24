import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/summer/testing")
def return_summer_school_testing_routes():
    reports = [
        {
            "report_title": "Process Initial Exam Signups",
            "report_function": "scripts.return_summer_school_testing_process_initial_signups",
            "report_description": "Process initial exam signups from CR 4.01 and CR S.01",
        },
        {
            "report_title": "August Regents Exam Ordering",
            "report_function": "scripts.return_summer_school_regents_ordering",
            "report_description": "Process exam registration spreadsheet and determine exam order",
        },
    ]
    return render_template(
        "summer/templates/summer/testing/index.html", reports=reports
    )


import app.scripts.summer.testing.process_initial_signups as process_initial_signups


@scripts.route("/summer/testing/process_initial_signups")
def return_summer_school_testing_process_initial_signups():
    school_year = session["school_year"]
    f = process_initial_signups.main()

    download_name = f"Regents_Registration_Summer_{school_year+1}.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


import app.scripts.summer.testing.regents_ordering as regents_ordering
from app.scripts.summer.testing.forms import RegentsOrderingForm


@scripts.route("/summer/testing/regents_ordering", methods=["GET", "POST"])
def return_summer_school_regents_ordering():
    if request.method == "GET":
        form = RegentsOrderingForm()
        return render_template(
            "/summer/templates/summer/testing/regents_ordering_form.html",
            form=form,
        )
    else:

        form = RegentsOrderingForm(request.form)
        df = regents_ordering.main(form, request)
        return df.to_html()
