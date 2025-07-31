import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import files_df
import app.scripts.utils as utils


from app.scripts.graduation import graduation


@graduation.route("certification")
def return_graduation_certification_routes():
    reports = [
        {
            "report_title": "Generate Graduation Certification Spreadsheet",
            "report_function": "graduation.return_graduation_certification_spreadsheet",
            "report_description": "Return Generate Graduation Certification Spreadsheet reports",
        },
    ]
    return render_template(
        "graduation/templates/graduation/certification/index.html", reports=reports
    )


from app.scripts.graduation.certification import graduation_certification


@graduation.route("certification/spreadsheet")
def return_graduation_certification_spreadsheet():
    f, df = graduation_certification.main()
    school_year = session["school_year"]
    download_name = f"June{school_year+1}_grad_list.xlsx"
    # return df.to_html()
    return send_file(
        f,
        as_attachment=True,
        download_name=download_name,
    )
