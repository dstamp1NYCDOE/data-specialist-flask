import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.date_to_marking_period import return_mp_from_date

import math 

def main(data):
    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]

    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    still_enrolled_students = students_df['StudentID'].unique()

    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report(files_df, "jupiter_period_attendance")
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## drop SAGA
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course']!='MQS22']

    ## keep enrolled students only
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"].isin(still_enrolled_students)
    ]

    ## convert date and insert marking period
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(return_mp_from_date, args=(school_year,))

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
        index=["StudentID",'Term',"Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student['total'] = attd_by_student.sum(axis=1)

    attd_by_student['%_present'] = 100*(1-attd_by_student['unexcused']/attd_by_student['total'])
    attd_by_student['%_on_time'] = 100*attd_by_student['present']/(attd_by_student['present'] + attd_by_student['tardy'])
    attd_by_student = attd_by_student.fillna(0)
    
    for standard in ['%_present','%_on_time']:
        attd_by_student[standard] = attd_by_student[standard].apply(lambda x: math.ceil(x))
    


    ON_TIME_BENCHMARK = 80
    attd_by_student["meeting_on_time_benchmark"] = attd_by_student["%_on_time"] >= ON_TIME_BENCHMARK

    PRESENT_BENCHMARK = 90
    attd_by_student["meeting_present_benchmark"] = attd_by_student["%_present"] >= PRESENT_BENCHMARK


    attd_by_student = attd_by_student.reset_index()

    ### pivots by student/mp for late benchmark and for present benchmark

    late_benchmark_pvt_tbl = pd.pivot_table(
        attd_by_student,
        index=["StudentID", "Term"],
        columns='meeting_on_time_benchmark',
        values="Pd",
        aggfunc="count",
    ).fillna(0).reset_index()
    late_benchmark_pvt_tbl["%_of_classes_meeting_on_time_benchmark"] = (
        late_benchmark_pvt_tbl[True]
    ) / (late_benchmark_pvt_tbl[True] + late_benchmark_pvt_tbl[False])
    late_benchmark_pvt_tbl["meeting_on_time_benchmark"] = (
        late_benchmark_pvt_tbl["%_of_classes_meeting_on_time_benchmark"] >= 1
    )

    late_benchmark_pvt_tbl = late_benchmark_pvt_tbl[
        [
            "StudentID",
            "Term",
            "%_of_classes_meeting_on_time_benchmark",
            "meeting_on_time_benchmark",
        ]
    ]

    ### present
    present_benchmark_pvt_tbl = pd.pivot_table(
        attd_by_student,
        index=["StudentID", "Term"],
        columns='meeting_present_benchmark',
        values="Pd",
        aggfunc="count",
    ).fillna(0).reset_index()
    present_benchmark_pvt_tbl["%_of_classes_meeting_present_benchmark"] = (
        present_benchmark_pvt_tbl[True]
    ) / (present_benchmark_pvt_tbl[True] + present_benchmark_pvt_tbl[False])
    present_benchmark_pvt_tbl["meeting_present_benchmark"] = (
        present_benchmark_pvt_tbl["%_of_classes_meeting_present_benchmark"] >= 1
    )

    present_benchmark_pvt_tbl = present_benchmark_pvt_tbl[
        [
            "StudentID",
            "Term",
            "%_of_classes_meeting_present_benchmark",
            "meeting_present_benchmark",
        ]
    ]

    df = present_benchmark_pvt_tbl.merge(late_benchmark_pvt_tbl, on=['StudentID','Term'], how="left")
    df["meeting_attendance_benchmark"] = (
        df["meeting_present_benchmark"] & df["meeting_on_time_benchmark"]
    )

    students_df = students_df.merge(df, on=["StudentID"], how="left")

    return students_df
