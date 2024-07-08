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

    sheets_to_ignore = ["Directions", "HomeLangDropdown"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")

    filename = utils.return_most_recent_report(files_df, "s_01")
    cr_s_01_df = utils.return_file_as_df(filename)

    enrolled_students = cr_s_01_df["StudentID"]

    walkins_df = df[df["StudentID"].isin(enrolled_students)]

    walkins_df = walkins_df.dropna(subset=["StudentID"])
    walkins_df["GradeLevel"] = ""
    walkins_df["OfficialClass"] = ""
    walkins_df["Section"] = 1
    walkins_df["Action"] = "Add"

    exams = [
        ("ELA", "EXRCG"),
        ("Alg1", "MXRFG"),
        ("Global", "HXRCG"),
        ("Alg2", "MXRNG"),
        ("USH", "HXRKG"),
        ("ES", "SXRUG"),
        ("Chem", "SXRXG"),
        ("Geo", "MXRKG"),
        ("LE", "SXRKG"),
    ]

    output_df_lst = []
    output_cols_needed = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "Section",
        "Action",
    ]

    for exam, exam_code in exams:
        to_register_df = walkins_df[walkins_df[exam] == True]
        to_register_df["Course"] = exam_code
        to_register_df = to_register_df[output_cols_needed]
        output_df_lst.append(to_register_df)

    to_register_df = pd.concat(output_df_lst)

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    to_register_df.to_excel(writer)
    writer.close()
    f.seek(0)
    return f
