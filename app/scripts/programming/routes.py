import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from flask_wtf import FlaskForm
from app.scripts.programming.forms import (
    StudentVettingForm,
    InitialRequestForm,
    InitialRequestInformLetters,
    FinalRequestInformLetters,
    MajorReapplicationForm,
    AP_offers_Letter_Form,
)

from app.scripts.programming.jupiter.forms import JupiterMasterScheduleForm


@scripts.route("/programming")
def return_programming_reports():
    student_vetting_form = StudentVettingForm()
    initial_request_form = InitialRequestForm()
    initial_request_inform_letter_form = InitialRequestInformLetters()
    final_request_inform_letter_form = FinalRequestInformLetters()
    upload_advanced_coursework_surveys = UploadAdvancedCourseSurveyForm()
    ap_offer_letter_form = AP_offers_Letter_Form()
    jupiter_master_schedule_form = JupiterMasterScheduleForm()
    generic_form = FlaskForm()
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
            "Title": "Updated Fall Requests",
            "Description": "Return spreadsheet updated student requests based on math and science results",
            "form": initial_request_form,
            "route": "scripts.return_updated_requests",
        },
        {
            "Title": "Initial Fall Request Inform Letters",
            "Description": "Return spreadsheet initial student requests",
            "form": initial_request_inform_letter_form,
            "route": "scripts.return_initial_request_inform",
        },
        {
            "Title": "CTE Major Notification Letter",
            "Description": "Return form letter for rising 10th grade students to inform them of their CTE major",
            "form": initial_request_inform_letter_form,
            "route": "scripts.return_cte_major_notification",
        },        
        {
            "Title": "Final Fall Request Inform Letters",
            "Description": "Return PDF of final notice letters for Fall Requests",
            "form": final_request_inform_letter_form,
            "route": "scripts.return_final_request_inform",
        },
        {
            "Title": "Return AP Class Offers",
            "Description": "Return pdf of student offers for AP courses",
            "form": ap_offer_letter_form,
            "route": "scripts.return_ap_offer_letters",
        },
        {
            "Title": "Process Advanced Coursework Survey",
            "Description": "Return spreadsheet with student interest in advanced coursework combined with student vetting",
            "form": upload_advanced_coursework_surveys,
            "route": "scripts.return_processed_advanced_course_survey",
        },
        {
            "Title": "Process Master Schedule",
            "Description": "Process Master Schedule Spreadsheet to upload to STARS",
            "form": initial_request_form,
            "route": "scripts.return_processed_master_schedule",
        },
        {
            "Title": "Return Jupiter Master Schedule",
            "Description": "Process Master Schedule to Return File to Upload To Jupiter",
            "form": jupiter_master_schedule_form,
            "route": "scripts.return_jupiter_master_schedule",
        },
        {
            "Title": "Return Jupiter Student Upload",
            "Description": "Process Student Upload to Return File to Upload To Jupiter",
            "form": jupiter_master_schedule_form,
            "route": "scripts.return_jupiter_student_upload",
        },
        {
            "Title": "Combine ICT Sections",
            "Description": "Combine ICT sections for STARS Upload",
            "form": jupiter_master_schedule_form,
            "route": "scripts.return_combined_ict_for_stars",
        },
        {
            "Title": "Spring Programming",
            "Description": "Return Spring Programming Scripts",
            "form": jupiter_master_schedule_form,
            "route": "scripts.return_programming_spring_scripts",
        },   
        {
            "Title": "Update Request Post Summer",
            "Description": "Run this script after summer school grades + regents to update student requests. Will generate requests for students without any (may exclude CTE) and update based on progress towards graduation based on Spring and Summer terms.",
            "form": generic_form,
            "route": "scripts.return_updated_requests_post_summer",
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


from app.scripts.programming.forms import UploadAdvancedCourseSurveyForm


@scripts.route("/programming/process_advanced_course_survey", methods=["GET", "POST"])
def return_processed_advanced_course_survey():
    if request.method == "GET":
        form = UploadAdvancedCourseSurveyForm()
        return render_template(
            "programming/templates/programming/process_advanced_course_survey.html",
            form=form,
        )
    else:
        form = UploadAdvancedCourseSurveyForm(request.form)
        data = {
            "form": form,
            "request": request,
        }
        f = vetting.merge_with_interest_forms(data)

        school_year = session["school_year"]
        term = session["term"]

        download_name = (
            f"{school_year+1}_{1}_student_vetting_for_advanced_coursework.xlsx"
        )
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )



from app.scripts.programming.requests.update_requests import main as update_requests
@scripts.route("/programming/update_requests", methods=["GET", "POST"])
def return_updated_requests():
    f = update_requests()
    return f.to_html()
    f,download_name =  update_requests()
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )    

from app.scripts.programming.requests import main as requests


@scripts.route("/programming/initial_requests", methods=["GET", "POST"])
def return_initial_requests():
    f,download_name =  requests.main()
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )    


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


import app.scripts.programming.request_inform.final_request_inform as final_request_inform


@scripts.route("/programming/final_requests_letter", methods=["GET", "POST"])
def return_final_request_inform():
    school_year = session["school_year"]
    term = session["term"]

    form = FinalRequestInformLetters(request.form)
    data = {
        "date_of_letter": form.date_of_letter.data,
    }

    f = final_request_inform.main(data)
    f.seek(0)

    download_name = f"{school_year}_{term}_final_request_inform_letters.pdf"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )

import app.scripts.programming.request_inform.cte_major_change_inform as cte_major_change_inform


@scripts.route("/programming/cte_major_notification", methods=["GET", "POST"])
def return_cte_major_notification():
    school_year = session["school_year"]
    term = session["term"]

    form = InitialRequestInformLetters(request.form)
    data = {
        "date_of_letter": form.date_of_letter.data,
        "due_date": form.due_date.data,
    }

    f = cte_major_change_inform.main(data)
    f.seek(0)

    download_name = f"{school_year}_{term}_cte_major_change_inform_letters.pdf"

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


from app.scripts.programming.master_schedule import main as process_master_schedule


@scripts.route("/programming/process_master_schedule", methods=["GET", "POST"])
def return_processed_master_schedule():
    return process_master_schedule.main()


import app.scripts.programming.ap_offers.main as ap_offers


@scripts.route("/programming/ap_offer_letters", methods=["GET", "POST"])
def return_ap_offer_letters():
    if request.method == "GET":
        form = AP_offers_Letter_Form()
        return render_template(
            "/programming/templates/programming/ap_offer_letters.html",
            form=form,
        )
    else:
        school_year = session["school_year"]
        term = session["term"]
        form = AP_offers_Letter_Form(request.form)
        f = ap_offers.main(form, request)
        download_name = f"{school_year}_{term}_AP_offers_letter.pdf"
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


import app.scripts.programming.finalization.check_if_retaking_course as check_if_retaking_course


@scripts.route("/programming/check_if_enrolled_in_passed_course")
def return_check_if_passed_course():
    school_year = session["school_year"]
    f = check_if_retaking_course.main()

    download_name = f"PassedPriorCourse_Fall_{school_year}.xlsx"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )
