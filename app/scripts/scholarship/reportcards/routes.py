import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, redirect, url_for

from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils


@scripts.route("/scholarship/reportcards/", methods=["GET", "POST"])
def return_reportcard_reports():
    reports = [
        {
            "report_title": "Return Enhanced Student Report Cards",
            "report_function": "scripts.return_enhanced_student_reportcards",
            "report_description": "Return student enhanced report card based on a variety of reports",
        },
        {
            "report_title": "Return Enhanced Progress Report Cards",
            "report_function": "scripts.return_enhanced_progress_report",
            "report_description": "Return student progress report with attendance based only on Jupiter data",
        },        
    ]
    return render_template(
        "scholarship/templates/scholarship/reportcards/index.html", reports=reports
    )


from app.scripts.scholarship.reportcards.forms import EnhancedReportCardForm
from app.scripts.scholarship.reportcards.return_report_cards import (
    main as return_report_cards,
)
from app.scripts.scholarship.reportcards.return_jupiter_progress_report import (
    main as return_jupiter_progress_report,
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

@scripts.route(
    "/scholarship/reportcards/return_enhanced_progress_report", methods=["GET", "POST"]
)
def return_enhanced_progress_report():
    f, download_name = return_jupiter_progress_report()

    # return redirect(url_for('scripts.return_enhanced_student_reportcards'))
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )
