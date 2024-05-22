import datetime as dt
import pandas as pd
from io import BytesIO

from flask import render_template, request, send_file, session


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.testing.forms import (
    CollegeBoardExamInvitationLetter,
    CollegeBoardExamTicketsLetter,
    ProcessWalkingSpreadsheet,
)

import app.scripts.testing.college_board_signup_letter as college_board_signup_letter
import app.scripts.testing.college_board_exam_invitations as college_board_exam_invitations
import app.scripts.testing.college_board_exam_tickets as college_board_exam_tickets

import app.scripts.testing.regents.initial_registration as regents_initial_registration


@scripts.route("/testing")
def return_testing_reports():
    reports = [
        {
            "report_title": "P/SAT Reports",
            "report_function": "scripts.return_sat_reports",
            "report_description": "Reports related to the SAT and PSAT",
        },
        {
            "report_title": "Regents",
            "report_function": "scripts.return_regents_reports",
            "report_description": "Reports related to the Regents Exams",
        },
    ]
    return render_template("testing/templates/testing/index.html", reports=reports)


@scripts.route("/testing/SAT")
def return_sat_reports():
    reports = [
        {
            "report_title": "Generate College Board Signup Letters",
            "report_function": "scripts.return_college_board_signup_letters",
            "report_description": "Generates step-by-step guide for students to sign up for their college board accounts",
        },
        {
            "report_title": "Generate SAT/PSAT Exam Invitations",
            "report_function": "scripts.return_college_board_exam_invitations",
            "report_description": "Generates exam invitations for the SAT and PSAT",
        },
        {
            "report_title": "Generate SAT/PSAT Exam Tickets",
            "report_function": "scripts.return_college_board_exam_tickets",
            "report_description": "Generates exam tickets for the SAT and PSAT",
        },
    ]
    return render_template("testing/templates/testing/index_sat.html", reports=reports)


@scripts.route("/testing/college_board/signup_letters")
def return_college_board_signup_letters():

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    f = college_board_signup_letter.generate_letters(cr_3_07_df)
    download_name = f"CollegeBoardSignupLetters.pdf"
    return send_file(f, as_attachment=True, download_name=download_name)


@scripts.route("/testing/college_board/exam_invitations", methods=["GET", "POST"])
def return_college_board_exam_invitations():
    if request.method == "GET":
        form = CollegeBoardExamInvitationLetter()
        return render_template(
            "testing/templates/testing/college_board_exam_invitations.html", form=form
        )
    else:
        form = CollegeBoardExamInvitationLetter(request.form)
        f = college_board_exam_invitations.main(form, request)

        download_name = f"CollegeBoardExamInvitations_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"

        # return ""
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


@scripts.route("/testing/college_board/exam_tickets", methods=["GET", "POST"])
def return_college_board_exam_tickets():
    if request.method == "GET":
        form = CollegeBoardExamTicketsLetter()
        return render_template(
            "testing/templates/testing/college_board_exam_tickets.html", form=form
        )
    else:
        form = CollegeBoardExamTicketsLetter(request.form)
        f = college_board_exam_tickets.main(form, request)

        download_name = (
            f"CollegeBoardExamTickets_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        )

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


@scripts.route("/testing/regents")
def return_regents_reports():
    reports = [
        {
            "report_title": "Generate Exam Invitations",
            "report_function": "scripts.return_regents_exam_invitations",
            "report_description": "Generates student exam invitations from CR 1.08 and Regents Exam Calendar",
            "files_needed": ["1_01", "1_08", "regents_exam_calendar"],
        },
        {
            "report_title": "Generate Initial Exam Registrations",
            "report_function": "scripts.return_initial_regents_registrations",
            "report_description": "Generates student exam invitations from CR 1.08 and Regents Exam Calendar",
            "files_needed": ["1_42", "1_01"],
        },
        {
            "report_title": "Generate Walk In Spreadsheet Signup",
            "report_function": "scripts.return_regents_walkin_spreadsheet",
            "report_description": "Generates regents walk-in preregistration spreadsheet",
            "files_needed": ["1_49", "1_08"],
        },
        {
            "report_title": "Process Walk In Spreadsheet Signup",
            "report_function": "scripts.return_processed_regents_walkin_spreadsheet",
            "report_description": "Generates regents walk-in preregistration spreadsheet",
            "files_needed": [],
        },
        {
            "report_title": "Process Testing Accommodations",
            "report_function": "scripts.return_processed_testing_accommodations",
            "report_description": "Processes testing accommodations from SESIS file",
            "files_needed": ["TestingAccommodations"],
        },
        {
            "report_title": "Determine Lab Eligibility",
            "report_function": "scripts.return_lab_eligibility",
            "report_description": "Determine which students are lab eligible",
            "files_needed": ["1_01", "1_08", "1_14"],
        },
        {
            "report_title": "Schedule Students For Exams",
            "report_function": "scripts.return_students_scheduled_for_regents",
            "report_description": "Schedule students for sections based on testing accommodations and teacher of record",
            "files_needed": ["1_08", "testing_accommodations_processed"],
        },
        {
            "report_title": "Return Regents Exam Invitations",
            "report_function": "scripts.return_regents_exam_invitations",
            "report_description": "Schedule students for sections based on testing accommodations and teacher of record",
            "files_needed": ["1_08", "testing_accommodations_processed"],
        },
        {
            "report_title": "Return Processed ENL Glossary Numbers",
            "report_function": "scripts.return_processed_enl_glossaries",
            "report_description": "Return number of Glossaries Needed By Exam",
            "files_needed": ["1_08", "testing_accommodations_processed"],
        },
                {
            "report_title": "Assign Proctors",
            "report_function": "scripts.return_regents_proctor_assignments",
            "report_description": "Upload exam book and proctor availability to assign regents proctors",
            "files_needed": [],
        },
    ]
    files_needed = [
        "1_01",
        "1_08",
        "1_14",
        "1_42",
        "1_49",
        "TestingAccommodations",
        "testing_accommodations_processed",
    ]
    return render_template(
        "testing/templates/testing/regents/index.html",
        reports=reports,
        files_needed=files_needed,
    )


from app.scripts.testing.regents import (
    determine_lab_eligibility as determine_lab_eligibility,
)


@scripts.route("/testing/regents/lab_eligibility")
def return_lab_eligibility():
    school_year = session["school_year"]
    term = session["term"]

    f = determine_lab_eligibility.main()

    download_name = f"{school_year}_{term}_lab_eligibility.xlsx"
    return ""
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )


@scripts.route("/testing/regents/initial_registrations")
def return_initial_regents_registrations():
    school_year = session["school_year"]
    term = session["term"]
    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

    df = regents_initial_registration.main(month)
    f = BytesIO()
    df.to_excel(f, index=False)
    f.seek(0)

    download_name = f"{school_year}_{term}_exam_registrations.xlsx"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )


from app.scripts.testing.regents import create_exam_invitation as create_exam_invitation


@scripts.route("/testing/regents/examinvitations")
def return_regents_exam_invitations():

    f = create_exam_invitation.main()
    testing_period = "June2024"
    download_name = f"{testing_period}_exam_invitations.pdf"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )


import app.scripts.testing.regents.create_walkin_signup_spreadsheet as create_walkin_signup_spreadsheet


@scripts.route("/testing/regents/walk_in_spreadsheet")
def return_regents_walkin_spreadsheet():
    school_year = session["school_year"]
    term = session["term"]

    df = create_walkin_signup_spreadsheet.main()
    f = BytesIO()
    df.to_excel(f, index=False)
    f.seek(0)

    download_name = f"{school_year}_{term}_regents_walkin_registration.xlsx"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )


import app.scripts.testing.regents.process_walkin_signup_spreadsheet as process_walkin_signup_spreadsheet


@scripts.route("/testing/regents/process_walkin_spreadsheet", methods=["GET", "POST"])
def return_processed_regents_walkin_spreadsheet():
    if request.method == "GET":
        form = ProcessWalkingSpreadsheet()
        return render_template(
            "testing/templates/testing/regents/process_walkin_spreadsheet.html",
            form=form,
        )
    else:
        form = ProcessWalkingSpreadsheet(request.form)
        df = process_walkin_signup_spreadsheet.main(form, request)
        f = BytesIO()
        df.to_excel(f, index=False)
        f.seek(0)

        download_name = f"Processed_Regents_Walkin_Spreadsheet_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


import app.scripts.testing.regents.process_testing_accommodations as process_testing_accommodations


@scripts.route("/testing/regents/process_testing_accommodations")
def return_processed_testing_accommodations():
    school_year = session["school_year"]
    term = session["term"]

    df = process_testing_accommodations.main()

    f = BytesIO()
    df.to_excel(f, index=False)
    f.seek(0)

    download_name = f"{school_year}_{term}_processed_testing_accommodations.xlsx"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )


import app.scripts.testing.regents.schedule_students as schedule_students


@scripts.route("/testing/regents/schedule_students")
def return_students_scheduled_for_regents():
    school_year = session["school_year"]
    term = session["term"]

    df_dict = schedule_students.main()

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    for sheet_name, dff in df_dict.items():
        dff.to_excel(writer, sheet_name=sheet_name)
    writer.close()
    f.seek(0)

    download_name = f"{school_year}_{term}_regents_scheduled_students.xlsx"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )


import app.scripts.testing.regents.process_enl_glossaries as process_enl_glossaries


@scripts.route("/testing/regents/process_enl_glossaries")
def return_processed_enl_glossaries():
    school_year = session["school_year"]
    term = session["term"]

    df_dict = process_enl_glossaries.main()

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    for sheet_name, dff in df_dict.items():
        dff.to_excel(writer, sheet_name=sheet_name)
    writer.close()
    f.seek(0)

    download_name = f"{school_year}_{term}_regents_enl_registrations.xlsx"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )

from app.scripts.testing.forms import AssignRegentsProctoringForm
from app.scripts.testing.regents.proctoring import main as regents_proctoring_assignments
@scripts.route("/testing/regents/assign_proctors", methods=["GET", "POST"])
def return_regents_proctor_assignments():
    if request.method == "GET":
        form = AssignRegentsProctoringForm()
        return render_template(
            "testing/templates/testing/regents/assign_proctors.html",
            form=form,
        )
    else:
        form = AssignRegentsProctoringForm(request.form)
        data = {
            'form':form,
            'request':request,
        }
        f = regents_proctoring_assignments.main(form, request)

        school_year = session["school_year"]
        term = session["term"]


        download_name = f"{school_year}_{term}_proctor_assignments.xlsx"
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )