import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math

# Reports Needed
## 1_01
## MasterSchedule
## 6_42
## 4_23


def main(request, form):
    df = return_jupiter_schedule(request, form)

    output_lst = []
    for (course, section), course_rows in df.groupby(
        ["JupiterCourse", "JupiterSection"]
    ):

        course_row = course_rows.iloc[0]
        temp_dict = {
            "JupiterCourse": course_row["JupiterCourse"],
            "JupiterCourseName": course_row["Course Name"],
            "JupiterSection": course_row["JupiterSection"],
            "JupiterPeriods": ",".join(course_rows["JupiterPeriod"].unique().tolist()),
            "JupiterTab": return_jupiter_tab(
                ",".join(course_rows["JupiterPeriod"].unique().tolist())
            ),
            "JupiterTeacher1": course_row["TeacherName"],
            "JupiterTeacher2": course_row["Co-Teacher"],
            "JupiterRoom": course_row["Room"],
        }
        output_lst.append(temp_dict)

    output_df = pd.DataFrame(output_lst).fillna("")

    # output_df = df[['CourseCode','Course name']].drop_duplicates()
    return output_df.to_html(index=False)


def return_student_jupiter(request, form):
    jupiter_df = return_jupiter_schedule(request, form)
    jupiter_df = jupiter_df.drop_duplicates(subset=["Course Code", "Section"])
    jupiter_df = jupiter_df[
        ["Course Code", "Section", "JupiterCourse", "JupiterSection"]
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
        right_on=["Course Code", "Section"],
        how="inner",
    )
    jupiter_output_df = jupiter_output_df[
        ["StudentID", "JupiterCourse", "JupiterSection"]
    ].sort_values(by=["StudentID"])
    return jupiter_output_df.to_html(index=False)


def return_jupiter_schedule(request=None, form=None):
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
        files_df, "4_23", year_and_semester=year_and_semester
    )
    section_properties_df = utils.return_file_as_df(filename)
    co_teachers_df = section_properties_df[["Course", "Section", "Co-Teacher"]]

    master_schedule_df = master_schedule_df.merge(
        co_teachers_df,
        left_on=["Course Code", "Section"],
        right_on=["Course", "Section"],
    ).fillna("")


    filename = utils.return_most_recent_report_by_semester(
        files_df, "6_42", year_and_semester=year_and_semester
    )
    teacher_reference_df = utils.return_file_as_df(filename)
    teacher_reference_df["TeacherName"] = (
        teacher_reference_df["LastName"]
        + " "
        + teacher_reference_df["FirstName"].str[0]
    )

    df = master_schedule_df.merge(
        teacher_reference_df[["Teacher", f"TeacherName",'Mail']],
        left_on=[f"Teacher Name"],
        right_on=[f"Teacher"],
        how="left",
    )

    print(df[df['Course']=='MRS21'])

    # drop classes with no students
    # df = df[df["Capacity"] != df["Remaining Capacity"]]
    df = df[df["Active"] != 0]
    # drop classes with no meeting days
    df = df[df["Days"] != '-----']
    # drop classes attached to "staff"
    df = df[df["Teacher Name"] != "STAFF"]
    # drop classes outside of 1-10
    df = df[df["PD"] < 11]
    ## drop bussing dummy code
    df = df[df["Course Code"] != "ZMBUS"]
    
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
    course_code = row["Course Code"]
    if len(course_code) <= 5:
        return course_code
    if course_code[0] in ["A", "T", "B", "Z"]:
        return course_code
    if course_code[5] in ["T", "X", "H"]:
        return course_code
    if course_code[0:7] in ["EES87QC", "EES87QD", "EES87QF", "EES87QG","EES87QW"]:
        return course_code[0:7]
    if course_code[0:7] in ["EES88QC", "EES88QD", "EES88QF", "EES88QG","EES88QW"]:
        return course_code[0:7]
    if course_code[0:7] in [
        "MQS11QF",
        "MQS11QG",
    ]:
        return course_code[0:7]
    
    if  course_code in ['EQS11QQI']:
        return course_code

    # if "QQ" in course_code:
    #     return course_code
    if course_code[5] == "Q":
        return course_code[0:5]

    return course_code


def return_jupiter_section(row):
    course_code = row["Course Code"]
    section_id = row["Section"]

    if "QM" in course_code:
        return f"{int(section_id)}-QM"

    return str(int(section_id))


def return_jupiter_period(row):
    period = row["PD"]
    days = row["Days"]

    if days == 'MTWRF':
        return str(period)

    period_lst = [f"{day}{period}" for day in days if day !='-']

    return ", ".join(period_lst)
