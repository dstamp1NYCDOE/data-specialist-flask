import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math


def main(request, form):
    df = return_jupiter_schedule(request, form)

    output_lst = []
    for (course, section), course_rows in df.groupby(
        ["JupiterCourse", "JupiterSection"]
    ):

        course_row = course_rows.iloc[0]
        temp_dict = {
            "JupiterCourse": course_row["JupiterCourse"],
            "JupiterSection": course_row["JupiterSection"],
            "JupiterPeriods": ",".join(course_rows["JupiterPeriod"].unique().tolist()),
            "JupiterTab": return_jupiter_tab(
                ",".join(course_rows["JupiterPeriod"].unique().tolist())
            ),
            "JupiterTeacher1": course_row["DelegatedNickName1"],
            "JupiterTeacher2": course_row["DelegatedNickName2"],
            "JupiterRoom": course_row["Room"],
        }
        output_lst.append(temp_dict)

    output_df = pd.DataFrame(output_lst).fillna("")

    # output_df = df[['CourseCode','Course name']].drop_duplicates()
    return output_df.to_html(index=False)


def return_student_jupiter(request, form):
    jupiter_df = return_jupiter_schedule(request, form)
    jupiter_df = jupiter_df.drop_duplicates(subset=["CourseCode", "SectionID"])
    jupiter_df = jupiter_df[
        ["CourseCode", "SectionID", "JupiterCourse", "JupiterSection"]
    ]

    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    student_schedules_df = utils.return_file_as_df(filename).fillna("")

    jupiter_output_df = student_schedules_df.merge(
        jupiter_df,
        left_on=["Course", "Section"],
        right_on=["CourseCode", "SectionID"],
        how="inner",
    )
    jupiter_output_df = jupiter_output_df[
        ["StudentID", "JupiterCourse", "JupiterSection"]
    ].sort_values(by=["StudentID"])
    return jupiter_output_df.to_html(index=False)


def return_jupiter_schedule(request, form):
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

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
    teacher_reference_df["DelegatedNickName1"] = teacher_reference_df["TeacherName"]
    teacher_reference_df["DelegatedNickName2"] = teacher_reference_df["TeacherName"]


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
    df = df[df["Capacity"] != 0]
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
    # attach period
    df["JupiterPeriod"] = df.apply(return_jupiter_period, axis=1)
    # return jupiter_course
    df["JupiterCourse"] = df.apply(return_jupiter_course, axis=1)
    # return jupiter_section
    df["JupiterSection"] = df.apply(return_jupiter_section, axis=1)

    return df


def return_jupiter_tab(jupiter_periods):
    if len(jupiter_periods) == 1:
        return jupiter_periods
    else:
        return jupiter_periods.replace(",", "_")


def return_jupiter_course(row):
    course_code = row["CourseCode"]
    if len(course_code) <= 5:
        return course_code
    if course_code[0] in ["A", "T", "B", "Z"]:
        return course_code
    if course_code[5] in ["T", "X", "H"]:
        return course_code
    if course_code[0:7] in ["EES87QC", "EES87QD", "EES87QF", "EES87QG"]:
        return course_code[0:7]
    if course_code[0:7] in ["MQS11QF", "MQS11QG", "EES87QF", "EES87QG"]:
        return course_code[0:7]

    if course_code[0:5] in ["PPS85", "PPS87"]:
        days = row["Cycle Day"]
        pe_dict_by_cycle = {
            1010: "PPS85",
            10101: "PPS87",
        }
        return pe_dict_by_cycle.get(days)

    if "QQ" in course_code:
        return course_code
    if course_code[5] == "Q":
        return course_code[0:5]

    return course_code


def return_jupiter_section(row):
    course_code = row["CourseCode"]
    section_id = row["SectionID"]

    if "QM" in course_code:
        return f"{int(section_id)}-QM"

    return str(int(section_id))


def return_jupiter_period(row):
    period = row["PeriodID"]
    days = row["Cycle Day"]

    if days == 11111:
        return str(period)

    cycle_dict = {
        1010: ["T", "R"],
        101: ["W", "F"],
        10000: ["M"],
        10101: ["M", "W", "F"],
    }

    period_lst = [f"{day}{period}" for day in cycle_dict.get(days, [])]

    return ", ".join(period_lst)
