import json
import pandas as pd
from io import BytesIO

from flask import render_template, request, send_file

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate

import app.scripts.utils as utils
import app.scripts.commutes.utils as commute_utils

from app.scripts import scripts, files_df

from app.scripts.commutes.forms import CommuteByClassForm

from app.scripts.commutes.create_student_commute_letter import main as create_student_student_letter

@scripts.route("/commutes")
def return_commute_reports():
    commute_reports = [
        {
            "report_title": "Student Commutes by Class",
            "report_function": "scripts.generate_commute_class_report",
            "report_description":"Select a class list to generate student commute info"
        }
    ]
    return render_template(
        "commutes/templates/commutes/index.html", commute_reports=commute_reports
    )

@scripts.route("/commutes/class_report/", methods=["GET", "POST"])
def generate_commute_class_report():
    if request.method == 'GET':
        data = {"form": CommuteByClassForm()}
        return render_template("commutes/templates/commutes/commutes_by_class.html",data=data)
    else:
        course_and_section = request.form.get("course_and_section")
        course, section = course_and_section.split("/")
        cr_1_01_filename = utils.return_most_recent_report(files_df, "1_01")
        cr_1_01_df = utils.return_file_as_df(cr_1_01_filename)

        cr_1_01_df = cr_1_01_df[(cr_1_01_df['Course']==course) & (cr_1_01_df['Section']==int(section))]
        StudentIDs = cr_1_01_df['StudentID']

        student_commutes_filename = utils.return_most_recent_report(files_df, "student_commutes")
        with open(student_commutes_filename, "r") as j:
            contents = json.loads(j.read())
        student_commutes_df = pd.DataFrame(contents)

        starting_station_stats = pd.pivot_table(
            student_commutes_df,
            index="starting_station",
            values="StudentID",
            aggfunc="count",
        ).fillna(0).reset_index()
        starting_station_stats.columns = ['starting_station','#_of_other_students']

        student_commutes_df = student_commutes_df.merge(
            starting_station_stats, on=["starting_station"], how="left"
        ).fillna('Walking Distance')

        student_commutes_df = student_commutes_df[student_commutes_df["StudentID"].isin(StudentIDs)]
        student_commutes_df["student_steps"] = student_commutes_df["API_Response"].apply(
            commute_utils.return_list_of_directions
        )
        student_commutes_df["flowables"] = student_commutes_df.apply(
            create_student_student_letter, axis=1
        )

        flowables = student_commutes_df['flowables'].explode().to_list()

        filename = "data/student_commute_letters.pdf"
        f = BytesIO()
        my_doc = SimpleDocTemplate(
            f,
            pagesize=letter,
            topMargin=0.50 * inch,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            bottomMargin=0.5 * inch,
        )
        my_doc.build(flowables)

        f.seek(0)
        download_name = f"StudentCommuteLetters.pdf"

        return send_file(f, as_attachment=True, download_name=download_name)
