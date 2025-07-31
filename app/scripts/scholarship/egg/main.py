import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for

from app.scripts.programming.jupiter.return_master_schedule import (
    return_jupiter_course,
    return_jupiter_schedule,
)

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"


    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.egg_file.name]
    semester = form.semester.data
    egg_file_df = pd.read_excel(filename, sheet_name='Grade_Data').fillna("")


    jupiter_master_schedule_df = return_jupiter_schedule()
    jupiter_master_schedule_df = jupiter_master_schedule_df[
        ["CourseCode", "SectionID", "JupiterCourse", "JupiterSection"]
    ]

    dff = egg_file_df.merge(
        jupiter_master_schedule_df,
        left_on=["Course", "Sec"],
        right_on=["CourseCode", "SectionID"],
        how="left",
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, 'rosters_and_grades', year_and_semester=year_and_semester
    )
    df = utils.return_file_as_df(filename)   
    df = df[df['Term']==semester]
    df = df.rename(columns={'Course':'JupiterCourse','Section':'JupiterSection'})

    dfff = dff.merge(
        df,
        left_on=["JupiterCourse", "JupiterSection",'StudentID'],
        right_on=["JupiterCourse", "JupiterSection",'StudentID'],
        how="left",
    )  
    
    is_final = False
    dfff["ReconciledMark"] = dfff.apply(
        reconcile_egg_and_jupiter, args=(is_final,), axis=1
    )

    dfff = dfff.drop_duplicates(
        subset=["StudentID", "Course", "Sec"],
    )

    print(dfff)

    download_name = f"Egg.xlsx"
    
    f = BytesIO()
    dfff.to_excel(f,index=False)
    f.seek(0)

    return f, download_name


def convert_final_mark(Mark, is_final):
    try:
        if Mark < 50:
            if is_final:
                return 55
            else:
                return 45
        if Mark < 65:
            return 55
        if Mark > 100:
            return 100
        return round(Mark)
    except:
        return Mark
    

pass_fail_courses = [
    "GAS81QA",
    "GAS82QA",
    "GAS81QB",
    "GAS82QB",
    "GLS11QYL",
    "GLS11QA",
    "GLS11QB",
    # "GQS21",
]

def reconcile_egg_and_jupiter(row, is_final):
    egg_mark = row["Mark"]
    jupiter_mark = row["Pct"]
    Course = row["Course"]

    if egg_mark:
        final_mark = egg_mark
    else:
        final_mark = jupiter_mark

    if Course in pass_fail_courses:
        return convert_final_mark_to_pass_fail(final_mark)
    return convert_final_mark(final_mark, is_final)


def convert_final_mark_to_pass_fail(Mark):
    try:
        if Mark < 65:
            return "F"
        return "P"
    except:
        return Mark    