import datetime as dt


from flask import render_template, request, send_file


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.testing.forms import (
    CollegeBoardExamInvitationLetter,
    CollegeBoardExamTicketsLetter,
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
            "files_needed": ["1_14","1_01"],
        },
    ]
    files_needed = ['1_01','1_08','1_14']
    return render_template(
        "testing/templates/testing/regents/index.html", reports=reports, files_needed=files_needed
    )

@scripts.route("/testing/regents/initial_registrations")
def return_initial_regents_registrations():
    df = regents_initial_registration()
    print(df)
    return ''

    f = ""
    testing_period = "June2024"
    download_name = f"{testing_period}_exam_invitations.pdf"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )


@scripts.route("/testing/regents/examinvitations")
def return_regents_exam_invitations():

    f = ""
    testing_period = "June2024"
    download_name = f"{testing_period}_exam_invitations.pdf"
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )
