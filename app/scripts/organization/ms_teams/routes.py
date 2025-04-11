import json
import pandas as pd
import datetime as dt
from io import BytesIO
from requests import post
import os

from flask import render_template, request, send_file
from werkzeug.utils import secure_filename


import app.scripts.utils as utils


from app.scripts import scripts, files_df

ms_teams_HSFI_support_webhook_url = os.getenv("ms_teams_HSFI_support_webhook_url")


@scripts.route("/organization/ms_teams_test", methods=["GET", "POST"])
def return_post_to_ms_teams_test():
    if request.method == "GET":

        filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
        rosters_df = utils.return_file_as_df(filename)
        rosters_df = (
            rosters_df[["StudentID", "Course", "Section"]].drop_duplicates().head(10)
        )

        body = {
            "method": "chat",
            "posts": [
                {"to": "dstampone@schools.nyc.gov", "message": "test message"},
            ],
        }

        response = post(
            ms_teams_HSFI_support_webhook_url,
            json=body,
            headers={"Content-Type": "application/json"},
        )
        print(response)
        return ""
    else:
        return ""
