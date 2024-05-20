import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

from app.scripts.classwork.forms import MarkingPeriodChoiceForm

import app.scripts.classwork.scripts.failing_one_class_missing_assignments_reports as failing_one_class_missing_assignments_reports
import app.scripts.classwork.scripts.failing_all_classes_assignment_report as failing_all_classes_assignment_report
import app.scripts.classwork.scripts.assignments_analysis as assignments_analysis


@scripts.route("/classwork")
def return_classwork_reports():
    reports = [
        {
            "report_title": "Create Assignments Letter for Students Failing One Class",
            "report_function": "failing_one_class_missing_assignments_reports",
            "report_description": "Return student facing letters for missing + low assignments in the single course they are failing",
            "report_form": MarkingPeriodChoiceForm(
                meta={
                    "title": "MissingAssignmentsForFailingOneCourseForm",
                    "type": "marking_period_dropdown",
                }
            ),
        },
        {
            "report_title": "Spreadsheet of Students Failing All Classes",
            "report_function": "failing_all_classes_assignment_report",
            "report_description": "Return Spreadsheet of Students Failing all courses",
            "report_form": MarkingPeriodChoiceForm(
                meta={
                    "title": "failing_all_classes_assignment_report",
                    "type": "marking_period_dropdown",
                }
            ),
        },
        {
            "report_title": "Student Assignment Analysis",
            "report_function": "assignments_analysis",
            "report_description": "Return Spreadsheet of Students Assignments Analysis",
            "report_form": MarkingPeriodChoiceForm(
                meta={
                    "title": "assignments_analysis",
                    "type": "marking_period_dropdown",
                }
            ),
        },
    ]
    return render_template("classwork/templates/classwork/index.html", reports=reports)


@scripts.route("/classwork/<report_function>", methods=["GET", "POST"])
def return_classwork_report(report_function):
    if request.method == "GET":
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for("scripts.return_classwork_reports"))
    data = {"form": request.form}
    school_year = session["school_year"]
    term = session["term"]

    reports_dict = {
        "failing_one_class_missing_assignments_reports": {
            "function": failing_one_class_missing_assignments_reports.main,
            "download_name": f"{school_year}_{term}_StudentsFailingOneClassReport.pdf",
        },
        "failing_all_classes_assignment_report": {
            "function": failing_all_classes_assignment_report.main,
            "download_name": f"{school_year}_{term}_StudentsFailingAllClasses.xlsx",
        },
        "assignments_analysis": {
            "function": assignments_analysis.main,
            "download_name": f"{school_year}_{term}_JupiterAssignmentsAnalysis.xlsx",
        },
    }
    report_dict = reports_dict.get(report_function)
    if report_dict:
        f = report_dict["function"](data)
        download_name = report_dict["download_name"]
        return send_file(f, as_attachment=True, download_name=download_name)
    else:
        flash(f"Resubmit form to run {report_function}", category="warning")
        return redirect(url_for("scripts.return_classwork_reports"))
