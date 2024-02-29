from flask import jsonify
from app.api_1_0 import api
from app import cache

import pysftp

import os

import pandas as pd

JUPITER_SFTP_HOSTNAME = os.getenv("JUPITER_SFTP_HOSTNAME")
JUPITER_SFTP_USERNAME = os.getenv("JUPITER_SFTP_USERNAME")
JUPITER_SFTP_PASSWORD = os.getenv("JUPITER_SFTP_PASSWORD")


@api.route("/jupiter/<filename>")
@cache.cached(timeout=50)
def return_jupiter_file(filename):
    with pysftp.Connection(
        JUPITER_SFTP_HOSTNAME,
        username=JUPITER_SFTP_USERNAME,
        password=JUPITER_SFTP_PASSWORD,
    ) as sftp:
        df = pd.read_csv(sftp.open(filename))
    return jsonify(df.to_dict(orient='records'))
