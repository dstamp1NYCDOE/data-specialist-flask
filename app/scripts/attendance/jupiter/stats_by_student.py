import pandas as pd
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import files_df

from app.scripts.attendance.jupiter.process import process_local_file as process_jupiter_data

from app.scripts.attendance.attendance_tiers import return_attd_tier


def main():
    attendance_marks_df = process_jupiter_data()

    students_df = attendance_marks_df.drop_duplicates(
        subset=["StudentID", "Course", "Pd"]
    )
    students_df = students_df[["StudentID", "Course", "Teacher", "Pd"]]

    student_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "LastName", "FirstName", "year_in_hs", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    student_pvt["late_%"] = student_pvt["tardy"] / (
        student_pvt["tardy"] + student_pvt["present"]
    )
    student_pvt["absent_%"] = (student_pvt["excused"] + student_pvt["unexcused"]) / (
        student_pvt["excused"]
        + student_pvt["unexcused"]
        + student_pvt["tardy"]
        + student_pvt["present"]
    )
    student_pvt = student_pvt.reset_index()

    late_stats_pvt = pd.pivot_table(
        student_pvt, index="Pd", values="late_%", aggfunc=("mean", "std")
    )
    late_stats_pvt = late_stats_pvt.reset_index()
    late_stats_pvt.columns = ["Pd", "late_%_mean", "late_%_std"]
    student_pvt = student_pvt.merge(late_stats_pvt, on=["Pd"], how="left")

    absent_stats_pvt = pd.pivot_table(
        student_pvt, index="Pd", values="absent_%", aggfunc=("mean", "std")
    )
    absent_stats_pvt = absent_stats_pvt.reset_index()
    absent_stats_pvt.columns = ["Pd", "absent_%_mean", "absent_%_std"]
    student_pvt = student_pvt.merge(absent_stats_pvt, on=["Pd"], how="left")

    student_pvt["absent_%_z_score"] = (
        student_pvt["absent_%"] - student_pvt["absent_%_mean"]
    ) / student_pvt["absent_%_std"]
    student_pvt["late_%_z_score"] = (
        student_pvt["late_%"] - student_pvt["late_%_mean"]
    ) / student_pvt["late_%_std"]

    student_pvt = student_pvt.merge(students_df, on=["StudentID", "Pd"], how="left")

    student_pvt["AttdTier"] = student_pvt["absent_%"].apply(return_attd_tier)
    return student_pvt
