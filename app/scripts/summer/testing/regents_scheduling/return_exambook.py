import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math


def main(students_df):
    school_year = session["school_year"]
    term = session["term"]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    section_properties_df = pd.read_excel(path, sheet_name="SummerSectionProperties")
    section_properties_df = section_properties_df[["Section", "Type"]]

    output_cols = [
        "Course",
        "Section",
        "ExamTitle",
        "Day",
        "Time",
        "Room",
    ]
    students_df["Room"] = students_df.apply(return_room, axis=1)
    students_df = students_df.drop(columns=["Section"])
    students_df = students_df.rename(columns={"FinalSection": "Section"})

    sections_df = pd.pivot_table(
        students_df, index=output_cols, values="StudentID", aggfunc="count"
    ).reset_index()

    sections_df = sections_df.rename(columns={"StudentID": "#_of_students"})
    sections_df = sections_df.merge(section_properties_df, on=["Section"], how="left")

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


def return_room(row):
    AM1_ROOM = row["AM1_ROOM"]
    AM2_ROOM = row["AM2_ROOM"]
    PM1_ROOM = row["PM1_ROOM"]
    PM2_ROOM = row["PM2_ROOM"]
    AM3_ROOM = row["AM3_ROOM"]
    PM3_ROOM = row["PM3_ROOM"]

    TIME = row["Time"]
    exam_num = row["exam_num"]

    org_dict = {
        "AM": {1: AM1_ROOM, 2: AM2_ROOM, 3: AM3_ROOM},
        "PM": {1: PM1_ROOM, 2: PM2_ROOM, 3: PM3_ROOM},
    }
    if org_dict.get(TIME).get(exam_num) == 202 and exam_num == 3:
        return org_dict.get(TIME).get(2)

    return org_dict.get(TIME).get(exam_num)
