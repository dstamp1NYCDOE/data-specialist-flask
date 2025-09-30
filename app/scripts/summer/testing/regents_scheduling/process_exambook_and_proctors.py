import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session

import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    exam_book_df = regents_organization_utils.return_exam_book()
    ## keep relevant columns
    cols = [
        "Day",
        "Time",
        "ExamTitle",
        "exam_num",
        "Course",
        "Section",
        "Type",
        "Room",
        "NumOfStudents",
        "hub_location",
    ]
    exam_book_df = exam_book_df[cols]
    TESTING_TIME_COL_NAME = "TestingTime (hours)"
    exam_book_df[TESTING_TIME_COL_NAME] = exam_book_df["Type"].apply(
        return_max_section_time
    )

    ## determine_proctor_needs
    PROCTOR_NUM = 0
    PROCTOR_LST = []
    for (day, room), sections_in_room_df in exam_book_df[
        exam_book_df["Section"] > 1
    ].groupby(["Day", "Room"]):
        section_type_lst = sections_in_room_df["Type"].to_list()
        time_lst = sections_in_room_df["Time"].unique().tolist()

        is_conflict_room = return_is_conflict_room(section_type_lst)

        is_am_room = return_if_am_room(time_lst)
        is_pm_room = return_if_pm_room(time_lst)
        is_am_pm_room = return_if_am_pm_room(time_lst)

        testing_sessions_df = sections_in_room_df.drop_duplicates(
            subset=["Time", "ExamTitle", TESTING_TIME_COL_NAME]
        )

        hours_in_room = testing_sessions_df[TESTING_TIME_COL_NAME].sum()

        if hours_in_room < 8:
            PROCTOR_NUM += 1
            proctor_type = "_".join(time_lst)
            proctor_dict = {
                "Day": day,
                "ProctorAssignment": PROCTOR_NUM,
                "Room": room,
                "proctor_type": proctor_type,
                "HoursOfAssignment": hours_in_room,
            }
            PROCTOR_LST.append(proctor_dict)
        else:
            for proctor_type in ["AM", "PM"]:
                PROCTOR_NUM += 1
                if hours_in_room < 6:
                    hours_in_room = 4.5
                else:
                    hours_in_room = 6

                proctor_dict = {
                    "Day": day,
                    "ProctorAssignment": PROCTOR_NUM,
                    "Room": room,
                    "proctor_type": proctor_type,
                    "HoursOfAssignment": hours_in_room,
                }
                PROCTOR_LST.append(proctor_dict)

    proctor_df = pd.DataFrame(PROCTOR_LST)

    print(proctor_df)
    print(exam_book_df)

    proctor_df = exam_book_df.merge(
        proctor_df, on=["Day", "Room"], how="left"
    ).sort_values(by=["Day", "ExamTitle", "Room"])

    proctors_pvt_tbl = (
        pd.pivot_table(
            proctor_df,
            index=["Day", "Time", "Room", "ExamTitle", "hub_location"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        .reset_index()
        .sort_values(by=["Day", "Room", "Time"])
    )

    ## generate hub pvt
    hub_pvt = pd.pivot_table(
        exam_book_df,
        index=["Day", "Time", "hub_location", "ExamTitle"],
        # columns=["ExamTitle"],
        values="NumOfStudents",
        aggfunc="sum",
    ).fillna(0)

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    exam_book_df.to_excel(writer, sheet_name="ExamBook", index=False)
    
    proctors_pvt_tbl.to_excel(writer, sheet_name="ProctorNumbers")
    hub_pvt.to_excel(writer, sheet_name="HubNumbers")
    ##folders_to_prep_per_hub
    for hub_location, hub_sections_list in exam_book_df.groupby(["hub_location"]):
        sheet_name = f"Hub{hub_location[0]}"
        hub_rooms_pvt = pd.pivot_table(
            hub_sections_list,
            index=["Day", "Time", "Room", "ExamTitle"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        hub_rooms_pvt.to_excel(writer, sheet_name=sheet_name)

    ## day/time/hub sections_list
    for (day, time, hub_location), hub_sections_list in exam_book_df.groupby(
        ["Day", "Time", "hub_location"]
    ):
        day_str = day.replace("/", "-")
        sheet_name = f"{day_str}_{time}_Hub{hub_location}"
        hub_rooms_pvt = pd.pivot_table(
            hub_sections_list,
            index=["Room", "ExamTitle"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        hub_rooms_pvt.to_excel(writer, sheet_name=sheet_name)

    writer.close()
    f.seek(0)

    return f


def combine_lst_of_section_properties(x):
    x = x.unique()
    output = "\n".join(str(v) for v in x)
    return output


def return_max_section_time(section_type):
    default_time = 3
    if "enl" in section_type:
        default_time = 4.5
    if "2x" in section_type:
        default_time = 6
    if "1.5x" in section_type:
        default_time = 4.5
    return default_time


def return_hub_location(section_row):
    Room = section_row["Room"]
    Time = section_row["Time"]
    exam_num = section_row["exam_num"]
    Section = section_row["Section"]

    if Room == 329:
        return 329
    if Room > 800:
        return {1: 919, 2: 823}.get(exam_num, 823)
    return {1: 727, 2: 519}.get(exam_num, 519)


def return_if_am_room(time_lst):
    if "AM" in time_lst:
        return True
    return False


def return_if_pm_room(time_lst):
    if "PM" in time_lst:
        return True
    return False


def return_if_am_pm_room(time_lst):
    return return_if_am_room(time_lst) and return_if_pm_room(time_lst)


def return_is_conflict_room(section_type_lst):
    for section_type in section_type_lst:
        if "conflict" in section_type:
            return True
    return False
