import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "4_01", year_and_semester
    )
    cr_4_01_df = utils.return_file_as_df(filename)
    cr_4_01_df["ModifiedCourseCode"] = cr_4_01_df["Course"].apply(
        convert_to_school_year_course
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_14", year_and_semester
    )
    cr_1_14_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(
        files_df,
        "1_30",
    )
    cr_1_30_df = utils.return_file_as_df(filename)
    marks_df = cr_1_30_df[["Mark", "PassFailEquivalent"]]

    cr_1_14_df = cr_1_14_df.merge(marks_df, on=["Mark"]).fillna("F")
    cr_1_14_df["ModifiedCourseCode"] = cr_1_14_df["Course"].apply(
        convert_to_school_year_course
    )

    cr_1_14_df = cr_1_14_df[
        [
            "StudentID",
            "ModifiedCourseCode",
            "Course Title",
            "Mark",
            "PassFailEquivalent",
            "Year",
            "Term",
            "Credits",
        ]
    ]

    passed_courses_df = cr_1_14_df[cr_1_14_df["PassFailEquivalent"] == "P"]
    passed_courses_df = passed_courses_df[passed_courses_df["Credits"] > 0]
    passed_courses_df = passed_courses_df[
        passed_courses_df["ModifiedCourseCode"].str[0] != "P"
    ]

    df = cr_4_01_df.merge(
        passed_courses_df,
        on=["StudentID", "ModifiedCourseCode"],
        how="inner",
    )

    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course Title",
        "Year",
        "Term",
        "Mark",
    ]
    # df = df[output_cols]

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    df.to_excel(writer, sheet_name="All", index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 5)
        worksheet.autofit()

    writer.close()
    f.seek(0)
    return f


def convert_to_school_year_course(course_code):
    if len(course_code) >= 5:
        if course_code[2] == "F":
            return course_code[0:2] + "S" + course_code[3:5]
        else:
            return course_code[0:5]
    return course_code
