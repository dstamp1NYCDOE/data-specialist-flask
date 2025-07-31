import datetime as dt
import pandas as pd
from io import BytesIO
import os

from flask import render_template, request, send_file, session, current_app


from app.scripts import scripts, files_df, gsheets_df
import app.scripts.utils as utils


def return_exambook_for_index():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    gsheet_url = utils.return_gsheet_url_by_title(
        gsheets_df, "regents_exam_book", year_and_semester
    )

    exam_book_df = utils.return_google_sheet_as_dataframe(gsheet_url, sheet="ExamBook")

    exams_lst = []
    for (day, time, exam, course), sections_df in exam_book_df.groupby(
        ["Day", "Time", "ExamTitle", "Course Code"]
    ):
        temp_dict = {
            "ExamTitle": exam,
            "Course": course,
            "Day": day,
            "Time": time,
            "Rooms": sections_df["Room"].sort_values().unique().tolist(),
            "Sections": sections_df["Section"].sort_values().unique().tolist(),
        }
        exams_lst.append(temp_dict)

    return exams_lst
