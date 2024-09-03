import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.programming.jupiter.forms import JupiterMasterScheduleForm

@scripts.route("/programming/jupiter")
def return_programming_jupiter_reports():
    jupiter_master_schedule_form = JupiterMasterScheduleForm()
    form_cards = [
        {
            "Title": "Return Jupiter Master Schedule",
            "Description": "Return spreadsheet to upload to Jupiter",
            "form": jupiter_master_schedule_form,
            "route": "scripts.return_student_vetting_report",
        },
    ]

    return render_template(
        "/programming/templates/programming/index.html", form_cards=form_cards
    )

import app.scripts.programming.jupiter.return_master_schedule as return_master_schedule
@scripts.route("/programming/jupiter/return_master_schedule", methods=['GET','POST'])
def return_jupiter_master_schedule():
    if request.method == 'GET':
        pass
    else:
        form = JupiterMasterScheduleForm(request.form)
        return return_master_schedule.return_student_jupiter(request, form)
        return return_master_schedule.main(request, form)
        f, download_name = return_master_schedule.main(request, form)
        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
        )