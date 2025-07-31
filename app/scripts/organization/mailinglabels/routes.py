import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.mailinglabels.forms import ReturnMailingLabelsFromStudentPDFForm, ReturnMailingLabelsByStudentIDListForm
from app.scripts.organization.mailinglabels.main import main as mailing_labels_by_student_pdf
from app.scripts.organization.mailinglabels.main import by_list_of_students as by_list_of_students

@scripts.route("/organization/mailinglabels/", methods=["GET", "POST"])
def return_mailing_labels_by_student_pdf():

    if request.method == "GET":
        form = ReturnMailingLabelsFromStudentPDFForm()
        return render_template(
            "organization/templates/organization/mailinglabels/form.html",
            form=form,
        )
    else:
        form = ReturnMailingLabelsFromStudentPDFForm(request.form)
        f = mailing_labels_by_student_pdf(form, request)

        download_name = f"mailing_labels.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )

@scripts.route("/organization/mailinglabels/by_studentid_lst", methods=["GET", "POST"])
def return_mailing_labels_by_student_list():

    if request.method == "GET":
        form = ReturnMailingLabelsByStudentIDListForm()
        return render_template(
            "organization/templates/organization/mailinglabels/by_student_list_form.html",
            form=form,
        )
    else:
        form = ReturnMailingLabelsByStudentIDListForm(request.form)
        f = by_list_of_students(form, request)

        download_name = f"mailing_labels.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )
