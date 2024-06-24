import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import files_df
import app.scripts.utils as utils


from app.scripts.graduation import graduation


@graduation.route("")
def return_graduation_routes():
    reports = [
        {
            "report_title": "Graduation Certification Scripts",
            "report_function": "graduation.return_graduation_certification_routes",
            "report_description": "Return graduation certification Scripts",
        },
        {
            "report_title": "Diploma Mockup",
            "report_function": "graduation.return_diploma_mockup",
            "report_description": "Return diploma mockup from uploaded Graduate Certification",
        },
    ]
    return render_template(
        "graduation/templates/graduation/index.html", reports=reports
    )
