import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils
import app.scripts.summer.utils as summer_utils


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
            "report_title": "August Regents Anticipated Proctor Need",
            "report_function": "scripts.return_summer_school_anticipated_proctor_need",
            "report_description": "Process exam registration spreadsheet and determine anticipated proctor need",
        },
        {
            "report_title": "August Regents Exam Only Admit List",
            "report_function": "scripts.return_summer_exam_only_students",
            "report_description": "Process exam registration spreadsheet and return students not already admitted",
        },
        {
            "report_title": "August Regents Exam Only Admit Automation (TRAF)",
            "report_function": "scripts.return_exam_only_admit_automation",
            "report_description": "Copy and paste StudentID numbers to admit students into ATSSUM with TRAF",
        },        
        {
            "report_title": "August Regents Process Pre-Registration",
            "report_function": "scripts.return_summer_regents_preregistration",
            "report_description": "Process exam registration spreadsheet and return file to upload students",
        },
        {
            "report_title": "August Regents ZQTEST",
            "report_function": "scripts.return_summer_school_add_to_zqtest",
            "report_description": "Process 1.01 to identify which students need to be added to ZQTEST",
        },
        {
            "report_title": "August Regents Scheduling",
            "report_function": "scripts.return_summer_regents_scheduling",
            "report_description": "Process CR 1.08 + exam registrations spreadsheet (for testing accommodations) to schedule students into sections",
        },
        {
            "report_title": "August YABC Regents Scheduling",
            "report_function": "scripts.return_summer_yabc_regents_scheduling",
            "report_description": "Process CR 1.08 + exam registrations spreadsheet (for testing accommodations) to schedule students into sections",
        },
        {
            "report_title": "Process STARS Master Schedule to Return Exam Book + Proctor Need",
            "report_function": "scripts.return_processed_summer_school_exam_book",
            "report_description": "Process Master Schedule file to return Exam Book + Proctor Needs",
        },
        {
            "report_title": "August Regents Exam Invitations",
            "report_function": "scripts.return_summer_school_exam_invitations",
            "report_description": "Process CR 1.08 to return exam invitations in alphabetical order",
        },
        {
            "report_title": "August Regents ENL Rosters",
            "report_function": "scripts.return_summer_school_enl_rosters",
            "report_description": "Process CR 1.08 & CR 3.07 to return Regents ENL Rosters by section",
        },
        {
            "report_title": "August Regents Organization for Printing",
            "report_function": "scripts.return_summer_school_regents_organization",
            "report_description": "Process CR 1.08 and Regents Calendar Spreadsheet to produce labels and rosters",
        },
        {
            "report_title": "August Regents Proctor Organization",
            "report_function": "scripts.return_summer_regents_proctor_documents",
            "report_description": "Process Proctor Spreadsheet",
        },
        {
            "report_title": "August Regents ES Organization",
            "report_function": "scripts.return_summer_school_earth_science_practical",
            "report_description": "Process CR 1.08 and CR 1.01 to schedule earth science lab practical",
        },
        {
            "report_title": "Generate August Exam Only Spreadsheet",
            "report_function": "scripts.return_summer_exam_only_spreadsheet",
            "report_description": "Upload last year's exam only spreadsheet, combined 3_07, and the latest 4_01 to generate exam only signup spreadsheet",
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

import app.scripts.summer.testing.regents_scheduling.anticipated_proctor_need as anticipated_proctor_need
from app.scripts.summer.testing.forms import RegentsOrderingForm


@scripts.route("/summer/testing/anticipated_proctor_need", methods=["GET", "POST"])
def return_summer_school_anticipated_proctor_need():
    if request.method == "GET":
        form = RegentsOrderingForm()
        return render_template(
            "/summer/templates/summer/testing/anticipated_proctor_need_form.html",
            form=form,
        )
    else:

        form = RegentsOrderingForm(request.form)
        f = anticipated_proctor_need.main(form, request)
        school_year = session["school_year"]
        download_name = f"AnticipatedProctorNeed_{school_year+1}_7.xlsx"
        return send_file(f, as_attachment=True, download_name=download_name)

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
    GenerateExamOnlySpreadsheetForm,
)

import app.scripts.summer.testing.create_walkin_spreadsheet as create_walkin_spreadsheet


@scripts.route(
    "/summer/testing/create_exam_only_spreadsheet_v2", methods=["GET", "POST"]
)
def return_exam_only_spreadsheet():
    if request.method == "GET":
        form = GenerateExamOnlySpreadsheetForm()
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

        # return f.to_html()

        school_year = session["school_year"]
        download_name = f"Regents_Sections{school_year+1}.xlsx"

        return send_file(f, as_attachment=True, download_name=download_name)


import app.scripts.summer.testing.regents_scheduling.return_exam_invitations as return_exam_invitations
from app.scripts.summer.programming.forms import SendingSchoolForm


@scripts.route("/summer/testing/regents/exam_invitations", methods=["GET", "POST"])
def return_summer_school_exam_invitations():
    if request.method == "GET":
        form = SendingSchoolForm()
        form.sending_school.choices = summer_utils.return_sending_school_list()
        form.sending_school.choices.insert(0, ("ALL", "ALL"))

        return render_template(
            "/summer/templates/summer/testing/regents/exam_invitation_form.html",
            form=form,
        )
    else:
        form = SendingSchoolForm(request.form)
        sending_school = form.data["sending_school"]

        f = return_exam_invitations.main(form, request)
        school_year = session["school_year"]
        if sending_school == "ALL":
            download_name = f"Summer{school_year+1}ExamInvitations.pdf"
        else:
            download_name = f"Summer{school_year+1}ExamInvitations{sending_school}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


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


import app.scripts.summer.testing.regents_scheduling.add_zqtest as add_zqtest


@scripts.route("/summer/testing/regents/add_zqtest")
def return_summer_school_add_to_zqtest():
    school_year = session["school_year"]
    f = add_zqtest.main()

    download_name = f"AddZQTEST.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


import app.scripts.summer.testing.regents_scheduling.process_exambook_and_proctors as process_exambook_and_proctors


@scripts.route("/summer/testing/regents/process_exam_book")
def return_processed_summer_school_exam_book():
    school_year = session["school_year"]
    f = process_exambook_and_proctors.main()

    # return f.to_html()

    download_name = f"{school_year}_7_ExamBook_and_proctor_need.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


from app.scripts.summer.testing.forms import YABCRegentsRegistration
import app.scripts.summer.testing.regents_scheduling.scheduled_yabc as scheduled_yabc


@scripts.route("/summer/testing/regents/yabc_scheduling", methods=["GET", "POST"])
def return_summer_yabc_regents_scheduling():
    if request.method == "GET":
        form = YABCRegentsRegistration()
        return render_template(
            "/summer/templates/summer/testing/regents_yabc_scheduling_form.html",
            form=form,
        )
    else:

        form = YABCRegentsRegistration(request.form)
        f = scheduled_yabc.main(form, request)

        # return f.to_html()

        school_year = session["school_year"]
        download_name = f"Regents_Sections{school_year+1}.xlsx"

        return send_file(f, as_attachment=True, download_name=download_name)


import app.scripts.summer.testing.schedule_pre_registered_students as schedule_registered_students

from app.scripts.summer.testing.forms import (
    ProcessRegentsPreregistrationSpreadsheetForm,
)


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


from app.scripts.summer.testing.forms import GenerateExamOnlySpreadsheetForm
import app.scripts.summer.testing.create_walkin_spreadsheet as create_walkin_spreadsheet


@scripts.route("/summer/testing/create_exam_only_spreadsheet", methods=["GET", "POST"])
def return_summer_exam_only_spreadsheet():
    if request.method == "GET":
        form = GenerateExamOnlySpreadsheetForm()
        return render_template(
            "/summer/templates/summer/testing/generate_exam_only_spreadsheet_form.html",
            form=form,
        )
    else:

        form = GenerateExamOnlySpreadsheetForm(request.form)
        f = create_walkin_spreadsheet.main(form, request)

        school_year = session["school_year"]
        download_name = f"RegentsRegistration_Summer_{school_year+1}.xlsx"

        return send_file(f, as_attachment=True, download_name=download_name)
