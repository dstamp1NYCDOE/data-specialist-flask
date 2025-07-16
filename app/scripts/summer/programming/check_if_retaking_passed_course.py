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

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
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
    cr_1_14_df["SummerCode"] = cr_1_14_df["Course"].apply(convert_to_summer_course)

    cr_1_14_df = cr_1_14_df[
        [
            "StudentID",
            "Course",
            "Course Title",
            "SummerCode",
            "Mark",
            "PassFailEquivalent",
            "Year",
            "Term",
            "Credits",
        ]
    ]

    passed_courses_df = cr_1_14_df[cr_1_14_df["PassFailEquivalent"] == "P"]
    passed_courses_df = passed_courses_df[passed_courses_df["Credits"] > 0]
    passed_courses_df = passed_courses_df[passed_courses_df["Course"].str[0] != "P"]

    df = cr_4_01_df.merge(
        passed_courses_df,
        left_on=["StudentID", "Course"],
        right_on=["StudentID", "SummerCode"],
        how="inner",
    )

    df = df.merge(
        cr_s_01_df[["StudentID", "Sending school", "school_name"]],
        on="StudentID",
        how="left",
    )
    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Sending school",
        "school_name",
        "SummerCode",
        "Course Title",
        "Course_y",
        "Year",
        "Term",
        "Mark",
    ]
    df = df[output_cols]

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    df.to_excel(writer, sheet_name="All", index=False)
    for sending_school, students_df in df.groupby("Sending school"):
        students_df.to_excel(writer, sheet_name=sending_school, index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 5)
        worksheet.autofit()

    writer.close()
    f.seek(0)
    return f


def convert_to_summer_course(CourseCode):
    CourseCode = CourseCode[0:2] + "F" + CourseCode[3:]
    if len(CourseCode) > 5:
        return CourseCode[0:5]
    else:
        return CourseCode
