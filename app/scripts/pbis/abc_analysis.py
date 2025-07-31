from flask import session
import pandas as pd

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from app.scripts.attendance.jupiter.stats_by_student import (
    main as attd_stats_by_student,
)


def main(form, request):
    attd_df = attd_stats_by_student()
    grades_df = return_student_grades()

    df = grades_df.merge(attd_df, on=["StudentID", "Course"], how="left")

    pvt_tbl = pd.pivot_table(
        df[df["Pd"] == 1],
        index=["#_failing", "AttdTier"],
        columns="Passing?",
        values="StudentID",
        aggfunc="count",
    )
    pvt_tbl["passing_%"] = pvt_tbl[True] / (pvt_tbl[True] + pvt_tbl[False])
    return pvt_tbl


def return_student_grades():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "rosters_and_grades", year_and_semester=year_and_semester
    )
    df = utils.return_file_as_df(filename)
    ## drop courses with no grades
    df = df.dropna(subset=["Pct"])
    # filter to S1 and S2
    df = df[df["Term"].isin(["S1", "S2"])]
    ## identify if passing
    df["Passing?"] = df["Pct"] >= 65

    ## pivot table
    pvt_tbl = pd.pivot_table(
        df,
        index=["StudentID", "Term"],
        columns="Passing?",
        values="Course",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl = pvt_tbl.reset_index()
    pvt_tbl.columns = ["StudentID", "Term", "#_failing", "#_passing"]
    ## combine grades with overall passing/failing number
    df = df.merge(pvt_tbl, on=["StudentID", "Term"], how="left")

    return df
