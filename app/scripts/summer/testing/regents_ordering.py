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

    student_exam_registration = request.files[
        form.combined_regents_registration_spreadsheet.name
    ]
    df_dict = pd.read_excel(student_exam_registration, sheet_name=None)

    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name != "HomeLangDropdown"
    ]
    df = pd.concat(dfs_lst)

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    exams_in_order = regents_calendar_df.sort_values(by=["Day", "Time", "ExamTitle"])[
        "ExamTitle"
    ]

    exam_dict_lst = []
    for exam in exams_in_order:

        exam_count_pvt = pd.pivot_table(
            df[df[exam]], index=exam, aggfunc="count", values="StudentID"
        )

        exam_dict = {
            "ExamTitle": exam,
            "num_of_exams": exam_count_pvt.loc[True, "StudentID"],
        }
        large_print_pvt = pd.pivot_table(
            df[df["large_print?"] & df[exam]],
            index=exam,
            aggfunc="count",
            values="StudentID",
        )
        if large_print_pvt.to_dict():
            exam_dict["num_of_exams"] = large_print_pvt.loc[True, "StudentID"]

        enl_count_pvt = pd.pivot_table(
            df[df["ENL?"] & df[exam]],
            index=exam,
            columns="HomeLang",
            aggfunc="count",
            values="StudentID",
        )
        if enl_count_pvt.to_dict():
            enl_count_pvt = {
                HomeLang: TRUE[True] for (HomeLang, TRUE) in enl_count_pvt.items()
            }
        else:
            enl_count_pvt = {}

        exam_dict = exam_dict | enl_count_pvt
        exam_dict_lst.append(exam_dict)

    df = pd.DataFrame(exam_dict_lst)
    return df
