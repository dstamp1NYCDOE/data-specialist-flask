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

load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    if form.gsheet_url.data:
        student_info_by_teacher_url = form.gsheet_url.data
    else:
        student_info_by_teacher_url = utils.return_gsheet_url_by_title(
            gsheets_df, "student_info_by_teacher", year_and_semester
        )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    student_schedules_df = utils.return_file_as_df(filename).fillna("")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester=year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "6_42", year_and_semester=year_and_semester
    )
    teacher_reference_df = utils.return_file_as_df(filename)
    teacher_reference_df["TeacherName"] = (
        teacher_reference_df["LastName"]
        + " "
        + teacher_reference_df["FirstName"].str[0]
    )
    teacher_reference_df["DelegatedNickName1"] = teacher_reference_df[
        "TeacherName"
    ].str.upper()
    teacher_reference_df["DelegatedNickName2"] = teacher_reference_df[
        "TeacherName"
    ].str.upper()

    ## attach Teacher 2
    teachers_df = student_schedules_df[
        ["Course", "Section", "Teacher1", "Teacher2"]
    ].drop_duplicates()
    df = master_schedule_df.merge(
        teachers_df,
        left_on=["CourseCode", "SectionID"],
        right_on=["Course", "Section"],
        how="left",
    )
    # drop classes with no students
    df = df[df["Capacity"] > 0]
    # drop classes with no meeting days
    df = df[df["Cycle Day"] != 0]
    # drop classes attached to "staff"
    df = df[df["Teacher Name"] != "STAFF"]
    ## attach delegated nickname
    for teacher_num in [1, 2]:
        df = df.merge(
            teacher_reference_df[["Teacher", f"DelegatedNickName{teacher_num}"]],
            left_on=[f"Teacher{teacher_num}"],
            right_on=[f"Teacher"],
            how="left",
        )
    df_cols = [
        "Course",
        "Section",
        "Course name",
        "DelegatedNickName1",
        "DelegatedNickName2",
    ]
    df = df[df_cols]
    df = df.drop_duplicates(subset=["Course", "Section"])

    student_schedules_df = student_schedules_df.merge(
        df, on=["Course", "Section"], how="left"
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df = cr_3_07_df[
        ["StudentID", "Student DOE Email", "ParentLN", "ParentFN", "Phone"]
    ]
    student_schedules_df = student_schedules_df.merge(
        cr_3_07_df, on=["StudentID"], how="left"
    ).fillna("")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(filename)
    cr_1_49_df = cr_1_49_df[['StudentID','Counselor']]

    student_schedules_df = student_schedules_df.merge(
        cr_1_49_df, on=["StudentID"], how="left"
    ).fillna("")

    student_schedules_df = student_schedules_df[
        student_schedules_df["DelegatedNickName1"] != ""
    ]
    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Student DOE Email",
        "ParentLN",
        "ParentFN",
        "Phone",
        "Course name",
        "Course",
        "Section",
        "Period",
        "DelegatedNickName1",
        "DelegatedNickName2",
        "Counselor",
    ]
    student_schedules_df = student_schedules_df[output_cols]
    student_schedules_df = student_schedules_df.sort_values(
        by=["Period", "Course", "Section"]
    )

    ## write the full list to the spreadsheet
    sh = gc.open_by_url(student_info_by_teacher_url)
    try:
        wks = sh.worksheet_by_title("AllStudents")
    except:
        wks = sh.add_worksheet("AllStudents")
    wks.clear()
    wks.set_dataframe(student_schedules_df.fillna(""), "A1", fit=True)

    ## write combined spreadsheet
    try:
        wks = sh.worksheet_by_title("Combined")
    except:
        wks = sh.add_worksheet("Combined")
        cell_str = f"""=query(AllStudents!A:N"""
        wks.update_value("a1", cell_str)

    ## write the query cells to each sheet
    teacher_lst = pd.unique(
        student_schedules_df[["DelegatedNickName1", "DelegatedNickName2"]].values.ravel(
            "K"
        )
    )
    teacher_lst = sorted(teacher_lst)
    teacher_lst = [x for x in teacher_lst if x != ""]
    for teacher_name in teacher_lst:
        cell_str = f"""=query(Combined!A:Z,"select * where L='{teacher_name}' or M='{teacher_name}'")"""
        try:
            wks = sh.worksheet_by_title(teacher_name)
        except:
            wks = sh.add_worksheet(teacher_name)
            wks.update_value("a1", cell_str)
            wks.frozen_rows = 1
            wks.frozen_cols = 3
            wks.adjust_column_width(1, 14)

    counselor_lst = pd.unique(
        student_schedules_df[["Counselor"]].values.ravel(
            "K"
        )
    )
    counselor_lst = sorted(counselor_lst)
    counselor_lst = [x for x in counselor_lst if x != ""]
    for counselor in counselor_lst:
        cell_str = f"""=query(Combined!A:Z,"select * where N='{counselor}' order by B, C")"""
        try:
            wks = sh.worksheet_by_title(counselor)
        except:
            wks = sh.add_worksheet(counselor)
            wks.update_value("a1", cell_str)
            wks.frozen_rows = 1
            wks.frozen_cols = 3
            wks.adjust_column_width(1, 14)


    return student_schedules_df
    ## get gsheet

    student_info_by_teacher_url = utils.return_gsheet_url_by_title(
        gsheets_df, "student_info_by_teacher", year_and_semester
    )

    teacher_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "Section",
        "Period",
        "Student DOE Email",
    ]

    return df
    # for index, gradebook in summer_school_gradebooks_hub_df.iterrows():
    #     gradebook_url = gradebook["Gradebook URL"]
    #     teacher_name = gradebook["TeacherName"]
    #     print(teacher_name)
    #     df = cr_1_01_df[cr_1_01_df["Teacher1"] == teacher_name]
    #     df = df[teacher_cols]
    #     df = df.sort_values(by=["Period", "Cycle", "LastName", "FirstName"])

    #     wks.frozen_rows = 1
    #     wks.frozen_cols = 3
    #     wks.set_data_validation(
    #         start="N2",
    #         end="N1000",
    #         condition_type="ONE_OF_LIST",
    #         condition_values=[0, 1, 2, 3, 4, 5],
    #         inputMessage="Each student is scored on a 0-5 for each day enrolled in a class",
    #         strict=True,
    #         showCustomUi=True,
    #     )
    #     wks.adjust_column_width(1, 14)

    #     # update current roster
    #     wks = sh.worksheet(0)
    #     wks.clear("A1", "M1000")
    #     wks.set_dataframe(df.drop(columns=["DailyGrade"]).fillna(""), "A1")
    #     wks.adjust_column_width(1, 13)
    #     wks.frozen_rows = 1
    #     wks.frozen_cols = 3

    # ## all students
    # sh = gc.open_by_url(summer_school_gradebooks_hub_url)
    # df = cr_1_01_df
    # df = df[df["Course"].str[0] != "Z"]
    # df = df[df["Period"].isin([1, 2, 3])]

    # df = df.sort_values(by=["school_name", "LastName", "FirstName", "Period"])
    # wks = sh.worksheet_by_title("AllStudentsBySchool")
    # wks.clear("A1", "M4000")
    # wks.set_dataframe(df[combined_cols].drop(columns=["DailyGrade"]).fillna(""), "A1")
    # wks.adjust_column_width(1, 13)
    # wks.frozen_rows = 1
    # wks.frozen_cols = 7

    # return summer_school_gradebooks_hub_df.to_html()
