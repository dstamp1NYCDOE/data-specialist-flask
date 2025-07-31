import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df

from app.scripts.summer.testing.exam_only_admits.forms import ExamOnlyAdmitForm
from app.scripts.summer.testing.exam_only_admits import main as exam_only_admits_main
@scripts.route("/summer/testing/traf/automation", methods=["GET", "POST"])
def return_exam_only_admit_automation():

    if request.method == "GET":
        form = ExamOnlyAdmitForm()
        return render_template(
            "summer/testing/exam_only_admits/templates/exam_only_admit_form.html",
            form=form,
        )
    else:
        form = ExamOnlyAdmitForm(request.form)
        results_df = exam_only_admits_main.main(form, request)
        return results_df.to_html()