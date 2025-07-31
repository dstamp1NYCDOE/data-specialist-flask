import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils


@scripts.route("/programming/spring", methods=["GET", "POST"])
def return_programming_spring_scripts():
    reports = [
        {
            "report_title": "Return Spring Master Schedule From Fall",
            "report_function": "scripts.return_programming_spring_return_master_schedule",
            "report_description": "Process Fall Master Schedule and Return Spring",
        },
    ]

    return render_template(
        "/programming/templates/programming/spring/index.html", reports=reports
    )


from app.scripts.programming.spring_scheduling import return_spring_master_schedule


@scripts.route("/programming/spring/return_master_schedule", methods=["GET", "POST"])
def return_programming_spring_return_master_schedule():
    f, download_name = return_spring_master_schedule.main()

    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )
