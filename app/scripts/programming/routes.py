import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.programming.forms import (
    StudentVettingForm,
    InitialRequestForm,
    InitialRequestInformLetters,
    MajorReapplicationForm,
)


@scripts.route("/programming")
def return_programming_reports():
    student_vetting_form = StudentVettingForm()
    initial_request_form = InitialRequestForm()
    initial_request_inform_letter_form = InitialRequestInformLetters()
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
        {
            "Title": "Initial Fall Request Inform Letters",
            "Description": "Return spreadsheet initial student requests",
            "form": initial_request_inform_letter_form,
            "route": "scripts.return_initial_request_inform",
        },
    ]

    return render_template(
        "/programming/templates/programming/index.html", form_cards=form_cards
    )


import app.scripts.programming.vetting.main as vetting


@scripts.route("/programming/student_vetting", methods=["GET", "POST"])
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


import app.scripts.programming.request_inform.initial_request_inform as initial_request_inform


@scripts.route("/programming/initial_requests_letter", methods=["GET", "POST"])
def return_initial_request_inform():
    school_year = session["school_year"]
    term = session["term"]

    form = InitialRequestInformLetters(request.form)
    data = {
        "date_of_letter": form.date_of_letter.data,
        "due_date": form.due_date.data,
    }

    f = initial_request_inform.main(data)
    f.seek(0)

    download_name = f"{school_year}_{term}_initial_request_inform_letters.pdf"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )


from app.scripts.programming.cte_major_reapplication import (
    cte_major_reapplication as cte_major_reapplication,
)


@scripts.route("/programming/cte_major_reapplication", methods=["GET", "POST"])
def return_cte_major_reapplication():
    if request.method == "GET":
        form = MajorReapplicationForm()
        return render_template(
            "/programming/templates/programming/cte_major_reapplication.html",
            form=form,
        )
    else:
        school_year = session["school_year"]
        term = session["term"]
        form = MajorReapplicationForm(request.form)
        f = cte_major_reapplication.main(form, request)
        download_name = f"{school_year}_{term}_cte_majors_for_sophomores.xlsx"
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            # mimetype="application/pdf",
        )
