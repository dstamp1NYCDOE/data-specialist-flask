import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df

from app.scripts.officialclass.forms import MarkingPeriodChoiceForm, GenericForm, CohortYearChoiceForm

import app.scripts.officialclass.scripts.future_class as future_class



@scripts.route("/officialclass")
def return_officialclass_reports():
    reports = [
        {
            "report_title": "Prepare Future Classes",
            "report_function": "future_class",
            "report_description": "Return student facing letters for missing + low assignments in the single course they are failing",
            "report_form": CohortYearChoiceForm(
                meta={
                    "title": "CohortYearChoiceForm",
                    "type": "cohort_year_dropdown",
                }
            ),
        },
    ]
    return render_template("officialclass/templates/officialclass/index.html", reports=reports)


@scripts.route("/officialclass/<report_function>", methods=["GET", "POST"])
def return_officialclass_report(report_function):
    if request.method == "GET":
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for("scripts.return_officialclass_reports"))
    
    data = {"form": request.form}
    school_year = session["school_year"]
    term = session["term"]

    reports_dict = {
        "future_class": {
            "function": future_class.main,
            "download_name": f"{school_year}_{term}_Future_Class.xlsx",
        },
    }
    report_dict = reports_dict.get(report_function)
    if report_dict:
        f = report_dict["function"](data)
        download_name = report_dict["download_name"]
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for("scripts.return_officialclass_reports"))
