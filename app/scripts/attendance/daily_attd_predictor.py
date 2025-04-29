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

    days_to_simulate = [x for x in all_school_days if x not in school_days_already]

    days_to_simulate_df = calendar_df[calendar_df["Date"].isin(days_to_simulate)]

    simulated_attd = []
    for StudentID in enrolled_students:
        most_recent_monthly_attd = return_most_recent_monthly_attd(
            student_attd_by_month_df, StudentID
        )

        for index, day_to_simulate in days_to_simulate_df.iterrows():
            weekday = day_to_simulate["Date"].weekday()
            days_before_break = day_to_simulate["DaysBeforeBreak"]
            days_after_break = day_to_simulate["DaysAfterBreak"]

            days_before_break_absence_rate = return_avg_absence_rate_by_col(
                student_attd_by_days_before_break_df,
                StudentID,
                "DaysBeforeBreak",
                days_before_break,
            )
            days_after_break_absence_rate = return_avg_absence_rate_by_col(
                student_attd_by_days_after_break,
                StudentID,
                "DaysAfterBreak",
                days_after_break,
            )

            day_of_week_absence_rate = return_day_of_week_absence_rate(
                student_attd_by_day_of_week_df, StudentID, weekday
            )
            absence_probability = return_absence_probability(
                day_of_week_absence_rate,
                most_recent_monthly_attd,
                days_before_break_absence_rate,
                days_after_break_absence_rate,
            )
            student_temp = {
                "StudentID": StudentID,
                "Date": day_to_simulate,
                "ATTD": return_simulated_attd_mark(absence_probability),
            }
            simulated_attd.append(student_temp)

    simulated_df = pd.DataFrame(simulated_attd)

    pvt_tbl = pd.pivot_table(
        simulated_df,
        index="StudentID",
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["modeled_total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["modeled_absences"] = pvt_tbl["A"]
    pvt_tbl["modeled_absence_%"] = pvt_tbl["A"] / pvt_tbl["modeled_total"]
    pvt_tbl = pvt_tbl.reset_index()

    pvt_tbl = pvt_tbl[
        ["StudentID", "modeled_absences", "modeled_total", "modeled_absence_%"]
    ]

    output_df = student_attd_df[
        ["StudentID", "actual_absences", "actual_total", "ytd_absence_%"]
    ].merge(pvt_tbl, on="StudentID")

    output_df["predicted_absences"] = (
        output_df["actual_absences"] + output_df["modeled_absences"]
    )
    output_df["predicted_total"] = (
        output_df["actual_total"] + output_df["modeled_total"]
    )

    output_df["predicted_absence_%"] = (
        output_df["predicted_absences"] / output_df["predicted_total"]
    )

    output_df = cr_3_07_df[["StudentID", "LastName", "FirstName"]].merge(
        output_df, on="StudentID", how="left"
    )
    return output_df


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


def return_absence_probability(
    day_of_week_absence_rate,
    most_recent_monthly_attd,
    days_before_break_absence_rate,
    days_after_break_absence_rate,
):
    return (
        0.5 * day_of_week_absence_rate
        + 0.25 * most_recent_monthly_attd
        + 0.125 * days_before_break_absence_rate
        + 0.125 * days_after_break_absence_rate
        + 0.00001 * random.random()
    )


def return_simulated_attd_mark(absence_probability):
    if random.random() < absence_probability:
        return "A"
    else:
        return "P"


def return_most_recent_monthly_attd(student_attd_by_month_df, StudentID):
    most_recent_monthly_absence_rate = student_attd_by_month_df[
        (student_attd_by_month_df["StudentID"] == StudentID)
    ]["absence_%"].to_list()
    try:
        most_recent_monthly_absence_rate = most_recent_monthly_absence_rate[-1]
    except:
        most_recent_monthly_absence_rate = 0
    return most_recent_monthly_absence_rate


def return_avg_absence_rate_by_col(df, StudentID, col, value):
    absence_rate = df[(df["StudentID"] == StudentID) & (df[col] == value)][
        "absence_%"
    ].to_list()
    try:
        absence_rate = absence_rate[0]
    except:
        absence_rate = 0
    return absence_rate


def return_day_of_week_absence_rate(student_attd_by_day_of_week_df, StudentID, weekday):
    day_of_week_absence_rate = student_attd_by_day_of_week_df[
        (student_attd_by_day_of_week_df["StudentID"] == StudentID)
        & (student_attd_by_day_of_week_df["Weekday"] == weekday)
    ]["absence_%"].to_list()
    try:
        day_of_week_absence_rate = day_of_week_absence_rate[0]
    except:
        day_of_week_absence_rate = 0
    return day_of_week_absence_rate


def return_student_pvt_by_subcolumn(RATR_df, subcolumn):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", subcolumn],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    if 'L' in pvt_tbl.columns:
        pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    else:
        pvt_tbl["late_%"] = 0
    if 'A' in pvt_tbl.columns:        
        pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]
    else:
        pvt_tbl["absence_%"] = 0

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
