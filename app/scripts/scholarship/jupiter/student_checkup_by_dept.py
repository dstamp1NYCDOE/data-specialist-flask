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

    ##drop non-credit bearing classes
    df = df[df["Course"].str[0] != "G"]
    df = df[df["Course"].str[0] != "Z"]
    df = df[df["Course"].str[0] != "R"]

    ## drop non core ELA
    df = df[df["Course"].str[0:2] != "EQ"]
    df = df[df["Course"].str[0:2] != "ES"]

    df["Dept"] = df["Course"].apply(return_department)

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

    dept_pvt_of_failures = pd.pivot_table(
        students_df[students_df["Passing?"] == False],
        index="Dept",
        columns="#_of_classes_failing",
        values="StudentID",
        aggfunc="count",
        margins=True,
    ).fillna(0)
    dept_pvt_of_failures = dept_pvt_of_failures.reset_index()
    dept_pvt_of_failures.to_excel(
        writer, sheet_name=f"SchoolwideFailingByDept", index=False
    )

    student_level_cols = [
        "LastName",
        "FirstName",
        "Counselor",
        "year_in_hs",
        "Course",
        "Section",
        "Teacher1",
        "Teacher2",
        "Pct",
        "classes_failing",
        "classes_passing",
    ]
    for dept, _df in students_df.groupby("Dept"):
        dept_pvt_of_failures = pd.pivot_table(
            _df[_df["Passing?"] == False],
            index="Teacher1",
            columns="#_of_classes_failing",
            values="StudentID",
            aggfunc="count",
            margins=True,
        ).fillna(0)
        dept_pvt_of_failures = dept_pvt_of_failures.reset_index()
        dept_pvt_of_failures.to_excel(writer, sheet_name=f"{dept}-Summary", index=False)

        students_failing_one_class_df = _df[
            (_df["Passing?"] == False) & (_df["#_of_classes_failing"] == 1)
        ]
        students_failing_one_class_df = students_failing_one_class_df.sort_values(
            by=["Teacher1", "Course", "Section"], ascending=[True, False, False]
        )
        students_failing_one_class_df[student_level_cols].to_excel(
            writer, sheet_name=f"{dept}-FailingOneClass", index=False
        )

        students_failing_all_classes_df = _df[
            (_df["Passing?"] == False) & (_df["#_of_classes_passing"] == 0)
        ]
        students_failing_all_classes_df = students_failing_all_classes_df.sort_values(
            by=["Teacher1", "Course", "Section"], ascending=[True, False, False]
        )
        students_failing_all_classes_df[student_level_cols].to_excel(
            writer, sheet_name=f"{dept}-FailingAllClasses", index=False
        )

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 0)
        worksheet.autofit()

    # return ''
    writer.close()
    f.seek(0)

    download_name = f"{year_and_semester}-JupiterGradesStudentCheckupByDept-{dt.datetime.now().strftime('%Y_%m_%d')}.xlsx"
    return f, download_name


def return_department(course_code):
    if course_code[1] == "K" and course_code[0] != "B":
        return "CTE-SD"
    if course_code[0:2] == "TQ":
        return "CTE-SD"
    if course_code[0:2] == "TZ":
        return "CTE-FMM"
    if course_code[0] == "S":
        return "Science"
    if course_code[0] == "M":
        return "Math"
    if course_code[0] == "E":
        return "ELA"
    if course_code[0] == "F":
        return "LOTE"
    if course_code[0] == "H":
        return "SS"
    if course_code[0:2] == "PP":
        return "PE"
    if course_code[0:2] == "PH":
        return "Health"
    if course_code[0:2] == "AH":
        return "SS"
    if course_code[0:2] == "AF":
        return "CTE-FD"
    if course_code[0] == "B":
        return "CTE-FMM"
    if course_code[0:2] == "TU":
        return "CTE-FMM"
    if course_code[0:2] == "AC":
        return "CTE-Photo"
    if course_code == "ALS21TP":
        return "CTE-Photo"
    if course_code == "ALS22QP":
        return "CTE-Photo"
    if course_code == "ABS11":
        return "CTE-FMM"
    if course_code[0] == "A":
        return "CTE-AD"
    else:
        return "check"
