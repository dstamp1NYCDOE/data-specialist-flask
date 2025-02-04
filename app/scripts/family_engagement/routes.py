import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session


from app.scripts import scripts, files_df
import app.scripts.utils as utils



@scripts.route("/family_engagement")
def return_family_engagement_reports():
    reports = [
        {
            "report_title": "Weekly Family Engagement Assignment",
            "report_function": "scripts.return_family_engagement_weekly_assignment",
            "report_description": "Return weekly family engagement assignment based on Jupiter data",
        },
    ]
    title = "Family Engagement"
    return render_template(
        "section.html",
        reports=reports,
        title=title,
    )