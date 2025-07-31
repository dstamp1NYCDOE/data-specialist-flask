import datetime as dt
from io import BytesIO
import pandas as pd
import math

from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df
from app.scripts.date_to_marking_period import return_mp_from_date


def main(PRESENT_STANDARD=90, ON_TIME_STANDARD=80):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )

    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    rosters_df = utils.return_file_as_df(filename).drop_duplicates(subset=['StudentID','Course','Section'])
    rosters_df = rosters_df[['StudentID','Course','Section']]
    rosters_df['Enrolled?'] = True
    

    attendance_marks_df = attendance_marks_df.merge(rosters_df, on=['StudentID','Course','Section'], how='left').fillna(False)
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Enrolled?']]
    

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

    ## exclude SAGA
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["Course"].isin(["MQS22", "MQS21"])
    ]

    semester_attd_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Term", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    semester_attd_pvt["total"] = semester_attd_pvt.sum(axis=1)
    semester_attd_pvt = semester_attd_pvt.reset_index()
    

    full_term_attd_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)

    full_term_attd_pvt["total"] = full_term_attd_pvt.sum(axis=1)
    full_term_attd_pvt = full_term_attd_pvt.reset_index()
    full_term_attd_pvt["Term"] = "Full Semester"

    semester_attd_pvt = pd.concat([semester_attd_pvt, full_term_attd_pvt])

    semester_attd_pvt["%_present"] = 100 * (
        1 - semester_attd_pvt["unexcused"] / semester_attd_pvt["total"]
    )
    semester_attd_pvt["%_on_time"] = (
        100
        * semester_attd_pvt["present"]
        / (semester_attd_pvt["present"] + semester_attd_pvt["tardy"])
    )

    semester_attd_pvt = semester_attd_pvt.fillna(0)
    for standard in ["%_present", "%_on_time"]:
        semester_attd_pvt[standard] = semester_attd_pvt[standard].apply(
            lambda x: math.ceil(x)
        )

    ## go for entire term

    ## meets present + on time standard

    semester_attd_pvt["meeting_present_standard"] = (
        semester_attd_pvt["%_present"] >= PRESENT_STANDARD
    )
    semester_attd_pvt["meeting_on_time_standard"] = (
        semester_attd_pvt["%_on_time"] >= ON_TIME_STANDARD
    )
    semester_attd_pvt["meet_attd_standard"] = (
        (semester_attd_pvt["meeting_present_standard"] & semester_attd_pvt["meeting_on_time_standard"] ) | (semester_attd_pvt["%_present"] == 100)
    )

    benchmark_pvt = pd.pivot_table(
        semester_attd_pvt,
        index=["StudentID", "Term"],
        values="meet_attd_standard",
        aggfunc=all_true,
    ).reset_index()
    benchmark_pvt.columns = ["StudentID", "Term", "overall_meet_attd_standard"]

    semester_attd_pvt = semester_attd_pvt.merge(
        benchmark_pvt, on=["StudentID", "Term"], how="left"
    )
    print(semester_attd_pvt)

    return semester_attd_pvt


def return_attd_grid(StudentID):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"] == StudentID
    ]

    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(
        return_mp_from_date, args=(school_year,)
    )
    attendance_marks_df["date"] = attendance_marks_df["Date"].apply(
        lambda x: x.strftime("%-m/%d")
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

    ## exclude SAGA
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["Course"].isin(["MQS22", "MQS21"])
    ]

    student_attd_mark_grid = (
        pd.pivot_table(
            attendance_marks_df,
            index="Pd",
            columns="date",
            values="Attendance",
            aggfunc=return_attd_mark,
        )
        .fillna("")
        .reset_index()
    )
    return student_attd_mark_grid


def return_overall_attd_benchmark(PRESENT_STANDARD=90, ON_TIME_STANDARD=80):
    semester_attd_pvt = main(PRESENT_STANDARD=90, ON_TIME_STANDARD=80)
    output_cols = ["StudentID", "Term", "overall_meet_attd_standard"]
    semester_attd_pvt = semester_attd_pvt[output_cols]
    semester_attd_pvt = semester_attd_pvt.sort_values(by=["StudentID", "Term"])
    return semester_attd_pvt.drop_duplicates()


def return_overall_attd_file(PRESENT_STANDARD=90, ON_TIME_STANDARD=80):
    df = return_overall_attd_benchmark(PRESENT_STANDARD=90, ON_TIME_STANDARD=80)

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    df.to_excel(writer, index=False)
    writer.close()
    f.seek(0)

    return f


def return_attd_mark(x):
    return x


def all_true(x):
    return x.all()
