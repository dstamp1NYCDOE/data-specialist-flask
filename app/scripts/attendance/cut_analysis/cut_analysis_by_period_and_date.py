import pandas as pd
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
import itertools


def main():
    sheets = []
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    shared_instruction_students = cr_3_07_df[cr_3_07_df["GradeLevel"] == "ST"][
        "StudentID"
    ]

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## only keep students still on register
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"].isin(students_df["StudentID"])
    ]

    ## drop shared instruction students
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["StudentID"].isin(shared_instruction_students)
    ]

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attd_by_student_by_day = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="count",
    ).fillna(0)

    attd_by_student_by_day["in_school?"] = (
        attd_by_student_by_day["present"] + attd_by_student_by_day["tardy"]
    ) >= 2
    attd_by_student_by_day = attd_by_student_by_day.reset_index()[
        ["StudentID", "Date", "in_school?"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        attd_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    first_period_present_by_student_by_day = pd.pivot_table(
        attendance_marks_df[attendance_marks_df["in_school?"]],
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="min",
    ).reset_index()

    first_period_present_by_student_by_day["first_period_present"] = (
        first_period_present_by_student_by_day[["present", "tardy"]].min(axis=1)
    )

    first_period_present_by_student_by_day = first_period_present_by_student_by_day[
        ["StudentID", "Date", "first_period_present"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        first_period_present_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    attendance_marks_df["potential_cut"] = attendance_marks_df.apply(
        determine_potential_cut, axis=1
    )

    attendance_marks_df["AttdMark"] = attendance_marks_df.apply(
        return_enhanced_attd_mark, axis=1
    )
    print(attendance_marks_df)

    pvt_by_date_and_period = pd.pivot_table(
        attendance_marks_df,
        index=["Date", "Pd"],
        columns="AttdMark",
        values="StudentID",
        aggfunc="count",
    )
    pvt_by_date_and_period = pvt_by_date_and_period.reset_index()
    print(pvt_by_date_and_period)

    sheets.append(("combined", pvt_by_date_and_period))

    for period, attendance_by_period_df in pvt_by_date_and_period.groupby("Pd"):
        sheets.append((f"P{period}", attendance_by_period_df))

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    f.seek(0)

    download_name = "attendance_analysis_by_date_and_period.xlsx"
    return f, download_name


def return_enhanced_attd_mark(student_row):

    attd_type = student_row["Type"]
    potential_cut = student_row["potential_cut"]
    first_period_present = student_row["first_period_present"]
    class_period = student_row["Pd"]

    if potential_cut:
        if class_period > first_period_present:
            return "potential cut"
        else:
            return "potential late to school"
    else:
        return attd_type


def determine_potential_cut(student_row):
    is_in_school = student_row["in_school?"]

    if is_in_school == False:
        return False

    attendance_type = student_row["Type"]
    period = student_row["Pd"]
    first_period_present = student_row["first_period_present"]
    if attendance_type == "unexcused" and period >= first_period_present:
        return True

    return False
