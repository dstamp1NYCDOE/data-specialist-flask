import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from io import StringIO
from flask import current_app, session


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## process possible times
    possible_times = form.practical_times.data
    string_data = StringIO(possible_times)

    # Read the string data into a DataFrame
    possible_times_df = pd.read_csv(string_data, sep="\t")

    ## pull student email
    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)
    student_emails_df = cr_3_07_df[["StudentID", "Student DOE Email"]]

    ## pull exam registrations
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_08", year_and_semester
    )
    cr_1_08_df = utils.return_file_as_df(filename)
    ### keep currently on register students
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    ### keep ES
    es_registrations_df = cr_1_08_df[cr_1_08_df["Course"] == "SXRUG"]

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]
    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left")

    ## pull 1_01
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)

    cr_1_01_df["is_exam_code"] = cr_1_01_df["Course"].apply(is_exam_code)
    cr_1_01_df = cr_1_01_df[~cr_1_01_df["is_exam_code"]]
    student_schedules_df = cr_1_01_df[cr_1_01_df["Course"].str[0] != "Z"]
    student_schedules_df = student_schedules_df[
        student_schedules_df["Period"].isin([1, 2, 3])
    ]

    student_period_availability_df = pd.pivot_table(
        student_schedules_df,
        index="StudentID",
        columns="Period",
        values="Section",
        aggfunc="count",
    ).fillna(0)

    students_in_earth_science_df = student_schedules_df[
        student_schedules_df["Course"].str[0:2] == "SE"
    ]
    students_in_earth_science_df = students_in_earth_science_df.rename(
        columns={"Period": "EarthSciencePeriod"}
    )
    students_in_earth_science_df = students_in_earth_science_df[
        ["StudentID", "EarthSciencePeriod"]
    ]

    es_registrations_df = es_registrations_df.merge(
        student_period_availability_df, on=["StudentID"], how="left"
    ).fillna(0)
    es_registrations_df = es_registrations_df.merge(
        students_in_earth_science_df, on=["StudentID"], how="left"
    ).fillna(0)

    es_registrations_df["InitialLabPracticalSession"] = es_registrations_df.apply(
        assign_period_for_students_in_summer_school, axis=1
    )

    student_dict_list = []
    assigned_dict = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for i, student in es_registrations_df.iterrows():
        InitialLabPracticalSession = student["InitialLabPracticalSession"]
        StudentID = student["StudentID"]

        if InitialLabPracticalSession == 0:
            InitialLabPracticalSession = min(assigned_dict, key=assigned_dict.get)

        assigned_dict[InitialLabPracticalSession] += 1
        student_dict = {
            "StudentID": StudentID,
            "LabPracticalSession": InitialLabPracticalSession,
        }
        student_dict_list.append(student_dict)

    lab_practical_df = pd.DataFrame(student_dict_list)
    lab_practical_df = lab_practical_df.drop_duplicates(subset=["StudentID"])

    lab_practical_df = es_registrations_df.merge(
        lab_practical_df, on=["StudentID"], how="left"
    )
    lab_practical_df = lab_practical_df.merge(cr_s_01_df, on=["StudentID"], how="left")
    lab_practical_df = lab_practical_df.merge(
        student_emails_df, on=["StudentID"], how="left"
    )
    lab_practical_df = lab_practical_df.merge(
        possible_times_df, on=["LabPracticalSession"], how="left"
    )
    lab_practical_df = lab_practical_df.drop_duplicates(subset=["StudentID"])

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Student DOE Email",
        "Sending school",
        "EarthSciencePeriod",
        "Time",
    ]
    lab_practical_df = lab_practical_df[cols]

    download_name = "LabPractical.xlsx"

    ## put into spreadsheet
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    sheet_name = "FullList"
    lab_practical_df.to_excel(writer, sheet_name=sheet_name, index=False)

    ## roster by Time
    for LabPracticalTime, students_by_session_df in lab_practical_df.groupby("Time"):
        sheet_name = LabPracticalTime.replace(":", "_")
        students_by_session_df.to_excel(writer, index=False, sheet_name=sheet_name)

    ## roster by sending_school
    for sending_school, students_by_dbn_df in lab_practical_df.groupby(
        "Sending school"
    ):
        sheet_name = sending_school
        students_by_dbn_df.sort_values(by=["Time"]).to_excel(
            writer, index=False, sheet_name=sheet_name
        )

    writer.close()
    f.seek(0)
    return f, download_name


def assign_period_for_students_in_summer_school(student_row):
    p1 = student_row[1]
    p2 = student_row[2]
    p3 = student_row[3]
    EarthSciencePeriod = student_row["EarthSciencePeriod"]
    i = student_row.name
    n = 5
    if p1 + p2 + p3 + EarthSciencePeriod == 0:
        return 0
    if p1 == 0:
        return 1
    if p2 == 0:
        return 2
    if p3 == 0:
        return 3
    if EarthSciencePeriod != 0:
        return EarthSciencePeriod
    return 0


def return_session(i, n):
    return 1 + i % n


def is_exam_code(course_code):
    return course_code[1:3] == "XR"
