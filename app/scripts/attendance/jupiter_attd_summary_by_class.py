import pandas as pd
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from app.scripts.date_to_marking_period import return_mp_from_date


def main(data):
    report = "rosters_and_grades"
    filename = utils.return_most_recent_report(files_df, report)

    df = utils.return_file_as_df(filename).fillna('')
    term = session['term']
    df = df[df['Term']==f'S{term}']

    Course = data['Course']
    Section = data['Section']
    df = df[(df["Course"] == Course) & (df["Section"] == Section)]
    StudentID_lst = df['StudentID']

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]

    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report(
        files_df, "jupiter_period_attendance"
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## keep students in the course
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"].isin(StudentID_lst)
    ]

    ## convert date and insert marking period
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(
        return_mp_from_date, args=(school_year,)
    )

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
        index=["StudentID", "Term", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student["total"] = attd_by_student.sum(axis=1)

    attd_by_student["%_late"] = attd_by_student["tardy"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student["%_absent"] = attd_by_student["unexcused"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student = attd_by_student.fillna(0)

    return attd_by_student
