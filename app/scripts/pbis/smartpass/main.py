import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for

# Define class period schedules as module-level constants
# Monday: All periods are 35 minutes
MONDAY_SCHEDULE = [
    (1, dt.time(9, 45), dt.time(10, 20)),   # Period 1: 9:45 - 10:20 (35 min)
    (2, dt.time(10, 20), dt.time(11, 0)),   # Period 2: 10:20 - 11:00 (40 min - includes 5 min passing)
    (3, dt.time(11, 0), dt.time(11, 40)),   # Period 3: 11:00 - 11:40 (40 min)
    (4, dt.time(11, 40), dt.time(12, 20)),  # Period 4: 11:40 - 12:20 (40 min)
    (5, dt.time(12, 20), dt.time(13, 0)),   # Period 5: 12:20 - 13:00 (40 min)
    (6, dt.time(13, 0), dt.time(13, 40)),   # Period 6: 13:00 - 13:40 (40 min)
    (7, dt.time(13, 40), dt.time(14, 20)),  # Period 7: 13:40 - 14:20 (40 min)
    (8, dt.time(14, 20), dt.time(15, 0)),   # Period 8: 14:20 - 15:00 (40 min)
    (9, dt.time(15, 0), dt.time(15, 40)),   # Period 9: 15:00 - 15:40 (40 min)
]

# Tuesday-Friday: Periods 1,2,4,5,6,7,8,9 are 45 minutes; Period 3 is 50 minutes
REGULAR_SCHEDULE = [
    (1, dt.time(8, 5), dt.time(8, 55)),     # Period 1: 8:05 - 8:55 (50 min - includes 5 min passing)
    (2, dt.time(8, 55), dt.time(9, 45)),    # Period 2: 8:55 - 9:45 (50 min)
    (3, dt.time(9, 45), dt.time(10, 40)),   # Period 3: 9:45 - 10:40 (55 min)
    (4, dt.time(10, 40), dt.time(11, 30)),  # Period 4: 10:40 - 11:30 (50 min)
    (5, dt.time(11, 30), dt.time(12, 20)),  # Period 5: 11:30 - 12:20 (50 min)
    (6, dt.time(12, 20), dt.time(13, 10)),  # Period 6: 12:20 - 13:10 (50 min)
    (7, dt.time(13, 10), dt.time(14, 0)),   # Period 7: 13:10 - 14:00 (50 min)
    (8, dt.time(14, 0), dt.time(14, 50)),   # Period 8: 14:00 - 14:50 (50 min)
    (9, dt.time(14, 50), dt.time(15, 40)),  # Period 9: 14:50 - 15:40 (50 min)
]

SUMMER_SCHEDULE = [
    (1, dt.time(8, 0), dt.time(9, 48)),     # Assuming 108 min periods
    (2, dt.time(9, 48), dt.time(11, 52)),
    (3, dt.time(11, 52), dt.time(14, 27)),
]


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.smartpass_file.name]
    date_of_interest = form.date_of_interest.data

    smartpass_df = pd.read_csv(filename)
    smartpass_df = process_smartpass_data(smartpass_df)
    f = return_smartpass_report(smartpass_df, date_of_interest)

    download_name = f"SmartPass_{date_of_interest}.xlsx"

    return f, download_name


def process_smartpass_data(smartpass_df):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## rename ID columns
    smartpass_df = smartpass_df.rename(columns={"ID": "StudentID"})
    ## drop no StudentID
    smartpass_df = smartpass_df.dropna(subset=["StudentID"])
    ## drop passes less than 30 seconds
    smartpass_df = smartpass_df[smartpass_df["Duration (sec)"] > 30]
    ## drop passes that originate from cafeteria
    smartpass_df = smartpass_df[smartpass_df["Origin"] != "Cafeteria"]
    ## drop students no longer at HSFI
    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    students_df = utils.return_file_as_df(filename)
    students_df = students_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]
    enrolled_students = students_df["StudentID"].unique().tolist()
    smartpass_df = smartpass_df[smartpass_df["StudentID"].isin(enrolled_students)]
    

    ## keep bathroom passes only
    bathroom_passes_destinations = [
        "9th Floor Girls",
        "7th Floor Girls",
        "6th Floor Girls",
        "5th floor Girls",
        "4th Floor Boys",
        "Gender Neutral",
        "4th Floor Girls",
        "9th Floor Boys",
        "3rd Floor Girls",
        "5th Floor Boys",
        "6th Floor Boys",
    ]
    smartpass_df = smartpass_df[
        smartpass_df["Destination"].isin(bathroom_passes_destinations)
    ]
    ## exceeded 10 minutes
    smartpass_df["OvertimeFlag"] = smartpass_df["Duration (sec)"] > 60 * 10
    ## futz with the date and time to return class period
    smartpass_df["datetime"] = pd.to_datetime(
        smartpass_df["Date"] + " " + smartpass_df["Time"], format="mixed"
    )
    smartpass_df["endtime"] = smartpass_df["datetime"] + pd.to_timedelta(
        smartpass_df["Duration (sec)"], unit="S"
    )
    
    if session['term'] == 7:
        smartpass_df["class_period"] = smartpass_df.apply(
            return_summer_class_period, axis=1
        )
        smartpass_df["FirstTenMinutesFlag"] = smartpass_df.apply(
            lambda row: is_in_first_ten_minutes(row, SUMMER_SCHEDULE), axis=1
        )
    else:
        ## return class period based on the time of the pass
        ## if it is a Monday, then the first period is at 10:20
        ## otherwise, the first period is at 8:55
        smartpass_df["class_period"] = smartpass_df.apply(return_class_period, axis=1)
        smartpass_df["FirstTenMinutesFlag"] = smartpass_df.apply(
            lambda row: is_in_first_ten_minutes(
                row, MONDAY_SCHEDULE if row["datetime"].weekday() == 0 else REGULAR_SCHEDULE
            ), axis=1
        )

    return smartpass_df


def is_in_first_ten_minutes(pass_row, schedule):
    """
    Check if a pass was started in the first 10 minutes of the class period.
    
    Args:
        pass_row: DataFrame row containing 'datetime' and 'class_period'
        schedule: List of tuples (period, start_time, end_time)
    
    Returns:
        bool: True if pass started in first 10 minutes, False otherwise
    """
    pass_time = pass_row["datetime"].time()
    class_period = pass_row["class_period"]
    
    if pd.isna(class_period):
        return False
    
    # Find the start time for this period
    for period, start_time, end_time in schedule:
        if period == class_period:
            # Calculate 10 minutes after period start
            start_datetime = dt.datetime.combine(dt.date.today(), start_time)
            ten_min_mark = (start_datetime + dt.timedelta(minutes=10)).time()
            
            # Check if pass time is between start and 10 minutes after
            return start_time <= pass_time <= ten_min_mark
    
    return False


def return_summer_class_period(pass_row):
    pass_datetime = pass_row["datetime"]
    pass_time = pass_datetime.time()

    for period, start_time, end_time in SUMMER_SCHEDULE:
        if pass_time <= end_time:
            return period
    
    return None


def return_class_period(pass_row):
    pass_datetime = pass_row["datetime"]
    pass_time = pass_datetime.time()
    is_monday = pass_datetime.weekday() == 0
    
    schedule = MONDAY_SCHEDULE if is_monday else REGULAR_SCHEDULE
    
    for period, start_time, end_time in schedule:
        if pass_time <= end_time:
            return period
    
    return None


def return_possible_encounters(smartpass_df):
    list_of_encounters = []
    for (day, period), passes_df in smartpass_df.groupby(["Date", "class_period"]):
        for index, pass_one in passes_df.iterrows():
            for index, pass_two in passes_df.iterrows():
                if pass_one["StudentID"] != pass_two["StudentID"]:
                    datetime_one = pass_one["datetime"]
                    endtime_one = pass_one["endtime"]
                    datetime_two = pass_two["datetime"]
                    endtime_two = pass_two["endtime"]
                    seconds_of_overlap = return_seconds_of_overlap(
                        datetime_one, endtime_one, datetime_two, endtime_two
                    )
                    is_same_destination = (
                        pass_one["Destination"] == pass_two["Destination"]
                    )
                    is_same_origin = pass_one["Origin"] == pass_two["Origin"]
                    overlap_factor = return_overlap_factor(
                        seconds_of_overlap, is_same_destination, is_same_origin
                    )
                    if overlap_factor > 60:
                        student_one = {
                            "Student1_StudentID": pass_one["StudentID"],
                            "Student1_StudentName": pass_one["Student Name"],
                            "Student1_Origin": pass_one["Origin"],
                            "Student1_Destination": pass_one["Destination"],
                            "Student2_StudentID": pass_two["StudentID"],
                            "Student2_StudentName": pass_two["Student Name"],
                            "Student2_Origin": pass_two["Origin"],
                            "Student2_Destination": pass_two["Destination"],
                            "Date": pass_one["Date"],
                            "Period": pass_one["class_period"],
                            "overlap_factor": overlap_factor,
                        }
                        list_of_encounters.append(student_one)
                        student_two = {
                            "Student1_StudentID": pass_two["StudentID"],
                            "Student1_StudentName": pass_two["Student Name"],
                            "Student1_Origin": pass_two["Origin"],
                            "Student1_Destination": pass_two["Destination"],
                            "Student2_StudentID": pass_one["StudentID"],
                            "Student2_StudentName": pass_one["Student Name"],
                            "Student2_Origin": pass_one["Origin"],
                            "Student2_Destination": pass_one["Destination"],
                            "Date": pass_one["Date"],
                            "Period": pass_one["class_period"],
                            "overlap_factor": overlap_factor,
                        }
                        list_of_encounters.append(student_two)

    encounters_df = pd.DataFrame(list_of_encounters)
    cols = [
        "Student1_StudentID",
        "Student1_StudentName",
        "Student2_StudentID",
        "Student2_StudentName",
    ]
    encounters_pvt = pd.pivot_table(
        encounters_df, index=cols, values="overlap_factor", aggfunc="sum"
    )
    encounters_pvt = encounters_pvt.reset_index()

    ## determine avg stdv per Student1

    student_avg_and_std_dev = pd.pivot_table(
        encounters_pvt,
        index="Student1_StudentID",
        values="overlap_factor",
        aggfunc=["mean", "std"],
    ).reset_index()

    student_avg_and_std_dev.columns = [
        "Student1_StudentID",
        "Student1_Avg",
        "Student1_Std",
    ]

    encounters_pvt = encounters_pvt.merge(
        student_avg_and_std_dev, on=["Student1_StudentID"], how="left"
    )

    encounters_pvt[f"Student1_z_score"] = (
        encounters_pvt["overlap_factor"] - encounters_pvt["Student1_Avg"]
    ) / encounters_pvt["Student1_Std"]

    encounters_pvt = encounters_pvt[encounters_pvt["Student1_z_score"] > 0].sort_values(
        by=["Student1_z_score"], ascending=[False]
    )

    return encounters_pvt


def return_overlap_factor(seconds_of_overlap, is_same_destination, is_same_origin):
    factor = seconds_of_overlap
    if is_same_destination:
        factor *= 2
    if is_same_origin:
        factor *= 2
    return factor


def return_seconds_of_overlap(datetime_one, endtime_one, datetime_two, endtime_two):
    datetime_i = min(datetime_one, datetime_two)
    endtime_i = min(endtime_one, endtime_two)

    datetime_j = max(datetime_one, datetime_two)
    endtime_j = max(datetime_one, datetime_two)

    if datetime_j >= endtime_i:
        return 0
    else:
        return (endtime_i - datetime_j).total_seconds()


def return_overtime_pvt_by_student(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        columns="OvertimeFlag",
        values="Grade",
        aggfunc="count",
    ).fillna(0)
    pvt["Total"] = pvt[True] + pvt[False]
    pvt["Overtime%"] = 100 * pvt[True] / pvt["Total"]
    pvt["Overtime%"] = pvt["Overtime%"].apply(lambda x: int(x))
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=[True, "Overtime%"], ascending=[False, False])
    return pvt


def return_total_time_by_students_by_day(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        columns="Date",
        values="Duration (sec)",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    return pvt


def return_number_of_passes_by_students_by_day(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        columns="Date",
        values="Grade",
        aggfunc="count",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    return pvt


def return_number_of_passes_by_student_by_destination(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        columns="Destination",
        values="Grade",
        aggfunc="count",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    return pvt


def return_total_time_per_period_by_student(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        columns="class_period",
        values="Duration (sec)",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    return pvt


def return_overtime_pvt_by_origin(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["Origin"],
        columns="OvertimeFlag",
        values="Grade",
        aggfunc="count",
    ).fillna(0)
    pvt["Total"] = pvt[True] + pvt[False]
    pvt["Overtime%"] = 100 * pvt[True] / pvt["Total"]
    pvt["Overtime%"] = pvt["Overtime%"].apply(lambda x: int(x))
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=[True, "Overtime%"], ascending=[False, False])

    return pvt


def return_total_time_out_of_class_by_student(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["StudentID", "Student Name"],
        values="Duration (sec)",
        aggfunc=["count", "sum"],
    ).fillna(0)
    pvt = pvt.reset_index()
    pvt.columns = ["StudentID", "Student Name", "Total Passes", "Total Time (sec)"]
    pvt["seconds_per_pass"] = pvt["Total Time (sec)"] / pvt["Total Passes"]
    pvt = pvt.sort_values(by=["Total Time (sec)"], ascending=[False])

    return pvt


def return_total_time_out_of_class_by_origin(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["Origin"],
        values="Duration (sec)",
        aggfunc=["count", "sum"],
    ).fillna(0)
    pvt = pvt.reset_index()
    pvt.columns = ["Origin", "Total Passes", "Total Time (sec)"]
    pvt["seconds_per_pass"] = pvt["Total Time (sec)"] / pvt["Total Passes"]
    pvt = pvt.sort_values(by=["Total Time (sec)"], ascending=[False])

    return pvt


def return_total_time_out_of_class_by_origin_by_period(smartpass_df):
    pvt = pd.pivot_table(
        smartpass_df,
        index=["Origin"],
        columns=["class_period"],
        values="Duration (sec)",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()

    pvt = pvt.sort_values(by=["Total"], ascending=[False])

    return pvt


def return_first_ten_minutes_by_student(smartpass_df):
    """
    Report on students who take bathroom passes in the first 10 minutes of class.
    """
    # Filter to only first 10 minutes passes
    first_ten_df = smartpass_df[smartpass_df["FirstTenMinutesFlag"] == True]
    
    pvt = pd.pivot_table(
        first_ten_df,
        index=["StudentID", "Student Name"],
        values="Grade",
        aggfunc="count",
    ).fillna(0)
    pvt = pvt.reset_index()
    pvt.columns = ["StudentID", "Student Name", "First 10 Min Bathroom Passes"]
    
    pvt = pvt.sort_values(by=["First 10 Min Bathroom Passes"], ascending=[False])
    
    return pvt


def return_first_ten_minutes_by_origin_by_period(smartpass_df):
    """
    Report on which classrooms (Origins) have the most bathroom passes 
    in the first 10 minutes, broken down by period.
    """
    # Filter to only first 10 minutes passes
    first_ten_df = smartpass_df[smartpass_df["FirstTenMinutesFlag"] == True]
    
    pvt = pd.pivot_table(
        first_ten_df,
        index=["Origin"],
        columns=["class_period"],
        values="Grade",
        aggfunc="count",
        margins=True,
        margins_name="Total",
    ).fillna(0)
    pvt = pvt.reset_index()
    
    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    
    return pvt


def return_smartpass_report(smartpass_df, date_of_interest):

    sheets = [
        ("overtime_by_student", return_overtime_pvt_by_student(smartpass_df)),
        (
            "total_time_by_student",
            return_total_time_out_of_class_by_student(smartpass_df),
        ),
        (
            "total_time_by_period_by_student",
            return_total_time_per_period_by_student(smartpass_df),
        ),
        (
            "total_passes_per_day_by_student",
            return_number_of_passes_by_students_by_day(smartpass_df),
        ),
        (
            "total_time_per_day_by_student",
            return_total_time_by_students_by_day(smartpass_df),
        ),
        ("overtime_by_origin", return_overtime_pvt_by_origin(smartpass_df)),
        (
            "total_time_by_origin",
            return_total_time_out_of_class_by_origin(smartpass_df),
        ),
        (
            "total_time_by_origin_by_period",
            return_total_time_out_of_class_by_origin_by_period(smartpass_df),
        ),
        ("possible_encounters_pvt", return_possible_encounters(smartpass_df)),
        (
            "total_passes_by_dest_by_student",
            return_number_of_passes_by_student_by_destination(smartpass_df),
        ),
        (
            "first_10min_by_student",
            return_first_ten_minutes_by_student(smartpass_df),
        ),
        (
            "first_10min_by_origin_by_period",
            return_first_ten_minutes_by_origin_by_period(smartpass_df),
        ),
    ]

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    f.seek(0)

    return f