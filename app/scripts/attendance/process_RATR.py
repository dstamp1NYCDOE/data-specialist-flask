import pandas as pd
import random
from app.scripts import scripts, files_df
import app.scripts.utils as utils


def main(RATR_df):
    calendar_filename = "app/data/SchoolCalendar.xlsx"
    calendar_df = pd.read_excel(calendar_filename)
    calendar_df["Holiday?"] = calendar_df["Holiday?"].astype("bool")
    calendar_df["HalfDay?"] = calendar_df["HalfDay?"].astype("bool")
    calendar_df = calendar_df[calendar_df["SchoolDay?"]]
    all_school_days = calendar_df["Date"].to_list()

    RATR_df = clean(RATR_df)
    school_days_already = RATR_df["Date"].to_list()

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    enrolled_students = cr_3_07_df["StudentID"]

    RATR_df = RATR_df[RATR_df["StudentID"].isin(enrolled_students)]

    RATR_df = RATR_df.merge(calendar_df, on="Date", how="left")

    student_attd_df = return_student_attd(RATR_df)
    student_attd_by_month_df = student_attd_by_month(RATR_df)
    student_attd_by_day_of_week_df = student_attd_by_weekday(RATR_df)
    student_attd_by_days_before_break_df = return_student_pvt_by_subcolumn(
        RATR_df, "DaysBeforeBreak"
    )
    student_attd_by_days_after_break = return_student_pvt_by_subcolumn(
        RATR_df, "DaysAfterBreak"
    )
    return student_attd_df


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

    return pvt_tbl


def clean(RATR_df):
    RATR_df["StudentID"] = RATR_df["STUDENT ID"].str.extract("(\d{9})")
    RATR_df["StudentID"] = RATR_df["StudentID"].astype(int)
    RATR_df["Date"] = RATR_df["SCHOOL DAY"].str.extract("(\d{2}/\d{2}/\d{2})")
    RATR_df["Date"] = pd.to_datetime(RATR_df["Date"])
    RATR_df["Weekday"] = RATR_df["Date"].dt.weekday
    RATR_df["Month"] = RATR_df["Date"].apply(lambda x: x.strftime("%Y-%m"))
    return RATR_df


def student_attd_by_month(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", "Month"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl


def student_attd_by_weekday(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", "Weekday"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()
    return pvt_tbl
