import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.programming.post_summer.main import main as post_summer_main

@scripts.route("/programming/updated_requests_post_summer", methods=["GET", "POST"])
def return_updated_requests_post_summer():
    """
    Return updated requests for post-summer programming.
    1. Changes based on credits/regents scores
    2. Requests for incoming 10th graders
    3. Requests for incoming 9th graders
    """
    # return post_summer_main()
    f, download_name = post_summer_main()
    return send_file(f, as_attachment=True, download_name=download_name)
