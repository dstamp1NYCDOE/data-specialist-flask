from flask import session

import pandas as pd
from sklearn.linear_model import LinearRegression

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main(data):

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    grades_df = utils.return_file_as_df(filename)

    ## assignments
    filename = utils.return_most_recent_report(files_df, "assignments")
    assignments_df = utils.return_file_as_df(filename)

    assignments_df = assignments_df[assignments_df["Course"] != ""]

    # drop assignments worth zero
    assignments_df = assignments_df.dropna(subset=["RawScore"])
    assignments_df = assignments_df[assignments_df["WorthPoints"] != 0]

    # drop assignments not graded yet
    not_graded_marks = ["NG", "Ng", "ng"]
    assignments_df = assignments_df[~assignments_df["RawScore"].isin(not_graded_marks)]
    # drop excused assignments
    excused_marks = ["EX", "Ex", "ex", "es", "eng"]
    assignments_df = assignments_df[~assignments_df["RawScore"].isin(excused_marks)]
    # drop assignments with no grade entered
    assignments_df = assignments_df[assignments_df["RawScore"] != ""]
    # drop checkmarks
    assignments_df = assignments_df[assignments_df["RawScore"] != "✓"]

    # convert percentages
    assignments_df["Percent%"] = assignments_df.apply(convert_percentages, axis=1)

    # adjusted worth points
    assignments_group_by_cols = ["Teacher", "Assignment", "Course", "DueDate"]
    assignments_dff = assignments_df.drop_duplicates(
        subset=assignments_group_by_cols + ["Objective"]
    )
    assignments_dff = (
        assignments_dff.groupby(assignments_group_by_cols)[["Objective", "WorthPoints"]]
        .agg({"WorthPoints": ["min", "max", "sum"], "Objective": "nunique"})
        .reset_index()
    )
    reassigned_cols = [
        "Teacher",
        "Assignment",
        "Course",
        "DueDate",
        "WorthPointsMax",
        "WorthPointsMin",
        "WorthPointsSum",
        "ObjectivesCount",
    ]
    assignments_dff.columns = reassigned_cols

    assignments_df = assignments_df.merge(
        assignments_dff, on=assignments_group_by_cols, how="left"
    )

    assignments_df["WorthPoints"] = assignments_df.apply(recompute_worth_points, axis=1)

    assignments_df["numerator"] = (
        assignments_df["WorthPoints"] * assignments_df["Percent%"]
    )
    assignments_df["denominator"] = assignments_df["WorthPoints"]

    student_grades_df = (
        assignments_df.groupby(["StudentID", "Course", "Section", "CategoryWeight"])[
            ["numerator", "denominator"]
        ]
        .sum()
        .reset_index()
    )
    student_grades_df["Category%"] = (
        student_grades_df["numerator"] / student_grades_df["denominator"]
    )
    student_grades_df["weighted%"] = (
        student_grades_df["Category%"] * student_grades_df["CategoryWeight"]
    )

    student_grades_df = (
        student_grades_df.groupby(["StudentID", "Course", "Section"])["weighted%"]
        .sum()
        .reset_index()
    )

    student_grades_df["FinalMark"] = student_grades_df["weighted%"].apply(
        convert_final_mark
    )

    student_grades_df = student_grades_df.reset_index()

    student_grades_df["JupiterCourse"] = student_grades_df["Course"]
    student_grades_df["JupiterSection"] = student_grades_df["Section"]

    student_grades_df = student_grades_df[
        ["StudentID", "JupiterCourse", "JupiterSection", "FinalMark"]
    ]

    return student_grades_df.head(100).to_html()


def recompute_worth_points(row):
    WorthPoints = row["WorthPoints"]
    WorthPointsMax = row["WorthPointsMax"]
    WorthPointsMin = row["WorthPointsMin"]
    WorthPointsSum = row["WorthPointsSum"]
    ObjectivesCount = row["ObjectivesCount"]

    if ObjectivesCount == 0:
        return WorthPoints
    if WorthPointsMax == WorthPointsMin:
        return WorthPoints / ObjectivesCount
    else:
        return WorthPoints / WorthPointsSum


def reconcile_egg_and_jupiter(row):
    egg_mark = row["Mark"]
    jupiter_mark = row["FinalMark"]

    if egg_mark:
        return convert_final_mark(egg_mark)
    else:
        return jupiter_mark


def convert_final_mark(Mark):
    try:
        if Mark < 50:
            return 45
        if Mark < 65:
            return 55
        return round(Mark)
    except:
        return Mark


def convert_percentages(row):
    Percent = row["Percent"]
    RawScore = row["RawScore"]

    correction_dict = {
        "6!": 100,
        '61':100,
        "5%": 100,
        "5’": 100,
        "5!;": 100,
        "5": 100,
        '5!,3!':100,
        '5!,1!':100,
        '5!,5!':100,
        "05!": 100,
        "51":100,
        "!5": 100,
        "5!5!": 100,
        "5!,4!": 100,
        "5!!": 100,
        "5!`": 100,
        "9!": 50,
        "3!!": 85,
        "3!": 85,
        "31": 85,
        "1": 65,
        "11": 65,
        "$1": 65,
        "41": 95,
        "4%": 95,
        '4!,1!':95,
        '4!,3!':95,
        '4!,4!':95,
        '4!,5!':95,
        "4": 95,
        "4!;": 95,
        "4!/": 95,
        "4+": 95,
        '3!,2!':85,
        '3!,4!':85,
        '3!,3!':85,
        "21": 75,
        '!2':75,
        "2": 75,
        "2!,1!": 75,
        "2!,3!": 75,
        '1!,1!':65,
        "01": 50,
        "01%": 50,
        "-!": 50,
        "!": 50,
        "-.": 45,
        "-": 45,
        "/3!":85,
        "23%":23,
        "21%":21,
        "inc":45,
        '/,/':45,
    }

    if Percent in [100, 95, 85, 75, 65, 50, 45]:
        return Percent / 100
    if Percent == 0:
        return 50 / 100
    try:
        if Percent < 100 and Percent > 45:
            return Percent / 100
    except:
        print(RawScore)
        Percent = correction_dict[RawScore]

    if Percent < 100 and Percent > 45:
        return Percent / 100
    else:
        Percent = correction_dict[RawScore]
        return Percent / 100
