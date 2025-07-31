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
import app.scripts.utils.utils as utils

from app.scripts.summer.programming import programming_utils

load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    class_date = form.data["class_date"]
    sheet_name = class_date.strftime("%-m/%-d")

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
    cr_1_01_df["DailyGrade"] = ""

    ## get gsheet

    summer_school_gradebooks_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_gradebooks_hub", year_and_semester
    )

    summer_school_gradebooks_hub_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url
    )

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
        "ParentLN",
        "ParentFN",
        "Phone",
        "DailyGrade",
    ]

    combined_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Teacher1",
        "Course",
        "Period",
        "Course Name",
        "Cycle",
        "school_name",
        "Student DOE Email",
        "ParentLN",
        "ParentFN",
        "Phone",
        "DailyGrade",
    ]
    for index, gradebook in summer_school_gradebooks_hub_df.iterrows():
        
        gradebook_url = gradebook["Gradebook URL"]
        if gradebook_url == '':
            continue
        teacher_name = gradebook["TeacherName"]
        df = cr_1_01_df[cr_1_01_df["Teacher1"] == teacher_name]
        df = df[teacher_cols]
        df = df.sort_values(by=["Period", "Cycle", "LastName", "FirstName"])

        sh = gc.open_by_url(gradebook_url)
        try:
            wks = sh.worksheet_by_title(sheet_name)
        except:
            wks = sh.add_worksheet(sheet_name)
        print(sh)
        wks.clear()
        wks.set_dataframe(df.fillna(""), "A1")
        wks.frozen_rows = 1
        wks.frozen_cols = 3
        wks.set_data_validation(
            start="N2",
            end="N1000",
            condition_type="ONE_OF_LIST",
            condition_values=[0, 1, 2, 3, 4, 5],
            inputMessage="Each student is scored on a 0-5 for each day enrolled in a class",
            strict=True,
            showCustomUi=True,
        )
        wks.adjust_column_width(1, 14)

        # update current roster
        wks = sh.worksheet(0)
        wks.clear("A1", "M1000")
        wks.set_dataframe(df.drop(columns=["DailyGrade"]).fillna(""), "A1")
        wks.adjust_column_width(1, 13)
        wks.frozen_rows = 1
        wks.frozen_cols = 3

    ## all students
    sh = gc.open_by_url(summer_school_gradebooks_hub_url)
    df = cr_1_01_df
    df = df[df["Course"].str[0] != "Z"]
    df = df[df["Period"].isin([1, 2, 3])]

    df = df.sort_values(by=["school_name", "LastName", "FirstName", "Period"])
    wks = sh.worksheet_by_title("AllStudentsBySchool")
    wks.clear("A1", "M4000")
    wks.set_dataframe(df[combined_cols].drop(columns=["DailyGrade"]).fillna(""), "A1")
    wks.adjust_column_width(1, 13)
    wks.frozen_rows = 1
    wks.frozen_cols = 7

    return summer_school_gradebooks_hub_df.to_html()
