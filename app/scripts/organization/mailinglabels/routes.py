import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.mailinglabels.forms import ReturnMailingLabelsFromStudentPDFForm
from app.scripts.organization.mailinglabels.main import main as mailing_labels_by_student_pdf

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
