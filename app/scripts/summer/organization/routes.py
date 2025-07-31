import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils


import app.api_1_0 as api  #


@scripts.route("/summer/organization")
def return_summer_school_organization_routes():
    reports = [
        {
            "report_title": "Generate Paper Bathroom Passes",
            "report_function": "scripts.return_summer_school_bathroom_passes",
            "report_description": "Generate paper bathroom passes",
        },
        {
            "report_title": "Generate Teacher Labels",
            "report_function": "scripts.return_summer_school_teacher_labels",
            "report_description": "Generate teacher labels to put on folders/envelopes",
        },
        {
            "report_title": "Generate Class Lists with Photos",
            "report_function": "scripts.return_summer_school_class_list_with_photos",
            "report_description": "Generate class lists with photos for all teachers or for single teacher",
        },
        {
            "report_title": "Organize PDF by Teacher",
            "report_function": "scripts.return_summer_school_documents_organized_by_teacher",
            "report_description": "Organize PDF of student documents by last teacher of the day",
        },             
        {
            "report_title": "Zip Photos for SmartPass",
            "report_function": "scripts.return_summer_zipped_photos",
            "report_description": "Generate Zip Files to upload photos to SmartPass",
        },
        {
            "report_title": "SmartPass Kiosk Labels",
            "report_function": "scripts.return_smartpass_kiosk_labels",
            "report_description": "Generate labels for SmartPass Kiosks",
        },        
    ]

    return render_template(
        "summer/templates/summer/organization/index.html", reports=reports
    )


from app.scripts.summer.organization.forms import TeacherSelectForm

import json

import app.scripts.summer.organization.generate_bathroom_passes as generate_bathroom_passes


@scripts.route("/summer/organization/bathroom_passes", methods=["GET", "POST"])
def return_summer_school_bathroom_passes():
    if request.method == "GET":
        form = TeacherSelectForm()
        teachers = json.loads(api.teachers.return_teachers().get_data().decode("utf-8"))
        form.teacher.choices = [(i, i) for i in teachers]
        form.teacher.choices.insert(0, ("ALL", "ALL"))
        return render_template(
            "/summer/templates/summer/organization/bathroom_passes_form.html",
            form=form,
        )
    else:
        form = TeacherSelectForm(request.form)
        school_year = session["school_year"]
        f = generate_bathroom_passes.main(form, request)
        download_name = f"Bathroom_Passes_Summer{school_year+1}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


import app.scripts.summer.organization.generate_teacher_labels as generate_teacher_labels


@scripts.route("/summer/organization/teacher_labels", methods=["GET", "POST"])
def return_summer_school_teacher_labels():
    school_year = session["school_year"]
    f = generate_teacher_labels.main()
    download_name = f"Teacher_Labels_Summer{school_year+1}.pdf"

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )


import app.scripts.summer.organization.generate_class_list_with_photos as generate_class_list_with_photos


@scripts.route("/summer/organization/class_list_with_photos", methods=["GET", "POST"])
def return_summer_school_class_list_with_photos():
    if request.method == "GET":
        form = TeacherSelectForm()
        teachers = json.loads(api.teachers.return_teachers().get_data().decode("utf-8"))
        form.teacher.choices = [(i, i) for i in teachers]
        form.teacher.choices.insert(0, ("ALL", "ALL"))
        return render_template(
            "/summer/templates/summer/organization/class_list_with_photos_form.html",
            form=form,
        )
    else:
        form = TeacherSelectForm(request.form)
        school_year = session["school_year"]
        f, download_name = generate_class_list_with_photos.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


from app.scripts.summer.organization.forms import ZippedPhotosForm
import app.scripts.summer.organization.generate_zipped_photos as generate_zipped_photos


@scripts.route("/summer/organization/zipped_photos", methods=["GET", "POST"])
def return_summer_zipped_photos():
    if request.method == "GET":
        form = ZippedPhotosForm()
        return render_template(
            "/summer/templates/summer/organization/zipped_photos_form.html",
            form=form,
        )
    else:

        form = ZippedPhotosForm(request.form)
        f, download_name = generate_zipped_photos.main(form, request)
        return send_file(f, download_name=download_name, as_attachment=True)

from app.scripts.summer.organization.forms import SmartPassKioskLabels
import app.scripts.summer.organization.generate_smart_pass_kiosk_labels as generate_smart_pass_kiosk_labels
@scripts.route("/summer/organization/SmartPass/kiosk_labels", methods=["GET", "POST"])
def return_smartpass_kiosk_labels():
    if request.method == "GET":
        form = SmartPassKioskLabels()
        return render_template(
            "/summer/templates/summer/organization/smart_pass_kiosk_label_form.html",
            form=form,
        )
    else:

        form = SmartPassKioskLabels(request.form)
        f, download_name = generate_smart_pass_kiosk_labels.main(form, request)
        return send_file(f, download_name=download_name, as_attachment=True)


from app.scripts.summer.organization.forms import OrganizeStudentRecordsForm
import app.scripts.summer.organization.organize_pdf_by_teacher as organize_pdf_by_teacher
@scripts.route("/summer/organization/documents_by_teacher", methods=["GET", "POST"])
def return_summer_school_documents_organized_by_teacher():

    if request.method == "GET":
        form = OrganizeStudentRecordsForm()
        return render_template(
            "/summer/templates/summer/organization/organize_student_records_form.html",
            form=form,
        )
    else:
        form = OrganizeStudentRecordsForm(request.form)
        f = organize_pdf_by_teacher.main(form, request)

        download_name = f"organized_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )