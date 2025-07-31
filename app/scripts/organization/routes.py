import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.organization.forms import (
    OrganizeStudentRecordsForm,
    ClassListCountsFromSubsetForm,
    ClassRostersFromList,
    CareerDayReportsForm,
    MailingLabelsByPeriod,
    FolderLabelsByTeacherForm,
)
from app.scripts.organization import organize_student_documents_by_list
from app.scripts.organization import class_list_counts_from_list
from app.scripts.organization import class_rosters_from_list

from app.scripts.organization import career_day
from app.scripts.organization import geocoding



@scripts.route("/organization")
def return_organization_reports():
    reports = [
        {
            "report_title": "Return Geocoding Reports",
            "report_function": "scripts.return_geocoding_reports",
            "report_description": "",
        },
        {
            "report_title": "Return Teacher Input per Student Spreadsheet",
            "report_function": "scripts.return_gather_teacher_input_per_student_spreadsheet",
            "report_description": "",
        },
        {
            "report_title": "Update Google Sheet Class lists",
            "report_function": "scripts.return_updated_google_sheet_classlists",
            "report_description": "Update student class lists on Google Sheet",
        },
        {
            "report_title": "Organize Student Records ",
            "report_function": "scripts.return_student_records_organized_by_class_list",
            "report_description": "Organize PDF by class list",
        },
        {
            "report_title": "Make Bag Labels for Student Materials",
            "report_function": "scripts.return_bag_labels_for_student_documents_by_class_list",
            "report_description": "Upload class list to create teacher bag labels for material distribution",
        },
        {
            "report_title": "Class List Counts from StudentID List",
            "report_function": "scripts.return_class_list_counts_from_list",
            "report_description": "Return counts of students in each class based on StudentID List",
        },
        {
            "report_title": "Class Rosters from StudentID List",
            "report_function": "scripts.return_class_rosters_from_list",
            "report_description": "Return roster of students in each class based on StudentID List (inclusive or exclusive)",
        },
        {
            "report_title": "Career Day Organization",
            "report_function": "scripts.return_career_day_reports",
            "report_description": "Generate career day assignments as spreadsheet or letters",
        },
        {
            "report_title": "MetroCard Organization",
            "report_function": "scripts.return_metrocard_reports",
            "report_description": "Generate MetroCard labels and Signature Sheets",
        },
        {
            "report_title": "Locker Organization",
            "report_function": "scripts.return_lockers_reports",
            "report_description": "Generate Locker reports",
        },
        {
            "report_title": "Student Mailing Labels for a PDF",
            "report_function": "scripts.return_mailing_labels_by_student_pdf",
            "report_description": "Generate Mailing Labels to go with a PDF of student records",
        },
        {
            "report_title": "Student Mailing Labels by Period",
            "report_function": "scripts.return_mailing_labels_by_period",
            "report_description": "Generate Mailing Labels by period",
        },
        {
            "report_title": "Student Mailing Labels for StudentID List",
            "report_function": "scripts.return_mailing_labels_by_student_list",
            "report_description": "Generate Mailing Labels to go with a list of StudentIDs",
        },
        {
            "report_title": "Photo Roster from List of StudentIDs",
            "report_function": "scripts.return_photo_roster_by_studentid_lst",
            "report_description": "Generate student photo grid from list of StudentID numebers",
        },
        {
            "report_title": "Return Student Contact Tracing",
            "report_function": "scripts.return_contact_tracing",
            "report_description": "",
        }, 
        {
            "report_title": "Return Enhanced Line Schedule from List",
            "report_function": "scripts.return_enhanced_line_schedule_from_list",
            "report_description": "",
        },  
        {
            "report_title": "Return Student Staff Assignment",
            "report_function": "scripts.return_student_staff_assignment",
            "report_description": "",
        },                        
        {
            "report_title": "iLog Automation Form",
            "report_function": "scripts.return_ilog_automation",
            "report_description": "",
        },         
    ]
    return render_template(
        "organization/templates/organization/index.html", reports=reports
    )


@scripts.route("/organization/student_records_by_list", methods=["GET", "POST"])
def return_student_records_organized_by_class_list():

    if request.method == "GET":
        form = OrganizeStudentRecordsForm()
        return render_template(
            "organization/templates/organization/organize_student_records_form.html",
            form=form,
        )
    else:
        form = OrganizeStudentRecordsForm(request.form)
        f = organize_student_documents_by_list.main(form, request)

        download_name = f"organized_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


from app.scripts.organization.folder_mailing_labels_by_teacher import (
    main as folder_mailing_labels_by_teacher,
)


@scripts.route("/organization/teacher_bag_labels", methods=["GET", "POST"])
def return_bag_labels_for_student_documents_by_class_list():
    if request.method == "GET":
        form = FolderLabelsByTeacherForm()
        return render_template(
            "organization/templates/organization/return_teacher_bag_labels.html",
            form=form,
        )
    else:
        form = FolderLabelsByTeacherForm(request.form)
        f = folder_mailing_labels_by_teacher(form, request)

        download_name = (
            f"teacher_bag_labels_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        )

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


@scripts.route("/organization/counts_from_list", methods=["GET", "POST"])
def return_class_list_counts_from_list():
    if request.method == "GET":
        form = ClassListCountsFromSubsetForm()
        return render_template(
            "organization/templates/organization/class_list_counts_from_list_form.html",
            form=form,
        )
    else:
        form = ClassListCountsFromSubsetForm(request.form)

        student_subset_title = form.subset_title.data

        pvt = class_list_counts_from_list.main(form, request)
        pvt = pvt.style.set_table_attributes(
            'data-toggle="table" data-sortable="true" data-show-export="true" data-height="460"'
        )
        pvt_html = pvt.to_html(classes=["table", "table-sm"], index=False)

        data = {
            "reports": [
                {
                    "html": pvt_html,
                    "title": f"{student_subset_title} Analysis",
                },
            ]
        }
        return render_template("viewReport.html", data=data)


@scripts.route("/organization/rosters_from_list", methods=["GET", "POST"])
def return_class_rosters_from_list():
    if request.method == "GET":
        form = ClassRostersFromList()
        return render_template(
            "organization/templates/organization/class_rosters_from_list_form.html",
            form=form,
        )
    else:
        form = ClassRostersFromList(request.form)

        student_subset_title = form.subset_title.data

        f = class_rosters_from_list.main(form, request)

        download_name = (
            f"{student_subset_title}_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
        )

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


@scripts.route("/organization/career_day", methods=["GET", "POST"])
def return_career_day_reports():
    if request.method == "GET":
        form = CareerDayReportsForm()
        return render_template(
            "organization/templates/organization/career_day_form.html", form=form
        )
    else:
        form = CareerDayReportsForm(request.form)
        if form.output_file.data == "xlsx":
            df = career_day.process_spreadsheet(form, request)
            f = career_day.return_assignments_as_spreadsheet(df)
            download_name = (
                f"CareerDayAssignments_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
            )
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        if form.output_file.data == "pdf":
            df = career_day.process_spreadsheet(form, request)
            f = career_day.return_student_letters(df)

            download_name = (
                f"CareerDayAssignments_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
            )
            mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )


from app.scripts.organization import mailing_labels_by_period


@scripts.route("/organization/mailing_labels_by_period", methods=["GET", "POST"])
def return_mailing_labels_by_period():
    if request.method == "GET":
        form = MailingLabelsByPeriod()
        return render_template(
            "organization/templates/organization/mailing_labels_by_period.html",
            form=form,
        )
    else:
        form = MailingLabelsByPeriod(request.form)

        f = mailing_labels_by_period.main(form, request)

        download_name = "mailing_labels.pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )


import app.scripts.organization.photo_roster.main as photo_roster


@scripts.route("/organization/photo_roster_by_studentid_lst", methods=["GET", "POST"])
def return_photo_roster_by_studentid_lst():
    if request.method == "GET":
        form = ClassListCountsFromSubsetForm()
        return render_template(
            "organization/templates/organization/photo_roster.html",
            form=form,
        )
    else:
        form = ClassListCountsFromSubsetForm(request.form)

        f, download_name = photo_roster.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )

from app.main.forms import SelectStudentForm
from app.scripts.organization.contact_tracing.main import return_contact_tracing_results
@scripts.route("/organization/contact_tracing", methods=["GET", "POST"])
def return_contact_tracing():
    if request.method == "GET":
        form = SelectStudentForm()
        return render_template(
            "organization/templates/organization/contact_tracing/form.html",
            form=form,
        )
    else:
        form = SelectStudentForm(request.form)

        f, download_name = return_contact_tracing_results(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )


from app.scripts.organization.enhanced_line_schedule.forms import EnhancedLineScheduleForm
from app.scripts.organization.enhanced_line_schedule import main as enhanced_line_schedule
@scripts.route("/organization/enhanced_line_schedule", methods=["GET", "POST"])
def return_enhanced_line_schedule_from_list():
    if request.method == "GET":
        form = EnhancedLineScheduleForm()
        return render_template(
            "organization/templates/organization/enhanced_line_schedule/form.html",
            form=form,
        )
    else:
        form = EnhancedLineScheduleForm(request.form)
        f, download_name = enhanced_line_schedule.main(form, request)

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )
    

from app.scripts.organization.student_staff_assignment import main as student_staff_assignment
@scripts.route("/organization/student_staff_assignment", methods=["GET", "POST"])
def return_student_staff_assignment():

    f, download_name = student_staff_assignment.main()

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )