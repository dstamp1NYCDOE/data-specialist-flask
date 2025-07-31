
from flask import session
import pandas as pd

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"  

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    df = utils.return_file_as_df(filename)

    ## drop courses with no grades
    df = df.dropna(subset=["Pct"])
    ## drop zero credit classes
    df = df[~df["Course"].str[0].isin(["G"])]
    # filter to S1 and S2
    df = df[df["Term"].isin(["S1", "S2"])]
    ## identify if passing
    df["Passing?"] = df["Pct"] >= 65

    print(df)
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

    ## teacher pvt
    pvt_tbl = pd.pivot_table(
        df[df["Passing?"] == False],
        index=["Teacher1", "Term"],
        columns="#_failing",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total_failing_students"] = pvt_tbl.sum(axis=1)
    pvt_tbl["%_failing_one"] = pvt_tbl[1] / pvt_tbl["total_failing_students"]

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl
