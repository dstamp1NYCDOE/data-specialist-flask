import pandas as pd 
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

def main():
    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report(files_df, "jupiter_period_attendance")
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

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
        index=["StudentID","Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student['total'] = attd_by_student.sum(axis=1)

    attd_by_student["%_late"] = attd_by_student["tardy"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student["%_absent"] = attd_by_student["unexcused"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student = attd_by_student.fillna(0)

    attd_by_student["late_freq"] = attd_by_student["%_late"].apply(utils.convert_percentage_to_ratio)

    attd_by_student = attd_by_student.reset_index()
    students_df = students_df.merge(attd_by_student, on=["StudentID"], how='left') 

    return students_df.sort_values(by=["%_late"])

    stats_df = (
        pd.pivot_table(
            attd_by_student,
            index=["Pd"],
            values="%_late",
            aggfunc=("mean", "std"),
        )
        .fillna(0)
        .reset_index()
    )

    attd_by_student = attd_by_student.merge(
        stats_df, on=["Pd"], how="left"
    )

    attd_by_student["z-score"] = attd_by_student.apply(calculate_z_score, axis=1)

    attd_by_student = attd_by_student.sort_values(by=['z-score'], ascending=[False]).reset_index(drop=True)
    return attd_by_student


def calculate_z_score(row):
    schoolwide_mean = row["mean"]
    schoolwide_std = row["std"]
    class_value = row["%_late"]

    if schoolwide_std == 0:
        return 0
    else:
        return (class_value - schoolwide_mean) / schoolwide_std
