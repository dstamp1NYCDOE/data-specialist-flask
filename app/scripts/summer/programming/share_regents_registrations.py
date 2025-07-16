from zipfile import ZipFile
from io import BytesIO
from flask import current_app, session
from dotenv import load_dotenv

import pygsheets
import pandas as pd

import os
import numpy as np

import datetime as dt
from app.scripts import scripts, files_df, photos_df, gsheets_df
import app.scripts.utils as utils

from app.scripts.summer.programming import programming_utils

load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## process current class list
    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)
    master_schedule_df = master_schedule_df.rename(columns={"Course Code": "Course"})
    master_schedule_df["Cycle"] = master_schedule_df["Days"].apply(
        programming_utils.convert_days_to_cycle
    )
    code_deck = master_schedule_df[["Course", "Course Name"]].drop_duplicates()
    master_schedule_df = master_schedule_df[["Course", "Section", "Cycle"]]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)

    cr_1_01_df = cr_1_01_df.merge(
        master_schedule_df, on=["Course", "Section"], how="left"
    )
    cr_1_01_df = cr_1_01_df.merge(code_deck, on=["Course"], how="left")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df = cr_3_07_df[
        ["StudentID", "Student DOE Email", "ParentLN", "ParentFN", "Phone"]
    ]
    cr_1_01_df = cr_1_01_df.merge(cr_3_07_df, on=["StudentID"], how="left")

    filename = utils.return_most_recent_report(files_df, "s_01")
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_1_01_df = cr_1_01_df.merge(
        cr_s_01_df[["StudentID", "school_name"]], on=["StudentID"], how="left"
    )

    exams_df = cr_1_01_df[cr_1_01_df['Course'].str[1] == 'X']
    

    exams_pvt = pd.pivot_table(exams_df,index='StudentID',columns='Course Name',values='Section',aggfunc='max')
    exams_pvt = exams_pvt >= 1
    exams_pvt = exams_pvt.replace({True:'Y',False:'N'})
    
    exams_lst = exams_pvt.columns.tolist()
    exams_pvt = exams_pvt.reset_index()
    
    

    cr_1_01_df = cr_1_01_df.merge(exams_pvt, on='StudentID',how='left').fillna('')
    cr_1_01_df.replace("N", "", inplace=True)

    teacher_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "Section",
        "Period",
        "Course Name",
        "Cycle",
        "school_name",
        "Student DOE Email",
    ] + exams_lst

    ## get gsheet

    summer_school_gradebooks_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_gradebooks_hub", year_and_semester
    )

    summer_school_gradebooks_hub_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url
    )

    for index, gradebook in summer_school_gradebooks_hub_df.iterrows():
        gradebook_url = gradebook["Gradebook URL"]
        teacher_name = gradebook["TeacherName"]
        df = cr_1_01_df[cr_1_01_df["Teacher1"] == teacher_name]
        df = df[teacher_cols]
        df = df.sort_values(by=["Period", "Cycle", "LastName", "FirstName"])

        sh = gc.open_by_url(gradebook_url)
        try:
            wks = sh.worksheet_by_title("AugustRegentsRegistrations")
        except:
            wks = sh.add_worksheet("AugustRegentsRegistrations")
        wks.clear()
        wks.set_dataframe(df.fillna(""), "A1")
        wks.frozen_rows = 1
        wks.frozen_cols = 3

        wks.adjust_column_width(1, 18)

    return summer_school_gradebooks_hub_df.to_html()
