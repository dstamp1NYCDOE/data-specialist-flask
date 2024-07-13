import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session, redirect, url_for

import app.scripts.summer.attendance.update_RDAL_spreadsheets as update_rdal_spreadsheets


def main(form, request):
    filename = request.files[form.rdal_file.name]
    class_date = form.class_date.data
    f, rdal_df = process_rdal_csv_and_save(filename, class_date)
    download_name = f"RDAL_{class_date}.csv"

    
    return f, download_name


def process_rdal_csv_and_save(filename, class_date):

    rdal_df = pd.read_csv(filename, skiprows=3)
    rdal_df["Date"] = class_date

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = f"{year_and_semester}_{class_date}_RDAL.xlsx"

    path = os.path.join(current_app.root_path, f"data/{year_and_semester}/RDAL")
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    full_filename = os.path.join(path, filename)

    rdal_df = rdal_df.rename(
        columns={
            "Student ID": "StudentID",
        }
    )
    rdal_df[["StudentID", "Date"]].to_excel(full_filename, index=False)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename).fillna(0)

    student_info_cols = [
        "StudentID",
        "Student DOE Email",
        "ParentLN",
        "ParentFN",
        "Phone",
    ]
    student_info_df = cr_3_07_df[student_info_cols]
    student_info_df["Phone"] = student_info_df["Phone"].apply(lambda x: str(int(x)))
    student_info_df["Phone"] = student_info_df["Phone"].str.replace(
        "^(\d{3})(\d{3})(\d{4})$", r"(\1)\2-\3"
    )

    rdal_df = rdal_df.merge(student_info_df, on=["StudentID"], how="left")

    f = BytesIO()

    rdal_df[["Student Last Name", "First Name", "Phone", "Student DOE Email"]].to_csv(
        f, index=False
    )

    f.seek(0)
    return f, rdal_df[["StudentID", "Date"]]
