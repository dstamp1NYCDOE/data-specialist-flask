from flask import jsonify, request

import app.scripts.utils.utils as utils
from app.api_1_0 import api, files_df


@api.route("/students")
def return_students():
    year_and_semester = request.args.get("year_and_semester")
    if year_and_semester:
        cr_3_07_filename = utils.return_most_recent_report_by_semester(
            files_df, "3_07", year_and_semester
        )
    else:
        cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")

    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    cr_3_07_df = cr_3_07_df.sort_values(by=["LastName", "FirstName", "StudentID"])
    students_lst = cr_3_07_df[["StudentID", "LastName", "FirstName"]].to_dict("records")

    return jsonify(students_lst)


@api.route("/students/<StudentID>")
def return_student_info(StudentID):
    year_and_semester = request.args.get("year_and_semester")
    if year_and_semester:
        cr_3_07_filename = utils.return_most_recent_report_by_semester(
            files_df, "3_07", year_and_semester
        )
    else:
        cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")

    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)

    cr_3_07_df = cr_3_07_df[cr_3_07_df["StudentID"] == int(StudentID)]

    students_lst = cr_3_07_df.to_dict("records")

    return jsonify(students_lst)
