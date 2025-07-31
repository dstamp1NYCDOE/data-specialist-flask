import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, redirect, url_for, flash



import app.scripts.utils as utils


from app.scripts import scripts, files_df



@scripts.route("/organization/ats/automation")
def return_ats_automation():
    ats_automation_reports = {

    }
    return render_template("organization/ats_ocr/templates/index.html")


from app.scripts.organization.ats_ocr.forms import StudentIDForm
from app.scripts.organization.ats_ocr.main import return_student_VEXM_main as return_student_VEXM_main
@scripts.route("/organization/ats/automation/VEXM", methods=["GET", "POST"])
def return_VEXM_automation():

    if request.method == "GET":
        form = StudentIDForm()
        return render_template(
            "organization/ats_ocr/templates/ats_ocr_vexm_form.html",
            form=form,
        )
    else:
        form = StudentIDForm(request.form)
        return return_student_VEXM_main(form, request)
