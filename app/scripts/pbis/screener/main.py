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

    download_name = f"UniveralScreenerAnalysis.xlsx"

    return f, download_name


def return_screener_questions(columns):
    return [x for x in columns if "?" in x]


def process_screener_data(dfs_dict):
    dfs_lst = dfs_dict.values()
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


def return_teacher_completition_pvt(df, screener_questions):
    student_pvt = pd.concat(
        [
            pd.pivot_table(
                df,
                index="Teacher1",
                columns=question,
                values="StudentID",
                aggfunc="count",
            ).fillna(0)
            for question in screener_questions
        ],
        axis=1,
        keys=screener_questions,
    )
    return [("Combined", student_pvt)]



def return_results_by_questions(df, screener_questions):
    id_vars = [x for x in df.columns if x not in screener_questions]

    results = []
    for question, sheet_name in zip(screener_questions,['Q1','Q2','Q3']):
        student_pvt = pd.pivot_table(
            df,
            index=["StudentID", "LastName", "FirstName", "Counselor"],
            columns=question,
            values="Teacher1",
            aggfunc="count",
        )
        results.append((sheet_name, student_pvt))
    return results


def return_student_pivot(df, screener_questions):
    id_vars = [x for x in df.columns if x not in screener_questions]
    dff = df.melt(id_vars=id_vars, var_name="Question", value_name="TeacherResponse")
    student_pvt = pd.pivot_table(
        dff,
        index=["StudentID", "LastName", "FirstName", "Counselor"],
        columns="TeacherResponse",
        values="Teacher1",
        aggfunc="count",
    )
    return [("StudentPivot", student_pvt)]


def return_results_by_counselor(df, screener_questions):
    sheets = []

    for counselor, dff in df.groupby("Counselor"):

        index = ["StudentID", "LastName", "FirstName"]
        student_pvt = pd.concat(
            [
                pd.pivot_table(
                    dff,
                    index=index,
                    columns=question,
                    values="Teacher1",
                    aggfunc="count",
                ).fillna(0)
                for question in screener_questions
            ],
            axis=1,
            keys=screener_questions,
        )

        sheets.append(
            (counselor, student_pvt),
        )

    return sheets


def return_download_file(df):

    screener_questions = return_screener_questions(df.columns)

    sheets = []

    # counselor_sheets = return_results_by_counselor(df, screener_questions)
    # sheets.extend(counselor_sheets)

    teacher_completion_sheet = return_teacher_completition_pvt(df, screener_questions)
    sheets.extend(teacher_completion_sheet)

    student_pvt_sheet = return_student_pivot(df, screener_questions)
    sheets.extend(student_pvt_sheet)

    sheets_temp = return_results_by_questions(df, screener_questions)
    sheets.extend(sheets_temp)

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
