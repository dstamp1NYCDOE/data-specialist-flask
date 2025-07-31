import pandas as pd  #

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def main():
    school_year = session["school_year"]
    cte_df = pd.DataFrame()

    filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(filename)
    cr_1_14_df["is_CTE?"] = cr_1_14_df["Course"].apply(return_if_CTE)

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left"
    )
    cr_1_14_df["earned_credit?"] = cr_1_14_df["NumericEquivalent"].apply(
        lambda x: x >= 65
    )

    cte_credits_earned_pvt = pd.pivot_table(
        cr_1_14_df[(cr_1_14_df["is_CTE?"]) & (cr_1_14_df["earned_credit?"])],
        index="StudentID",
        aggfunc="sum",
        values="Credits",
    )
    cte_credits_earned_pvt = cte_credits_earned_pvt.reset_index()
    cte_credits_earned_pvt["CTE_credits_met?"] = cte_credits_earned_pvt["Credits"] >= 10

    fall_courses_df = cr_1_14_df[
        (cr_1_14_df["Year"] == school_year) & (cr_1_14_df["Term"] == 1)
    ]

    WBL_df = cr_1_14_df[cr_1_14_df["Course"] == "WBLHR"]
    WBL_df = WBL_df[["StudentID", "Mark"]]
    WBL_df["Mark"] = WBL_df["Mark"].apply(lambda x: x == "P")
    WBL_df.columns = ["StudentID", "WBLHR"]

    CTE_majors_df = fall_courses_df[fall_courses_df["is_CTE?"]]
    CTE_majors_df["Major"] = CTE_majors_df["Course"].apply(return_CTE_major)
    CTE_majors_df = CTE_majors_df[["StudentID", "LastName", "FirstName", "Major"]]

    CTE_majors_df = CTE_majors_df.merge(WBL_df, on="StudentID", how="left").fillna(
        False
    )

    CTE_majors_df = CTE_majors_df.merge(
        cte_credits_earned_pvt[["StudentID", "CTE_credits_met?"]],
        on="StudentID",
        how="left",
    ).fillna(False)

    ## passed final CTE Course
    spring_courses_df = cr_1_14_df[
        (cr_1_14_df["Year"] == school_year) & (cr_1_14_df["Term"] == 2)
    ]
    cte_final_course_df = spring_courses_df[spring_courses_df["Credits"] == 2]
    cte_final_course_df["CTE_Culminating_Project_Passed?"] = cte_final_course_df[
        "earned_credit?"
    ]
    cte_final_course_df = cte_final_course_df[
        ["StudentID", "CTE_Culminating_Project_Passed?"]
    ]

    CTE_majors_df = CTE_majors_df.merge(
        cte_final_course_df, on=["StudentID"], how="left"
    ).fillna(False)

    ## return number of art credits
    art_credits_pvt = pd.pivot_table(
        cr_1_14_df[
            (cr_1_14_df["Course"].str[0] == "A") & (cr_1_14_df["earned_credit?"])
        ],
        index="StudentID",
        aggfunc="sum",
        values="Credits",
    )
    art_credits_pvt = art_credits_pvt.reset_index()
    art_credits_pvt["Arts Endorsed?"] = art_credits_pvt["Credits"] >= 10

    return CTE_majors_df


def return_CTE_major(course):
    curriculum = course[0:2]
    if curriculum == "AF":
        return "FD"
    if course == "ALS21T":
        return "AD"
    if course == "ALS21TP":
        return "Photo"
    if curriculum == "BN":
        return "FMM"
    if curriculum == "BN":
        return "FMM"
    if curriculum == "BM":
        return "VP"
    if curriculum == "TQ":
        return "SD"


def return_if_CTE(course):
    if len(course) <= 5:
        return False
    if course in ["SKS21X", "SKS22X"]:
        return True
    elif course[5] == "T":
        return True
    else:
        return False
