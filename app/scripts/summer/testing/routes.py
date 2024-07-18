import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/summer/testing")
def return_summer_school_testing_routes():
    reports = [
        {
            "report_title": "Process Initial Exam Signups",
            "report_function": "scripts.return_summer_school_testing_process_initial_signups",
            "report_description": "Process initial exam signups from CR 4.01 and CR S.01",
        },
        {
            "report_title": "August Regents Exam Ordering",
            "report_function": "scripts.return_summer_school_regents_ordering",
            "report_description": "Process exam registration spreadsheet and determine exam order",
        },
        {
            "report_title": "August Regents Exam Only Admit List",
            "report_function": "scripts.return_summer_exam_only_students",
            "report_description": "Process exam registration spreadsheet and return students not already admitted",
        },
        {
            "report_title": "August Regents Process Pre-Registration",
            "report_function": "scripts.return_summer_regents_preregistration",
            "report_description": "Process exam registration spreadsheet and return file to upload students",
        },
        {
            "report_title": "August Regents Scheduling",
            "report_function": "scripts.return_summer_regents_scheduling",
            "report_description": "Process CR 1.08 + exam registrations spreadsheet (for testing accommodations) to schedule students into sections",
        },     
        {
            "report_title": "August Regents Exam Invitations",
            "report_function": "scripts.return_summer_school_exam_invitations",
            "report_description": "Process CR 1.08 to return exam invitations in alphabetical order",
        },  
        {
            "report_title": "August Regents Exam Labels",
            "report_function": "scripts.return_summer_school_exam_labels",
            "report_description": "Process CR 1.08 to return Regents Exam Labels",
        },
        {
            "report_title": "August Regents ENL Rosters",
            "report_function": "scripts.return_summer_school_enl_rosters",
            "report_description": "Process CR 1.08 & CR 3.07 to return Regents ENL Rosters by section",
        },

    ]
    return render_template(
        "summer/templates/summer/testing/index.html", reports=reports
    )


import app.scripts.summer.testing.process_initial_signups as process_initial_signups


@scripts.route("/summer/testing/process_initial_signups")
def return_summer_school_testing_process_initial_signups():
    school_year = session["school_year"]
    f = process_initial_signups.main()

    download_name = f"Regents_Registration_Summer_{school_year+1}.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


import app.scripts.summer.testing.regents_ordering as regents_ordering
from app.scripts.summer.testing.forms import RegentsOrderingForm


@scripts.route("/summer/testing/regents_ordering", methods=["GET", "POST"])
def return_summer_school_regents_ordering():
    if request.method == "GET":
        form = RegentsOrderingForm()
        return render_template(
            "/summer/templates/summer/testing/regents_ordering_form.html",
            form=form,
        )
    else:

        form = RegentsOrderingForm(request.form)
        df = regents_ordering.main(form, request)
        return df.to_html()


import app.scripts.summer.testing.identify_students_to_admit_exam_only as identify_students_to_admit_exam_only
from app.scripts.summer.testing.forms import IdentifyExamOnlyForm


@scripts.route("/summer/testing/exam_only", methods=["GET", "POST"])
def return_summer_exam_only_students():
    if request.method == "GET":
        form = IdentifyExamOnlyForm()
        return render_template(
            "/summer/templates/summer/testing/exam_only_admit_form.html",
            form=form,
        )
    else:

        form = IdentifyExamOnlyForm(request.form)
        df = identify_students_to_admit_exam_only.main(form, request)
        return df.to_html()


from app.scripts.summer.testing.forms import (
    ProcessRegentsPreregistrationSpreadsheetForm,
)

import app.scripts.summer.testing.schedule_pre_registered_students as schedule_registered_students


@scripts.route("/summer/testing/process_preregistration", methods=["GET", "POST"])
def return_summer_regents_preregistration():
    if request.method == "GET":
        form = ProcessRegentsPreregistrationSpreadsheetForm()
        return render_template(
            "/summer/templates/summer/testing/exam_preregistration_scheduling_form.html",
            form=form,
        )
    else:

        form = ProcessRegentsPreregistrationSpreadsheetForm(request.form)
        f = schedule_registered_students.main(form, request)

        school_year = session["school_year"]
        download_name = f"Upload_Regents_Registration_Summer_{school_year+1}.xlsx"

        return send_file(f, as_attachment=True, download_name=download_name)

from app.scripts.summer.testing.forms import SummerRegentsSchedulingForm
from app.scripts.summer.testing.regents_scheduling import main as regents_scheduling
@scripts.route("/summer/testing/regents/student_scheduling", methods=["GET", "POST"])
def return_summer_regents_scheduling():
    if request.method == "GET":
        form = SummerRegentsSchedulingForm()
        return render_template(
            "/summer/templates/summer/testing/regents_student_scheduling_form.html",
            form=form,
        )
    else:

        form = SummerRegentsSchedulingForm(request.form)
        f = regents_scheduling.main(form, request)

        return f.to_html()

        school_year = session["school_year"]
        download_name = f"Regents_Sections{school_year+1}.xlsx"

        return send_file(f, as_attachment=True, download_name=download_name)



import app.scripts.summer.testing.regents_scheduling.return_exam_invitations as return_exam_invitations
@scripts.route("/summer/testing/regents/exam_invitations")
def return_summer_school_exam_invitations():
    school_year = session["school_year"]
    f = return_exam_invitations.main()

    download_name = f"Exam_Invitations_August{school_year+1}_by_alpha.pdf"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )

from app.scripts.summer.testing.forms import ReturnExamLabelsForm
import app.scripts.summer.testing.regents_scheduling.return_exam_labels as return_exam_labels
@scripts.route("/summer/testing/regents/exam_labels", methods=["GET", "POST"])
def return_summer_school_exam_labels():
    if request.method == "GET":
        form = ReturnExamLabelsForm()
        return render_template(
            "/summer/templates/summer/testing/regents_exam_labels_form.html",
            form=form,
        )
    else:
        form = ReturnExamLabelsForm(request.form)
        f, download_name = return_exam_labels.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)
    

from app.scripts.summer.testing.forms import ReturnENLrostersForm
import app.scripts.summer.testing.regents_scheduling.return_enl_rosters as return_enl_rosters
@scripts.route("/summer/testing/regents/enl_rosters", methods=["GET", "POST"])
def return_summer_school_enl_rosters():
    if request.method == "GET":
        form = ReturnENLrostersForm()
        return render_template(
            "/summer/templates/summer/testing/regents_enl_rosters_form.html",
            form=form,
        )
    else:
        form = ReturnENLrostersForm(request.form)
        f, download_name = return_enl_rosters.main(form, request)
        return send_file(f, as_attachment=True, download_name=download_name)    