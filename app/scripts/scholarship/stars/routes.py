import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for

from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/scholarship/stars/", methods=["GET", "POST"])
def return_scholarship_stars_report():
    reports = [
        {
            "report_title": "Return STARs Scholarship Report",
            "report_function": "scripts.return_stars_scholarship_report",
            "report_description": "Return historical STARs scholarship report for a staff member.",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/stars/index.html", reports=reports
    )


from app.scripts.scholarship.stars.forms import StaffMemberDropDown
from app.scripts.scholarship.stars.scholarship_report import (
    main as scholarship_report,
)

from app.scripts.scholarship.stars.scholarship_report import (
    return_teacher_names as return_teacher_names,
)


@scripts.route("/scholarship/stars/scholarship_report", methods=["GET", "POST"])
def return_stars_scholarship_report():
    if request.method == "GET":
        form = StaffMemberDropDown()
        form.staff_member.choices = return_teacher_names()

        return render_template(
            "scholarship/templates/scholarship/stars/scholarship_report_form.html",
            form=form,
        )
    else:
        form = StaffMemberDropDown(request.form)
        return scholarship_report(form, request)
        f, download_name = scholarship_report(form, request)
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
