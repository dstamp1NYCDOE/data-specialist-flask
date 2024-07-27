import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    exams_in_order = regents_calendar_df.sort_values(by=["Day", "Time", "ExamTitle"])[
        "ExamTitle"
    ]

    student_exam_registration = request.files[
        form.combined_regents_registration_spreadsheet.name
    ]
    df_dict = pd.read_excel(student_exam_registration, sheet_name=None)

    sheets_to_ignore = ["Directions", "HomeLangDropdown","YABC"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")

    filename = utils.return_most_recent_report(files_df, "s_01")
    cr_s_01_df = utils.return_file_as_df(filename)

    enrolled_students = cr_s_01_df["StudentID"]

    students_to_add = df[~df["StudentID"].isin(enrolled_students)]
    students_to_add = students_to_add.sort_values(by=["LastName", "FirstName"])
    students_to_add["#_of_exams"] = students_to_add[exams_in_order].sum(axis=1)
    students_to_add = students_to_add[students_to_add["#_of_exams"] > 0]
    students_to_add["StudentID"] = students_to_add["StudentID"].apply(
        lambda x: str(x)[0:9]
    )

    cols = ["StudentID", "LastName", "FirstName", "Sending school", "school_name"]
    return students_to_add[cols]
