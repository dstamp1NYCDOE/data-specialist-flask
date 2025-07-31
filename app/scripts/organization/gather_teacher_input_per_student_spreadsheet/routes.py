import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils.utils as utils


from app.scripts import scripts, files_df


from app.scripts.organization.gather_teacher_input_per_student_spreadsheet.forms import TeacherInputPerStudentSpreadsheetForm
import app.scripts.organization.gather_teacher_input_per_student_spreadsheet.main as gather_teacher_input_per_student_spreadsheet

@scripts.route("/organization/gather_teacher_input_per_student_spreadsheet", methods=["GET", "POST"])
def return_gather_teacher_input_per_student_spreadsheet():
    if request.method == "GET":
        form = TeacherInputPerStudentSpreadsheetForm()
        return render_template(
            "organization/templates/organization/gather_teacher_input_per_student_spreadsheet/form.html",
            form=form,
        )
    else:
        form = TeacherInputPerStudentSpreadsheetForm(request.form)

        spreadsheet_title = form.spreadsheet_title.data

        f = gather_teacher_input_per_student_spreadsheet.main(form, request)

        download_name = (
            f"{spreadsheet_title}_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
        )

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )        