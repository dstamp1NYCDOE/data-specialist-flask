from flask import session
import pandas as pd
import datetime as dt

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO


def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "rosters_and_grades", year_and_semester=year_and_semester
    )
    df = utils.return_file_as_df(filename).fillna({"Teacher2": ""})

    filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_master_schedule", year_and_semester=year_and_semester
    )
    dff = utils.return_file_as_df(filename)[["Course", "Section", "CourseTitle"]]
    df = df.merge(dff, on=["Course", "Section"], how="left")

    df["Summary"] = (
        df["CourseTitle"]
        + " - "
        + df["Teacher1"]
        + " - "
        + df["Pct"].apply(lambda x: str(x))
    )

    ## drop courses with no grades
    df = df.dropna(subset=["Pct"])
    ## drop non-credit bearing courses
    df = df[df["Course"].str[0] != "G"]
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
    pvt_tbl.columns = ["#_of_classes_failing", "#_of_classes_passing"]
    pvt_tbl["total_classes"] = pvt_tbl.sum(axis=1)
    pvt_tbl["%_of_classes_passing"] = (
        pvt_tbl["#_of_classes_passing"] / pvt_tbl["total_classes"]
    )
    pvt_tbl["passing_all_classes"] = pvt_tbl["#_of_classes_failing"] == 0
    pvt_tbl = pvt_tbl.reset_index()

    ## course info
    summary_pvt_tbl = pd.pivot_table(
        df,
        index=["StudentID", "Term"],
        columns="Passing?",
        values="Summary",
        aggfunc=lambda x: "\n".join(list(x)),
    ).fillna("")
    summary_pvt_tbl.columns = ["classes_failing", "classes_passing"]
    summary_pvt_tbl = summary_pvt_tbl.reset_index()
    grades_df = pvt_tbl.merge(summary_pvt_tbl, on=["StudentID", "Term"], how="left")

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(filename)
    cr_1_49_df = cr_1_49_df[
        [
            "StudentID",
            "Counselor",
        ]
    ]
    cr_3_07_df = cr_3_07_df.merge(cr_1_49_df, on="StudentID", how="left")

    students_df = cr_3_07_df[
        ["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"]
    ]

    students_df = students_df.merge(grades_df, on="StudentID", how="left").dropna()
    students_df = students_df.merge(df, on=["StudentID", "Term"], how="right").drop(
        columns=["CourseTitle", "Summary", "Term"]
    )

    students_df = students_df.dropna()

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    for teacher, _df in students_df.groupby("Teacher1"):
        _dff = _df.sort_values(
            by=["Passing?", "#_of_classes_failing", "Course", "Section"],
            ascending=[True, True, True, True],
        )
        print(_dff)
        _dff.to_excel(writer, sheet_name=f"{teacher}", index=False)

    writer.close()
    f.seek(0)

    download_name = f"{year_and_semester}-JupiterGradesStudentCheckupByTeacher-{dt.datetime.now().strftime('%Y_%m_%d')}.xlsx"
    return f, download_name
