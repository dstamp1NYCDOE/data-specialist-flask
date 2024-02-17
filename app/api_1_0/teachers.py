from flask import jsonify, request

import app.scripts.utils as utils
from app.api_1_0 import api, files_df

@api.route("/teachers")
def return_teachers():
    year_and_semester = request.args.get('year_and_semester')
    if year_and_semester:
        cr_6_31_filename = utils.return_most_recent_report_by_semester(
            files_df, "6_31", year_and_semester
        )
    else:
        cr_6_31_filename = utils.return_most_recent_report(files_df,'6_31')

    cr_6_31_df = utils.return_file_as_df(cr_6_31_filename).dropna()

    teachers_list = cr_6_31_df["NickName"].to_list()

    return jsonify(teachers_list)
