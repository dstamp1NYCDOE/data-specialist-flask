import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from flask import current_app, session


def main():

    filename = utils.return_most_recent_report(files_df, "3_07")
    students_df = utils.return_file_as_df(filename)
    school_year = session["school_year"]

    students_df["year_in_hs"] = students_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )
    cols = ["StudentID", "LastName", "FirstName", "year_in_hs", "Student DOE Email"]
    students_df = students_df[cols]

    regents_max_df = process_regents_max.main()

    regents_max_pvt = pd.pivot_table(
        regents_max_df,
        index="StudentID",
        columns="Exam",
        values="Mark",
        aggfunc=return_reg_mark,
    )

    students_df = students_df.merge(regents_max_pvt, on="StudentID", how="left")

    ### department GPA

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)

    ## attach numeric equivalent
    cr_1_14_filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left"
    )

    cr_1_14_df["dept"] = cr_1_14_df["Course"].str[0]

    student_department_gpa = pd.pivot_table(
        cr_1_14_df,
        index=["StudentID"],
        columns=["dept"],
        values="NumericEquivalent",
        aggfunc="mean",
    )
    student_department_gpa = student_department_gpa[["E", "M", "S", "H"]]
    student_department_gpa.columns = [
        "ELA GPA",
        "Math GPA",
        "Science GPA",
        "Soc Stud GPA",
    ]
    students_df = students_df.merge(student_department_gpa, on="StudentID", how="left")

    ## prior APs taken
    AP_courses_df = cr_1_14_df[cr_1_14_df["Course Title"].str[0:3] == "AP "]
    AP_courses_pvt = pd.pivot_table(
        AP_courses_df,
        index=["StudentID"],
        columns=["Course Title"],
        values="NumericEquivalent",
        aggfunc="mean",
    )

    students_df = students_df.merge(AP_courses_pvt, on="StudentID", how="left").fillna(
        ""
    )

    ## most recent semester attendance
    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report(
        files_df, "jupiter_period_attendance"
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## drop SAGA
    attendance_marks_df = attendance_marks_df[attendance_marks_df["Course"] != "MQS22"]

    ## convert date and insert marking period
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student["total"] = attd_by_student.sum(axis=1)

    attd_by_student["%_present"] = 100 * (
        1 - attd_by_student["unexcused"] / attd_by_student["total"]
    )
    attd_by_student["%_on_time"] = (
        100
        * attd_by_student["present"]
        / (attd_by_student["present"] + attd_by_student["tardy"])
    )
    attd_by_student = attd_by_student.fillna(0)
    attd_by_student = attd_by_student.reset_index()

    student_on_time_pvt = pd.pivot_table(
        attd_by_student,
        index="StudentID",
        columns="Pd",
        values="%_on_time",
        aggfunc="mean",
    )
    student_on_time_pvt.columns = [
        f"P{x}_%_on_time" for x in student_on_time_pvt.columns
    ]

    student_present_pvt = pd.pivot_table(
        attd_by_student,
        index="StudentID",
        columns="Pd",
        values="%_present",
        aggfunc="mean",
    )
    student_present_pvt.columns = [
        f"P{x}_%_present" for x in student_present_pvt.columns
    ]

    students_df = students_df.merge(
        student_present_pvt, on="StudentID", how="left"
    ).fillna("")
    students_df = students_df.merge(
        student_on_time_pvt, on="StudentID", how="left"
    ).fillna("")

    return students_df

    return students_df.sort_values(by=["LastName", "FirstName"])


def return_reg_mark(marks):
    return marks.to_list()[0]