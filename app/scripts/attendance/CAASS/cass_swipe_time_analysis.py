from io import BytesIO
import pandas as pd
import datetime as dt
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df


def main(form, request):
    f = BytesIO()

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    CAASS_file = request.files[form.CAASS_file.name]
    CAASS_df = pd.read_csv(CAASS_file)

    ## remove system marked absents
    CAASS_df = CAASS_df[CAASS_df["Attendance Status"] != "Absent"]

    CAASS_df["Entry Datetime"] = pd.to_datetime(
        CAASS_df["Entry Date"] + " " + CAASS_df["Entry Time"]
    )

    CAASS_df["Time"] = pd.to_timedelta(CAASS_df["Entry Datetime"].dt.time.astype(str))
    CAASS_df["DayOfWeek"] = CAASS_df["Entry Datetime"].dt.weekday

    student_pvt = pd.pivot_table(
        CAASS_df,
        index=["Student ID", "Last Name", "First Name"],
        columns="DayOfWeek",
        values="Time",
        aggfunc=(
            q1_time_func,
            avg_time_func,
            q3_time_func,
            earliest_time_func,
            latest_time_func,
        ),
    ).dropna()
    student_pvt = student_pvt.swaplevel(0, 1, axis=1).sort_index(axis=1)

    overall_pvt = pd.pivot_table(
        CAASS_df,
        index="DayOfWeek",
        values="Time",
        aggfunc=(
            q1_time_func,
            avg_time_func,
            q3_time_func,
            earliest_time_func,
            latest_time_func,
        ),
    ).dropna()

    writer = pd.ExcelWriter(f)

    student_pvt.to_excel(writer, sheet_name="avg_entry_time")
    overall_pvt.to_excel(writer, sheet_name="overall_pvt")
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()

    f.seek(0)
    download_name = "CAASS_swipe_analysis.xlsx"
    return f, download_name


def avg_time_func(x):
    out = x.mean().round("min")
    time = (dt.datetime.min + out).time()
    return time


def q1_time_func(x):
    out = x.quantile(0.25).round("min")
    time = (dt.datetime.min + out).time()
    return time


def q3_time_func(x):
    out = x.quantile(0.75).round("min")
    time = (dt.datetime.min + out).time()
    return time


def earliest_time_func(x):
    out = x.min().round("min")
    time = (dt.datetime.min + out).time()
    return time


def latest_time_func(x):
    out = x.max().round("min")
    time = (dt.datetime.min + out).time()
    return time
