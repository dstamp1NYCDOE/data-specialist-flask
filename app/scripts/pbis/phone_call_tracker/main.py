import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.file.name]

    dfs_dict = pd.read_excel(filename, sheet_name=None)
    df = process_screener_data(dfs_dict)

    f = return_download_file(df)

    download_name = f"PhoneCallTrackerAnalysis.xlsx"

    return f, download_name


def process_screener_data(dfs_dict):

    dfs_lst = []
    for teacher, df in dfs_dict.items():
        df["Teacher"] = teacher
        dfs_lst.append(df)

    # dfs_lst = dfs_dict.values()

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_49_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester=year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor"]]

    df = pd.concat(dfs_lst)
    df = df.merge(cr_1_49_df, on="StudentID", how="left")
    return df


def return_teacher_completition_pvt(df):

    pvt_tbl = pd.pivot_table(
        df,
        index=["Teacher"],
        columns="Action",
        values="StudentID",
        aggfunc="count",
        margins=True,
    ).fillna(0)

    return [("teacher_completion", pvt_tbl)]


def return_student_pvt_pvt(df):

    pvt_tbl = pd.pivot_table(
        df,
        index=["StudentID", "LastName", "FirstName", "Counselor"],
        columns="Action",
        values="Teacher",
        aggfunc=lambda x: list(x),
        margins=True,
    )
    pvt_tbl = pvt_tbl.drop("All", axis=0)
    pvt_tbl["Total"] = pvt_tbl["All"].apply(lambda x: len(x))
    pvt_tbl = pvt_tbl.sort_values(by=["Total"], ascending=[False])

    return [("student_pvt", pvt_tbl)]


def return_download_file(df):

    sheets = []

    # counselor_sheets = return_results_by_counselor(df)
    # sheets.extend(counselor_sheets)

    teacher_completion_sheet = return_teacher_completition_pvt(df)
    sheets.extend(teacher_completion_sheet)

    student_pvt_sheet = return_student_pvt_pvt(df)
    sheets.extend(student_pvt_sheet)

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()
    f.seek(0)

    return f
