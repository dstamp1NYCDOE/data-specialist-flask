import pandas as pd
from sklearn.linear_model import LinearRegression

import random
from app.scripts import scripts, files_df
import app.scripts.utils as utils

from itertools import pairwise

from flask import session


def main(RATR_df):
    calendar_filename = "app/data/SchoolCalendar.xlsx"
    calendar_df = pd.read_excel(calendar_filename)
    calendar_df["Holiday?"] = calendar_df["Holiday?"].astype("bool")
    calendar_df["HalfDay?"] = calendar_df["HalfDay?"].astype("bool")
    calendar_df = calendar_df[calendar_df["SchoolDay?"]]

    RATR_df = clean(RATR_df)

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )
    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]
    enrolled_students = cr_3_07_df["StudentID"]

    RATR_df = RATR_df[RATR_df["StudentID"].isin(enrolled_students)]

    RATR_df = RATR_df.merge(calendar_df, on="Date", how="left")

    student_attd_df = return_student_attd(RATR_df)
    student_attd_by_month_df = student_attd_by_days_before_break_df = (
        return_student_pvt_by_subcolumn(RATR_df, "Month")
    )
    student_attd_by_day_of_week_df = student_attd_by_days_before_break_df = (
        return_student_pvt_by_subcolumn(RATR_df, "Weekday")
    )
    student_attd_by_days_before_break_df = return_student_pvt_by_subcolumn(
        RATR_df, "DaysBeforeBreak"
    )
    student_attd_by_days_after_break = return_student_pvt_by_subcolumn(
        RATR_df, "DaysAfterBreak"
    )

    multiple_day_df = return_multiple_day_df(RATR_df)

    output_df = students_df
    student_attd_df = student_attd_df[["StudentID", "ytd_absence_%"]]
    month_df = student_attd_by_month_df.pivot(
        index="StudentID", columns="Month", values="absence_%"
    )
    monthly_trend_df = return_monthly_trend_df(student_attd_by_month_df)
    month_df = month_df.merge(monthly_trend_df, on=["StudentID"], how="left")

    vacation_extender_df = return_vacation_extender_df(
        student_attd_by_days_before_break_df, student_attd_by_days_after_break
    )
    day_of_week_df = return_day_of_week_df(student_attd_by_day_of_week_df)

    output_df = output_df.merge(student_attd_df, on="StudentID")
    output_df = output_df.merge(month_df, on="StudentID")
    output_df = output_df.merge(vacation_extender_df, on="StudentID")
    output_df = output_df.merge(day_of_week_df, on="StudentID")
    output_df = output_df.merge(multiple_day_df, on="StudentID")

    output_df["AttdTier"] = output_df["ytd_absence_%"].apply(return_attd_tier)
    output_df = output_df.sort_values(by=["year_in_hs", "LastName", "FirstName"])
    return output_df


def return_monthly_trend_df(student_attd_by_month_df):
    metric = "absence_%"
    df = (
        student_attd_by_month_df.groupby(["StudentID"])[metric]
        .apply(determine_weighted_slope)
        .reset_index()
        .rename(columns={metric: f"{metric}_trend"})
    )
    return df


def determine_weighted_slope(data):
    df = pd.DataFrame(list(data), columns=["absence_%"])
    df["X"] = df.index + 1
    df["sample_weights"] = df.index + 1

    regr = LinearRegression()
    regr.fit(df[["X"]], df[["absence_%"]], df["sample_weights"])

    return regr.coef_[0][0]


def return_multiple_day_df(RATR_df):
    df = RATR_df[["StudentID", "Date", "ATTD"]]
    df = df[df["ATTD"] != "I"]

    output_lst = []
    for StudentID, student_attd_df in df.groupby("StudentID"):
        consecutive_days_absent = 0
        possible_pairs = 0
        attd_list = student_attd_df["ATTD"].to_list()
        total_days_absent = attd_list.count("A")
        for i, j in list(pairwise(attd_list)):
            possible_pairs += 1
            if i == "A" and j == "A":
                consecutive_days_absent += 1

        if total_days_absent == 0:
            consecutive_days_absent_metric = 0
        else:
            consecutive_days_absent_metric = consecutive_days_absent / total_days_absent

        temp_dict = {
            "StudentID": StudentID,
            "consecutive_day_pattern": return_consecutive_days_absent_flag(
                consecutive_days_absent_metric
            ),
        }
        output_lst.append(temp_dict)

    return pd.DataFrame(output_lst)


def return_attd_tier(absence_rate):
    if absence_rate <= 0.05:
        return "Tier0-Satisfactory"
    if absence_rate <= 0.10:
        return "Tier1-At Risk"

    if absence_rate <= 0.15:
        return "Tier2-Early"
    if absence_rate <= 0.2:
        return "Tier2-High"

    return "Tier3"


def return_consecutive_days_absent_flag(consecutive_days_absent_metric):
    if consecutive_days_absent_metric <= 0:
        return "Single"

    if consecutive_days_absent_metric <= 0.25:
        return "None"

    return "Multiple"


def return_day_of_week_df(student_attd_by_day_of_week_df):

    df = student_attd_by_day_of_week_df.sort_values("z_score")
    df = df.drop_duplicates(subset=["StudentID"], keep="last")

    df = df.fillna(0)
    df["WeekdayFlag"] = df.apply(return_day_of_week_flag, axis=1)
    return df[["StudentID", "WeekdayFlag"]]


def return_day_of_week_flag(student_row):
    weekday = student_row["Weekday"]
    z_score = student_row["z_score"]
    for threshold, flag in [(1, "High"), (0.75, "Medium"), (0.5, "Low")]:
        if z_score >= threshold:
            return f"{weekday}-{flag}"

    return "No"


def return_vacation_extender_df(
    student_attd_by_days_before_break_df, student_attd_by_days_after_break
):
    day_before_df = student_attd_by_days_before_break_df[
        student_attd_by_days_before_break_df["DaysBeforeBreak"] == 1
    ]
    day_after_df = student_attd_by_days_after_break[
        student_attd_by_days_after_break["DaysAfterBreak"] == 1
    ]
    df = day_before_df.merge(day_after_df, on=["StudentID"])
    df["Holiday Pattern"] = df.apply(return_vacation_extender_flag, axis=1)

    df = df[["StudentID", "Holiday Pattern"]]
    return df


def return_vacation_extender_flag(student_row):
    before_z_score = student_row["z_score_x"]
    after_z_score = student_row["z_score_y"]

    if before_z_score < 0.25 and after_z_score < 0.25:
        return "No"

    if before_z_score > 2 and after_z_score > 2:
        return "Yes-High"
    if before_z_score > 1 and after_z_score > 1:
        return "Yes-Medium"
    if before_z_score > 0.25 and after_z_score > 0.25:
        return "Yes-Low"

    if before_z_score > 0.25:
        return "Yes-Before"
    if after_z_score > 0.25:
        return "Yes-After"


def return_student_attd(RATR_df):
    pvt_tbl = pd.pivot_table(
        RATR_df,
        index="StudentID",
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["actual_total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["actual_absences"] = pvt_tbl["A"]
    pvt_tbl["ytd_absence_%"] = pvt_tbl["A"] / pvt_tbl["actual_total"]

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl


def return_student_pvt_by_subcolumn(RATR_df, subcolumn):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", subcolumn],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()

    student_avg_and_std_dev = pd.pivot_table(
        pvt_tbl,
        index="StudentID",
        values="absence_%",
        aggfunc=["mean", "std"],
    ).reset_index()

    student_avg_and_std_dev.columns = ["StudentID", "Avg", "Std"]

    output_df = pvt_tbl[["StudentID", subcolumn, "absence_%"]].merge(
        student_avg_and_std_dev, on=["StudentID"], how="left"
    )

    output_df[f"z_score"] = (output_df["absence_%"] - output_df["Avg"]) / output_df[
        "Std"
    ]

    output_df = output_df.drop(columns=["Avg", "Std"])

    return output_df


def clean(RATR_df):
    RATR_df["StudentID"] = RATR_df["STUDENT ID"].str.extract("(\d{9})")
    RATR_df["StudentID"] = RATR_df["StudentID"].astype(int)
    RATR_df["Date"] = RATR_df["SCHOOL DAY"].str.extract("(\d{2}/\d{2}/\d{2})")
    RATR_df["Date"] = pd.to_datetime(RATR_df["Date"])
    RATR_df["Weekday"] = RATR_df["Date"].dt.day_name()
    RATR_df["Month"] = RATR_df["Date"].apply(lambda x: x.strftime("%Y-%m"))
    return RATR_df
