from flask import jsonify, request

import app.scripts.utils as utils
from app.api_1_0 import api, files_df

@api.route("/files")
def return_files():
    year_and_semester = request.args.get('year_and_semester')
    report = request.args.get("report")
    files_dff = files_df
    if year_and_semester:
        files_dff = files_dff[files_dff["year_and_semester"] == year_and_semester]
    if report:
        files_dff = files_dff[files_dff["report"] == report]

    return jsonify(files_dff.to_dict("records"))
