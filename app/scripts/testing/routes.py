import datetime as dt


from flask import render_template, request, send_file


from app.scripts import scripts, files_df
import app.scripts.utils as utils

import app.scripts.testing.college_board_signup_letter as college_board_signup_letter

@scripts.route("/testing")
def return_testing_reports():
    reports = [
        {
            "report_title": "P/SAT Reports",
            "report_function": "scripts.return_sat_reports",
            "report_description": "Reports related to the SAT and PSAT",
        },
    ]
    return render_template(
        "testing/templates/testing/index.html", reports=reports
    )

@scripts.route("/testing/SAT")
def return_sat_reports():
    reports = [
        {
            "report_title": "Generate College Board Signup Letters",
            "report_function": "scripts.return_college_board_signup_letters",
            "report_description": "Generates step-by-step guide for students to sign up for their college board accounts",
        },
    ]
    return render_template(
        "testing/templates/testing/index.html", reports=reports
    )

@scripts.route("/testing/SAT/college_board_signup_letters")
def return_college_board_signup_letters():

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    f = college_board_signup_letter.generate_letters(cr_3_07_df)
    download_name = f"CollegeBoardSignupLetters.pdf"
    return send_file(f, as_attachment=True, download_name=download_name)
