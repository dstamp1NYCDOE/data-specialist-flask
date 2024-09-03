import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils
import app.scripts.summer.utils as summer_utils


@scripts.route("/summer/programming")
def return_summer_school_programming_routes():
    reports = [
        {
            "report_title": "Check If Taking Prior Passed Course",
            "report_function": "scripts.return_summer_school_check_if_passed_course",
            "report_description": "Process current student programs to see if they are taking a course they've already passed",
        },
        {
            "report_title": "Return Program Cards",
            "report_function": "scripts.return_summer_school_program_cards",
            "report_description": "Return summer school program cards",
        },
        {
            "report_title": "Update Summer School Gradebooks",
            "report_function": "scripts.return_update_summer_gradebooks",
            "report_description": "Update Summer School Gradebooks",
        },
        {
            "report_title": "Share Recommended Programs with Teacher Gradebooks",
            "report_function": "scripts.return_summer_school_recommended_programs_with_teachers",
            "report_description": "Update Summer School Gradebook to include SESIS recommended programs",
        },
        {
            "report_title": "Share August Regents Registrations with Teachers",
            "report_function": "scripts.return_summer_school_regents_registrations_with_teachers",
            "report_description": "Update Summer School Gradebook to include August Regents Registrations",
        },
        {
            "report_title": "Return Summer School Progress Reports",
            "report_function": "scripts.return_summer_school_progress_reports",
            "report_description": "Return Summer School Progress Reports",
        },
    ]
    return render_template(
        "summer/templates/summer/programming/index.html", reports=reports
    )


import app.scripts.summer.programming.check_if_retaking_passed_course as check_if_retaking_passed_course


@scripts.route("/summer/programming/check_if_enrolled_in_passed_course")
def return_summer_school_check_if_passed_course():
    school_year = session["school_year"]
    f = check_if_retaking_passed_course.main()

    download_name = f"PassedPriorCourse_Summer_{school_year+1}.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


import app.scripts.summer.programming.create_programs_cards as create_programs_cards


@scripts.route("/summer/programming/program_cards")
def return_summer_school_program_cards():
    school_year = session["school_year"]
    f = create_programs_cards.main()

    # return f

    download_name = f"ProgramCardsSummer{school_year+1}.pdf"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


from app.scripts.summer.programming.forms import UpdateGradebooksForm
import app.scripts.summer.programming.update_gradebooks as update_gradebooks


@scripts.route("summer/programming/update_gradebooks", methods=["GET", "POST"])
def return_update_summer_gradebooks():
    if request.method == "GET":
        form = UpdateGradebooksForm()
        return render_template(
            "/summer/templates/summer/programming/update_gradebooks_form.html",
            form=form,
        )
    else:

        form = UpdateGradebooksForm(request.form)
        f = update_gradebooks.main(form, request)
        return f


import app.scripts.summer.programming.share_recommended_programs as share_recommended_programs


@scripts.route("summer/programming/share_recommended_programs")
def return_summer_school_recommended_programs_with_teachers():
    share_recommended_programs.main()
    return ""


import app.scripts.summer.programming.share_regents_registrations as share_regents_registrations


@scripts.route("summer/programming/share_regents_registrations")
def return_summer_school_regents_registrations_with_teachers():
    share_regents_registrations.main()
    return ""


import app.scripts.summer.programming.progress_reports as progress_reports

from app.scripts.summer.programming.forms import SendingSchoolForm


@scripts.route("summer/programming/progress_reports", methods=["GET", "POST"])
def return_summer_school_progress_reports():
    if request.method == "GET":
        form = SendingSchoolForm()
        form.sending_school.choices = summer_utils.return_sending_school_list()
        form.sending_school.choices.insert(0, ("ALL", "ALL"))

        return render_template(
            "/summer/templates/summer/programming/progress_reports_form.html",
            form=form,
        )
    else:
        form = SendingSchoolForm(request.form)
        sending_school = form.data["sending_school"]

        f = progress_reports.main(form, request)
        school_year = session["school_year"]
        if sending_school == "ALL":
            download_name = f"Summer{school_year+1}ProgressReports.pdf"
        else:
            download_name = f"Summer{school_year+1}ProgressReports{sending_school}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
