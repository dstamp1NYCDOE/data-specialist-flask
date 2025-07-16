import json
import pandas as pd
import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file

from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.organization.geocoding.process_addresses import main as process_addresses
from app.scripts.organization.geocoding.process_community_districts import main as process_community_districts



@scripts.route("/organization/geocoding")
def return_geocoding_reports():
    reports = [
        {
            "report_title": "Process student addresses and return geocoding",
            "report_function": "scripts.return_process_addresses",
            "report_description": "",
        },
        {
            "report_title": "Process student addresses and return community districts",
            "report_function": "scripts.return_community_districts",
            "report_description": "",
        },        
    ]
    return render_template(
        "organization/templates/organization/geocoding/index.html", reports=reports
    )

@scripts.route("/organization/geocoding/process", methods=["GET", "POST"])
def return_process_addresses():
    df = process_addresses()
    return df.to_html()

@scripts.route("/organization/geocoding/return_community_districts", methods=["GET", "POST"])
def return_community_districts():
    df = process_community_districts()
    return df.to_html()
