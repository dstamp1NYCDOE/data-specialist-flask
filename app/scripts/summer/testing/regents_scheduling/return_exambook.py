import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math


def main(students_df):
    school_year = session["school_year"]
    term = session["term"]

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    regents_calendar_df["exam_num"] = (
        regents_calendar_df.groupby(["Day", "Time"])["CourseCode"].cumcount() + 1
    )

    section_properties_df = pd.read_excel(
        path, sheet_name="SummerSectionProperties"
    ).dropna()

    print(section_properties_df)
    print(regents_calendar_df)

    sections_df = pd.pivot_table(
        students_df,
        index=["Course", "FinalSection"],
        values="StudentID",
        aggfunc="count",
    ).reset_index()
    sections_df.columns = ["Course", "Section", "#_of_students"]

    sections_df = sections_df.merge(
        section_properties_df[["Section", "Type"]],
        on="Section",
        how="left",
    )
    sections_df = sections_df.merge(
        regents_calendar_df,
        left_on="Course",
        right_on="CourseCode",
        how="left",
    )

    sections_df["Room"] = sections_df.apply(return_room_number, axis=1)
    output_cols = [
        "Course",
        "Section",
        "ExamTitle",
        "Day",
        "Time",
        "Type",
        "#_of_students",
        "Room",
    ]

    sections_df = sections_df[output_cols]

    room_check_df = pd.pivot_table(
        sections_df,
        index=[
            "Day",
            "Time",
            "ExamTitle",
        ],
        columns="Room",
        values="#_of_students",
        aggfunc="sum",
    ).fillna(0)

    return sections_df, room_check_df


GENED_ROOMS_DICT = {
    1: [840, 826, 824, 822, 802, 801, 845, 906, 902, 921],
    2: [940, 925, 923, 921, 902, 906, 845, 801, 802, 822],
    3: [646, 645, 640, 629],
}

GENED_AM_CONFLICT_ROOM = 219

## room order (1.5x, 1.5x, ENL, 2x, 1.5x/QR, 2x/QR)

AM1_1_5X_ROOM_1 = 701
AM1_1_5X_ROOM_2 = 702
AM1_2X_ROOM_3 = 722
AM1_QR_ROOM_4 = 724
AM1_QR_ROOM_5 = 743

AM2_1_5X_ROOM_1 = 742
AM2_1_5X_ROOM_2 = 740
AM2_2X_ROOM_3 = 726
AM2_QR_ROOM_4 = 725
AM2_QR_ROOM_5 = 744

PM1_1_5X_ROOM_1 = 522
PM1_1_5X_ROOM_2 = 523
PM1_2X_ROOM_3 = 524
PM1_QR_ROOM_4 = 525
PM1_QR_ROOM_5 = 527

PM2_1_5X_ROOM_1 = 545
PM2_1_5X_ROOM_2 = 544
PM2_2X_ROOM_3 = 542
PM2_QR_ROOM_4 = 540
PM2_QR_ROOM_5 = 529

AM_PM_3_1_5X_ROOM_1 = 427
AM_PM_3_2X_ROOM_2 = 427
AM_PM_3_QR_ROOM_3 = 421
AM_PM_3_QR_ROOM_4 = 421


time_and_half_room_dict = {
    "AM": {
        1: [AM1_1_5X_ROOM_1, AM1_1_5X_ROOM_2],
        2: [AM2_1_5X_ROOM_1, AM2_1_5X_ROOM_2],
        3: [AM_PM_3_1_5X_ROOM_1, AM_PM_3_1_5X_ROOM_1],
    },
    "PM": {
        1: [PM1_1_5X_ROOM_1, PM1_1_5X_ROOM_2],
        2: [PM2_1_5X_ROOM_1, PM2_1_5X_ROOM_2],
        3: [AM_PM_3_1_5X_ROOM_1, AM_PM_3_1_5X_ROOM_1],
    },
}

double_time_room_dict = {
    "AM": {
        1: [AM1_2X_ROOM_3],
        2: [AM2_2X_ROOM_3],
        3: [AM_PM_3_2X_ROOM_2],
    },
    "PM": {
        1: [PM1_2X_ROOM_3],
        2: [PM2_2X_ROOM_3],
        3: [AM_PM_3_2X_ROOM_2],
    },
}

QR_room_dict = {
    "AM": {
        1: [AM1_QR_ROOM_4, AM1_QR_ROOM_5],
        2: [AM2_QR_ROOM_4, AM2_QR_ROOM_5],
        3: [AM_PM_3_QR_ROOM_3, AM_PM_3_QR_ROOM_4],
    },
    "PM": {
        1: [PM1_QR_ROOM_4, PM1_QR_ROOM_5],
        2: [PM2_QR_ROOM_4, PM2_QR_ROOM_5],
        3: [AM_PM_3_QR_ROOM_3, AM_PM_3_QR_ROOM_4],
    },
}


def return_room_number(section_row):
    try:
        section_num = int(section_row["Section"])
        section_type = section_row["Type"]
        section_time = section_row["Time"]
        exam_num = section_row["exam_num"]

        AM_or_AM_PM_conflict = return_if_AM_or_AM_PM_conflict(section_num)

        if section_num < 3:
            return 202
        if section_num < 15:
            index = section_num - 3
            return GENED_ROOMS_DICT[exam_num][index]

        if section_num == 15:
            return GENED_AM_CONFLICT_ROOM
        ## 1.5x room 1 + CONFLICT
        if section_num in [20, 30, 31, 40, 41]:
            if AM_or_AM_PM_conflict:
                section_time = "AM"
            return time_and_half_room_dict[section_time][exam_num][0]
        ## 1.5x room 2 + ENL/ENL Conflict
        if section_num in [21, 22, 23, 32, 33, 42, 43]:
            if AM_or_AM_PM_conflict:
                section_time = "AM"
            return time_and_half_room_dict[section_time][exam_num][1]
        ## QR 1.5x
        if section_num in [26, 27, 36, 37, 46, 47, 56, 57]:
            if AM_or_AM_PM_conflict:
                section_time = "AM"
            return QR_room_dict[section_time][exam_num][0]
        ## QR 2x
        if section_num in [28, 29, 38, 39, 48, 49, 58, 59]:
            if AM_or_AM_PM_conflict:
                section_time = "AM"
            return QR_room_dict[section_time][exam_num][1]
        ## 2X
        if section_num in [24, 25, 34, 35, 44, 45]:
            if AM_or_AM_PM_conflict:
                section_time = "AM"
            return double_time_room_dict[section_time][exam_num][0]
        if (section_num >= 50) and section_num <= 59:
            return 127
        if (section_num >= 60) and section_num <= 63:
            return 329

    except IndexError:
        return 199


def return_if_AM_or_AM_PM_conflict(section_num):
    return (section_num >= 30) and (section_num <= 49)
