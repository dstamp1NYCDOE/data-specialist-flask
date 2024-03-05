import pysftp

import os

import pandas as pd
import datetime as dt
from flask import render_template, request, Blueprint, redirect, url_for, flash, current_app, session

JUPITER_SFTP_HOSTNAME = os.getenv("JUPITER_SFTP_HOSTNAME")
JUPITER_SFTP_USERNAME = os.getenv("JUPITER_SFTP_USERNAME")
JUPITER_SFTP_PASSWORD = os.getenv("JUPITER_SFTP_PASSWORD")


def main(report,year_and_semester):
    with pysftp.Connection(
        JUPITER_SFTP_HOSTNAME,
        username=JUPITER_SFTP_USERNAME,
        password=JUPITER_SFTP_PASSWORD,
    ) as sftp:
        jupiter_filename = f"{report}.csv"

        path = os.path.join(
            current_app.root_path, f"data/{year_and_semester}/{report}"
        )
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
        today = dt.datetime.today().strftime('%Y-%m-%d')

        local_filename = f"{year_and_semester}_9999-12-31_{report}.csv"
        local_filename = os.path.join(path, local_filename)

        sftp.get(jupiter_filename, local_filename)

    return ''
