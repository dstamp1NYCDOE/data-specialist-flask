import pandas as pd
import numpy as np
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import session

from io import BytesIO
import os
import re
import math

from flask import current_app


def main():
    year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(filename)

    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left"
    ).dropna()

    filename = utils.return_most_recent_report(files_df, "1_01")
    cr_1_01_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)

    ## previously lab eligible
    science_courses_df = cr_1_14_df[cr_1_14_df["Course"].str[0] == "S"]
    science_courses_df = science_courses_df[science_courses_df["Year"] < year]
    science_courses_df["Curriculum"] = science_courses_df["Course"].str[0:2]
    science_labs_df = science_courses_df[
        science_courses_df["Course Title"].str.contains(
            "LAB", flags=re.IGNORECASE, regex=True
        )
    ]

    lab_eligibility_lst = []
    for (StudentID, Curriculum), student_science_labs_df in science_labs_df.groupby(
        ["StudentID", "Curriculum"]
    ):
        lab_eligibility = {
            "StudentID": StudentID,
            "Curriculum": Curriculum,
            "LabEligible": student_science_labs_df.iloc[-1]["NumericEquivalent"] >= 65,
        }
        lab_eligibility_lst.append(lab_eligibility)

    lab_eligibility_df = pd.DataFrame(lab_eligibility_lst)

    print(lab_eligibility_df)

    ### check current term lab eligibility
    lab_courses = [
        "SLS22QL",
        "SES22QL",
        "SCS22QL",
        "SPS22QL",
    ]
    current_lab_courses_df = cr_1_01_df[cr_1_01_df["Course"].isin(lab_courses)]
    current_lab_courses_df["Curriculum"] = current_lab_courses_df["Course"].str[0:2]
    current_lab_courses_df["LabEligible"] = current_lab_courses_df.apply(
        return_last_entered_1_01_grade, axis=1
    )
    current_lab_courses_df = current_lab_courses_df[
        ["StudentID", "Curriculum", "LabEligible"]
    ]

    year_and_semester = f"{year}-{term}"

    filename = f"{year_and_semester}_9999-12-31_lab-eligibility.xlsx"

    path = os.path.join(
        current_app.root_path, f"data/{year_and_semester}/lab-eligibility"
    )
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    filename = os.path.join(path, filename)

    writer = pd.ExcelWriter(filename)
    current_lab_courses_df.to_excel(
        writer, index=False, sheet_name="current_lab_eligibility"
    )

    lab_eligibility_df.to_excel(
        writer, index=False, sheet_name="previous_lab_eligibility"
    )

    combined_df = pd.concat([lab_eligibility_df,current_lab_courses_df])
    combined_df['LabEligible'] = combined_df['LabEligible'].astype(bool)
    combined_df.to_excel(
        writer, index=False, sheet_name="combined_lab_eligibility"
    )

    writer.close()

    with open(filename, "rb") as f:
        return f


def return_last_entered_1_01_grade(student_row):
    marks = ["FinalMark", "Mark3", "Mark2", "Mark1"]
    for mark in marks:
        if student_row[mark] in ["P", "F"]:
            return student_row[mark] == "P"
