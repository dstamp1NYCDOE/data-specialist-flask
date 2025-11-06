import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from flask import current_app, session


def main(month):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "rosters_and_grades", year_and_semester=year_and_semester
    )
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[rosters_df["Term"] == f"S{term}"]
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()

    regents_max_df = process_regents_max.main()

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    if month == "January":
        return for_january(rosters_df, regents_max_df, regents_calendar_df)
    if month == "June":
        return for_june(rosters_df, regents_max_df, regents_calendar_df)


def for_january(rosters_df, regents_max_df, regents_calendar_df):
   
    courses_to_exclude = [""]
    rosters_df = rosters_df[~rosters_df["Course"].isin(courses_to_exclude)]

    rosters_df["CulminatingCourse"] = rosters_df["Course"].apply(lambda x: x[0:5])
    rosters_df = rosters_df.merge(
        regents_calendar_df[["CourseCode", "CulminatingCourse"]],
        on=["CulminatingCourse"],
        how="inner",
    )

    culminating_course_list = rosters_df[["StudentID", "CourseCode"]].to_dict("records")

    ## 4th year students without passing ELA score
    ela_retakes = regents_max_df[~regents_max_df["passed?"]]
    ela_retakes = ela_retakes[ela_retakes["CourseCode"] == "EXRC"]
    ela_retakes = ela_retakes[ela_retakes["year_in_hs"] >= 4]
    ela_retakes["CourseCode"] = ela_retakes["CourseCode"].apply(lambda x: x + "R")
    ela_retakes_lst = ela_retakes[["StudentID", "CourseCode"]].to_dict("records")

    ## attempted algebra but did not pass
    alg_retakes = regents_max_df[~regents_max_df["passed?"]]
    alg_retakes = alg_retakes[(alg_retakes["CourseCode"] == "MXRF")| (alg_retakes["CourseCode"] == "MXRC")]
    alg_retakes["CourseCode"] = alg_retakes["CourseCode"].apply(lambda x: "MXRFR")
    alg_retakes_lst = alg_retakes[["StudentID", "CourseCode"]].to_dict("records")


    ## 3rd or 4th year students without passing global score
    global_retakes = regents_max_df[~regents_max_df["passed?"]]
    global_retakes = global_retakes[global_retakes["CourseCode"] == "HXRC"]
    global_retakes = global_retakes[global_retakes["year_in_hs"] >= 3]
    global_retakes["CourseCode"] = global_retakes["CourseCode"].apply(lambda x: x + "R")
    global_retakes_lst = global_retakes[["StudentID", "CourseCode"]].to_dict("records")

    ## 4th year students without passing USH score
    ush_retakes = regents_max_df[~regents_max_df["passed?"]]
    ush_retakes = ush_retakes[ush_retakes["CourseCode"] == "HXRK"]
    ush_retakes = ush_retakes[ush_retakes["year_in_hs"] >= 4]
    ush_retakes["CourseCode"] = ush_retakes["CourseCode"].apply(lambda x: x + "R")
    ush_retakes_lst = ush_retakes[["StudentID", "CourseCode"]].to_dict("records")


    ## combine all possible registrations
    exam_registrations = culminating_course_list + ela_retakes_lst + alg_retakes_lst + global_retakes_lst + ush_retakes_lst
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


def for_june(rosters_df, regents_max_df, regents_calendar_df):
    # exclude AP bio students
    courses_to_exclude = ["SBS22X"]
    rosters_df = rosters_df[~rosters_df["Course"].isin(courses_to_exclude)]

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
    ela_retakes = ela_retakes[ela_retakes["year_in_hs"] >= 3]
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
