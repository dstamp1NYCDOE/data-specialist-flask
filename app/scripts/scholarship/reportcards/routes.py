import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for

from app.scripts import scripts, files_df
import app.scripts.utils as utils


@scripts.route("/scholarship/reportcards/smartpass/", methods=["GET", "POST"])
def return_reportcard_reports():
    reports = [
        {
            "report_title": "Return Enhanced Student Report Cards",
            "report_function": "scripts.return_enhanced_student_reportcards",
            "report_description": "Analyze passes written in SmartPass",
        },
    ]
    return render_template(
        "scholarship/templates/scholarship/reportcards/index.html", reports=reports
    )


from app.scripts.scholarship.reportcards.forms import EnhancedReportCardForm
from app.scripts.scholarship.reportcards.return_report_cards import (
    main as return_report_cards,
)


@scripts.route(
    "/scholarship/reportcards/return_enhanced_reportcards", methods=["GET", "POST"]
)
def return_enhanced_student_reportcards():
    if request.method == "GET":
        form = EnhancedReportCardForm()
        return render_template(
            "scholarship/templates/scholarship/reportcards/reportcards_form.html",
            form=form,
        )
    else:

        form = EnhancedReportCardForm(request.form)
        f, download_name = return_report_cards(form, request)

        # return redirect(url_for('scripts.return_enhanced_student_reportcards'))
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )
