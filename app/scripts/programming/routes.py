import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.programming.forms import StudentVettingForm, InitialRequestForm


@scripts.route("/programming")
def return_programming_reports():
    student_vetting_form = StudentVettingForm()
    initial_request_form = InitialRequestForm()
    form_cards = [
        {
            "Title": "Student Vetting",
            "Description": "Return spreadsheet of student vetting for advanced coursework",
            "form": student_vetting_form,
            "route": "scripts.return_student_vetting_report",
        },
        {
            "Title": "Initial Fall Requests",
            "Description": "Return spreadsheet initial student requests",
            "form": initial_request_form,
            "route": "scripts.return_initial_requests",
        },
    ]

    return render_template(
        "/programming/templates/programming/index.html", form_cards=form_cards
    )

import app.scripts.programming.vetting.main as vetting
@scripts.route("/programming/student_vetting", methods=['GET','POST'])
def return_student_vetting_report():
    school_year = session["school_year"]
    term = session["term"]


    df = vetting.main()
    
    
    f = BytesIO()
    df.to_excel(f, index=False)
    f.seek(0)

    download_name = f"{school_year}_{term}_student_vetting.xlsx"
    
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )

from app.scripts.programming.requests import main as requests


@scripts.route("/programming/initial_requests", methods=["GET", "POST"])
def return_initial_requests():
    return requests.main()
    return ""
