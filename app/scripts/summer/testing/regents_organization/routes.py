import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app, redirect, url_for


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.summer.testing.regents_organization.forms import *


@scripts.route("/summer/testing/regents/organization", methods=["GET", "POST"])
def return_summer_school_regents_organization():
    forms = [
        (
            "scripts.return_summer_school_regents_organization_labels",
            "Return Mailing Labels by Exam",
            RegentsOrganizationExamSelectForm(),
        ),
        (
            "scripts.return_summer_school_regents_organization_non_labels",
            "Return Rosters by Exam",
            RegentsOrganizationExamSelectForm(),
        ),
        (
            "scripts.return_summer_school_proctor_directions",
            "Return Proctor Directions by Hub",
            RegentsOrganizationExamSelectForm(),
        ),
        (
            "scripts.return_summer_school_student_exam_grid",
            "Return Student Exam Grid by Day + HomeSchool",
            RegentsOrganizationExamSelectForm(),
        ),
    ]
    return render_template(
        "summer/templates/summer/testing/regents/organization_index.html", forms=forms
    )


import app.scripts.summer.testing.regents_organization.return_exam_labels as return_exam_labels
@scripts.route("/summer/testing/regents/organization/labels", methods=["GET", "POST"])
def return_summer_school_regents_organization_labels():
    if request.method == "GET":
        return redirect(url_for('scripts.return_summer_school_regents_organization'))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_exam_labels.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)
    


import app.scripts.summer.testing.regents_organization.return_non_labels as return_non_labels


@scripts.route(
    "/summer/testing/regents/organization/non_labels", methods=["GET", "POST"]
)
def return_summer_school_regents_organization_non_labels():
    if request.method == "GET":
        return redirect(url_for('scripts.return_summer_school_regents_organization'))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_non_labels.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)




import app.scripts.summer.testing.regents_organization.return_student_exam_grid as return_student_exam_grid


@scripts.route(
    "/summer/testing/regents/organization/student_grid", methods=["GET", "POST"]
)
def return_summer_school_student_exam_grid():
    if request.method == "GET":
        return redirect(url_for('scripts.return_summer_school_regents_organization'))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_student_exam_grid.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)



import app.scripts.summer.testing.proctor_directions.return_proctor_directions as return_proctor_directions


@scripts.route(
    "/summer/testing/regents/organization/proctor_directions", methods=["GET", "POST"]
)
def return_summer_school_proctor_directions():
    if request.method == "GET":
        return redirect(url_for('scripts.return_summer_school_regents_organization'))
    else:
        form = RegentsOrganizationExamSelectForm(request.form)
        f, download_name = return_proctor_directions.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)





import app.scripts.summer.testing.regents_organization.organize_es_practical as organize_es_practical


@scripts.route(
    "/summer/testing/regents/organization/es_practical", methods=["GET", "POST"]
)
def return_summer_school_earth_science_practical():
    if request.method == "GET":
        form = EarthSciencePracticalForm()
        return render_template(
            "/summer/templates/summer/testing/regents/es_practical_organization.html",
            form=form,
        )
    else:
        form = EarthSciencePracticalForm(request.form)
        f, download_name = organize_es_practical.main(form, request)

        return send_file(f, as_attachment=True, download_name=download_name)
