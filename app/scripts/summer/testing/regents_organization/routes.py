import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import (
    render_template,
    request,
    send_file,
    session,
    current_app,
    redirect,
    url_for,
)


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.summer.testing.regents_organization.forms import *


@scripts.route("/summer/testing/regents/organization", methods=["GET", "POST"])
def return_summer_school_regents_organization():
    forms = [
        (
            "scripts.return_summer_school_regents_organization_bathroom_log",
            "Return Bathroom Logs by Exam",
            RegentsOrganizationAllExamsForm(),
        ),
        (
            "scripts.return_summer_school_regents_organization_folder_labels",
            "Return Folder Labels by Exam",
            RegentsOrganizationExamSelectForm(),
        ), 
        (
            "scripts.return_summer_school_regents_organization_folder_pages",
            "Return Folder Pages by Exam Organized by Room",
            RegentsOrganizationExamSelectForm(),
        ),
        (
            "scripts.return_summer_school_regents_organization_exam_labels",
            "Return Student Exam Labels by Exam organized by Room",
            RegentsOrganizationExamSelectForm(),
        ),         
    ]
    return render_template(
        "summer/templates/summer/testing/regents/organization_index.html", forms=forms
    )


import app.scripts.summer.testing.regents_organization.scripts.return_bathroom_log as return_bathroom_log
@scripts.route(
    "/summer/testing/regents/organization/bathroom_log", methods=["GET", "POST"]
)
def return_summer_school_regents_organization_bathroom_log():
    if request.method == "GET":
        return redirect(url_for("scripts.return_summer_school_regents_organization"))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_bathroom_log.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)
    
import app.scripts.summer.testing.regents_organization.scripts.return_folder_labels as return_folder_labels
@scripts.route(
    "/summer/testing/regents/organization/folder_labels", methods=["GET", "POST"]
)
def return_summer_school_regents_organization_folder_labels():
    if request.method == "GET":
        return redirect(url_for("scripts.return_summer_school_regents_organization"))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_folder_labels.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)    

import app.scripts.summer.testing.regents_organization.scripts.return_folder_pages as return_folder_pages
@scripts.route(
    "/summer/testing/regents/organization/folder_pages", methods=["GET", "POST"]
)
def return_summer_school_regents_organization_folder_pages():
    if request.method == "GET":
        return redirect(url_for("scripts.return_summer_school_regents_organization"))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_folder_pages.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)        
    

import app.scripts.summer.testing.regents_organization.scripts.return_exam_labels as return_exam_labels
@scripts.route(
    "/summer/testing/regents/organization/exam_labels", methods=["GET", "POST"]
)
def return_summer_school_regents_organization_exam_labels():
    if request.method == "GET":
        return redirect(url_for("scripts.return_summer_school_regents_organization"))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_exam_labels.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)      