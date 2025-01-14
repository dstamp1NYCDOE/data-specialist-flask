import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.testing.regents.day_of_org.main import return_exambook_for_index


@scripts.route("testing/regents/day_of_org")
def return_regents_day_of_org():
    exambook = return_exambook_for_index()
    return render_template(
        "/testing/regents/day_of_org/templates/day_of_org/index.html", exambook=exambook
    )


from app.scripts.testing.regents.day_of_org.student_labels import (
    main as return_student_labels,
)


@scripts.route("/testing/regents/day_of_org/<course>/<file>")
def return_regents_day_of_org_files(course, file):

    if file == "StudentLabels":
        f, download_name = return_student_labels(course, request)
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
        # mimetype="application/pdf",
    )
