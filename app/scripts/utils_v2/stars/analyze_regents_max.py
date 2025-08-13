import pandas as pd
import numpy as np

import app.scripts.utils as utils
from app.scripts import files_df

from flask import session

from functools import reduce

def main(cr_1_42_df):
    school_year = session["school_year"]
    cr_1_42_df["year_in_hs"] = cr_1_42_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    df = cr_1_42_df.set_index("StudentID")
    df1 = pd.DataFrame(
        {
            "Exam": np.tile(df.columns, len(df)),
            "StudentID": df.index.repeat(df.shape[1]),
            "Score": df.values.ravel(),
        }
    )
    df1 = df1[df1["Exam"].str.contains("REG")]
    df1 = df1.dropna()
    df1["Mark"] = df1["Score"].str[6:]

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    df1 = df1.merge(cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left")

    df1["passed?"] = df1.apply(determine_if_passed, axis=1)
    df1["CourseCode"] = df1["Score"].str[0:4]
    df1["ContentArea"] = df1["CourseCode"].str[0]

    ##
    ## pivot df1 on the StudentID and Exam column returning the passed? column as the value. Append "Passed?" to each of the columns in the pivot table before resetting the index
    passed_pivot = df1.pivot_table(
        index="StudentID",
        columns="Exam",
        values="passed?",
        aggfunc="first",    
    ).fillna(False)
    passed_pivot.columns = [f"{col} Passed?" for col in passed_pivot.columns]
    passed_pivot = passed_pivot.reset_index()

    ## pivot df1 on StudentID and Exam column returning the NumericEquivalent column as the value. Append "NumericEquivalent" to each of the columns in the pivot table before resetting the index
    numeric_equiv_pivot = df1.pivot_table(
        index="StudentID",
        columns="Exam",
        values="NumericEquivalent",
        aggfunc="first",
    )
    numeric_equiv_pivot.columns = [f"{col} NumericEquivalent" for col in numeric_equiv_pivot.columns]
    numeric_equiv_pivot = numeric_equiv_pivot.reset_index()
    print(numeric_equiv_pivot)

    ## for each content area, determine how many passing exam scores (passed? == True). The content area is the first character in the CourseCode column
    content_area_passed_pivot = df1[df1['passed?']].pivot_table(
        index="StudentID",
        columns="ContentArea",
        values="passed?",

        aggfunc="sum",
    ).fillna(0)
    content_area_passed_pivot.columns = [f"{col} Passed Count" for col in content_area_passed_pivot.columns]
    content_area_passed_pivot = content_area_passed_pivot.reset_index()
    content_area_passed_pivot['met_regents_grad_requirements'] = content_area_passed_pivot.apply(
        determine_if_met_regents_grad_requirements, axis=1
    )
    content_area_passed_pivot['met_advanced_regents_grad_requirements'] = content_area_passed_pivot.apply(
        determine_if_met_advanced_regents_grad_requirements, axis=1
    )


    ## combine list of dataframes into one on the StudentID column
    dataframes = [passed_pivot, numeric_equiv_pivot, content_area_passed_pivot]  # your list of dataframes
    merged_df = reduce(lambda left, right: pd.merge(left, right, on='StudentID'), dataframes)

    return merged_df

def determine_if_met_regents_grad_requirements(content_area_passed_pivot_row):
    E_PassedCount = content_area_passed_pivot_row["E Passed Count"]
    M_PassedCount = content_area_passed_pivot_row["M Passed Count"]
    S_PassedCount = content_area_passed_pivot_row["S Passed Count"]
    H_PassedCount = content_area_passed_pivot_row["H Passed Count"]

    if E_PassedCount < 1:
        return False
    if M_PassedCount < 1:
        return False
    if S_PassedCount < 1:
        return False
    if H_PassedCount < 1:
        return False
    
    return M_PassedCount >=2 or S_PassedCount >=2 or H_PassedCount >=2

def determine_if_met_advanced_regents_grad_requirements(content_area_passed_pivot_row):
    E_PassedCount = content_area_passed_pivot_row["E Passed Count"]
    M_PassedCount = content_area_passed_pivot_row["M Passed Count"]
    S_PassedCount = content_area_passed_pivot_row["S Passed Count"]
    H_PassedCount = content_area_passed_pivot_row["H Passed Count"]

    if E_PassedCount < 1:
        return False
    if M_PassedCount < 3:
        return False
    if S_PassedCount < 2:
        return False
    if H_PassedCount < 2:
        return False
    
    return M_PassedCount >=3 or S_PassedCount >=2 or H_PassedCount >=2

def determine_if_passed(student_row):
    mark = student_row["Mark"]
    NumericEquivalent = student_row["NumericEquivalent"]

    if mark in ["WA", "WG"]:
        return True
    elif mark in ["ABS", "INV"]:
        return False
    else:
        return NumericEquivalent >= 65



    