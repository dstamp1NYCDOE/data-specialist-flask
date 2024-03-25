import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from flask import current_app, session


def main(month):
    school_year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()

    regents_max_df = process_regents_max.main()

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    if month == "January":
        return for_january(rosters_df, regents_max_df, regents_calendar_df)
    if month == "June":
        return for_june(rosters_df, regents_max_df, regents_calendar_df)


def for_january(rosters_df, regents_max_df, regents_calendar_df):
    df = pd.DataFrame()
    return rosters_df


def for_june(rosters_df, regents_max_df, regents_calendar_df):
    rosters_df["CulminatingCourse"] = rosters_df["Course"].apply(lambda x: x[0:5])
    rosters_df = rosters_df.merge(
        regents_calendar_df[["CourseCode", "CulminatingCourse"]],
        on=["CulminatingCourse"],
        how="inner",
    )
    culminating_course_list = rosters_df[["StudentID", "CourseCode"]].to_dict("records")

    ela_retakes = regents_max_df[
        (regents_max_df["passed?"] == False)
        | (regents_max_df["NumericEquivalent"] < 75)
    ]
    ela_retakes = ela_retakes[ela_retakes["CourseCode"] == "EXRC"]
    ela_retakes["CourseCode"] = ela_retakes["CourseCode"].apply(lambda x: x + "E")

    ela_retakes_lst = ela_retakes[["StudentID", "CourseCode"]].to_dict("records")

    exam_registrations = culminating_course_list + ela_retakes_lst
    exam_registrations_df = pd.DataFrame(exam_registrations)
    exam_registrations_df = exam_registrations_df.drop_duplicates()

    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "Section",
        "Action",
    ]

    exam_registrations_df["LastName"] = ""
    exam_registrations_df["FirstName"] = ""
    exam_registrations_df["GradeLevel"] = ""
    exam_registrations_df["OfficialClass"] = ""
    exam_registrations_df["Section"] = 1
    exam_registrations_df["Course"] = exam_registrations_df["CourseCode"]
    exam_registrations_df["Action"] = "Add"

    return exam_registrations_df[output_cols]
