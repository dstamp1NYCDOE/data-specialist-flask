import pandas as pd 

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
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

    attd_by_teacher_and_period = pd.pivot_table(
        attendance_marks_df,
        index=["Teacher",'Pd','Course'],
        columns="Type",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)
    attd_by_teacher_and_period['total'] = attd_by_teacher_and_period.sum(axis=1)

    attd_by_teacher_and_period["%_late"] = (
        attd_by_teacher_and_period["tardy"] / attd_by_teacher_and_period["total"]
    )
    attd_by_teacher_and_period["%_absent"] = (
        attd_by_teacher_and_period["unexcused"] / attd_by_teacher_and_period["total"]
    )

    attd_by_teacher_and_period = attd_by_teacher_and_period.reset_index()

    stats_df = (
        pd.pivot_table(
            attd_by_teacher_and_period,
            index=["Pd"],
            values="%_late",
            aggfunc=("mean", "std"),
        )
        .fillna(0)
        .reset_index()
    )

    attd_by_teacher_and_period = attd_by_teacher_and_period.merge(
        stats_df, on=["Pd"], how="left"
    )

    attd_by_teacher_and_period["z-score"] = attd_by_teacher_and_period.apply(calculate_z_score, axis=1)

    attd_by_teacher_and_period = attd_by_teacher_and_period.sort_values(by=['z-score'], ascending=[False]).reset_index(drop=True)
    return attd_by_teacher_and_period


def calculate_z_score(row):
    schoolwide_mean = row["mean"]
    schoolwide_std = row["std"]
    class_value = row["%_late"]

    if schoolwide_std == 0:
        return 0
    else:
        return (class_value - schoolwide_mean) / schoolwide_std
