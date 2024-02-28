import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.forms import OrganizeStudentRecordsForm
from app.scripts.organization import organize_student_documents_by_list

@scripts.route("/organization")
def return_organization_reports():
    reports = [
        {
            "report_title": "Organize Student Records ",
            "report_function": "scripts.return_student_records_organized_by_class_list",
            "report_description": "Organize PDF by class list",
        },
    ]
    return render_template(
        "organization/templates/organization/index.html", reports=reports
    )


@scripts.route("/organization/student_records_by_list", methods=['GET','POST'])
def return_student_records_organized_by_class_list():
    
    if request.method == 'GET':
        form = OrganizeStudentRecordsForm()
        return render_template("organization/templates/organization/organize_student_records_form.html", form = form)
    else:
        form = OrganizeStudentRecordsForm(request.form)
        f = organize_student_documents_by_list.main(form, request)
        
        download_name = f"organized_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        return send_file(f, as_attachment=True, download_name=download_name)
