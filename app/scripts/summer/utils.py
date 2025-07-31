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


def return_summer_class_lists():
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
    cr_1_01_df = cr_1_01_df.merge(photos_df, on=["StudentID"], how="left")

    cr_1_01_df = cr_1_01_df.drop_duplicates(subset=["StudentID", "Course"])
    cr_1_01_df = cr_1_01_df[cr_1_01_df["Course"].str[0] != "Z"]
    return cr_1_01_df


def return_sending_school_list():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## process current class list
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_s_01_df = cr_s_01_df[cr_s_01_df["school_name"] != "NoSendingSchool"]

    sending_schools_df = cr_s_01_df[["Sending school", "school_name"]].drop_duplicates()
    sending_schools_df = sending_schools_df.sort_values(by="school_name")
    lst_of_tuples = list(sending_schools_df.itertuples(index=False, name=None))
    return lst_of_tuples
