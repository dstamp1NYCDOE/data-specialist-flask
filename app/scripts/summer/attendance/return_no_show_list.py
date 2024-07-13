from app.scripts import scripts, files_df, photos_df, gsheets_df
from dotenv import load_dotenv
from flask import current_app, session
from io import BytesIO
import app.scripts.utils as utils
from app.scripts.summer.programming import programming_utils
import numpy as np
import os
import pandas as pd
import pygsheets


load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main():

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    RDAL_files = files_df[
        (files_df["report"] == "RDAL")
        & (files_df["year_and_semester"] == year_and_semester)
    ]

    lst_of_dfs = []
    for filename in RDAL_files["filename"]:
        df = utils.return_file_as_df(filename)
        lst_of_dfs.append(df)

    combined_rdal_df = pd.concat(lst_of_dfs)
    combined_rdal_df["num_of_days_absent"] = 1

    rdal_pvt = (
        pd.pivot_table(
            combined_rdal_df,
            index="StudentID",
            columns="Date",
            values="num_of_days_absent",
            aggfunc="sum",
        )
        .fillna(0)
        .reset_index()
    )

    df = pd.melt(rdal_pvt, id_vars="StudentID")

    students_lst = []
    for StudentID, absences_df in df.groupby("StudentID"):
        absences_df = absences_df.sort_values("Date", ascending=False)
        absences_lst = [int(x) for x in absences_df["value"]]
        consecutive_absences = return_consective_absences(absences_lst)
        if consecutive_absences == sum(absences_lst):
            student_dict = {
                "StudentID": StudentID,
                "consecutive_absences": consecutive_absences,
                "total_absences": sum(absences_lst),
            }
            students_lst.append(student_dict)

    no_show_df = pd.DataFrame(students_lst)
    no_show_lst = no_show_df['StudentID']

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename).fillna(0)

    student_info_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Student DOE Email",
        "Phone",
    ]
    student_info_df = cr_3_07_df[student_info_cols]
    student_info_df["Phone"] = student_info_df["Phone"].apply(lambda x: str(int(x)))
    student_info_df["Phone"] = student_info_df["Phone"].str.replace(
        "^(\d{3})(\d{3})(\d{4})$", r"(\1)\2-\3"
    )

    

    f = BytesIO()

    student_info_df = student_info_df[student_info_df['StudentID'].isin(no_show_lst)]
    student_info_df[student_info_cols].to_csv(f,index=False)
    f.seek(0)
    return f



def return_consective_absences(absences_lst):
    consecutive_absences = 0
    for absence in absences_lst:
        if absence == 0:
            return consecutive_absences
        else:
            consecutive_absences += 1
    return consecutive_absences