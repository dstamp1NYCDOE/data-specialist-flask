from io import BytesIO
import pandas as pd
import datetime as dt
from flask import session, current_app
import os

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Dept"] = attendance_marks_df["Course"].str[0]

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)
    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep periods 1-9
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "CAASS_Swipe_Data", year_and_semester=year_and_semester
    )
    entrance_swipes_df = utils.return_file_as_df(filename)
    entrance_swipes_df = entrance_swipes_df.rename(
        columns={"Student ID": "StudentID", "Entry Date": "Date"}
    )
    entrance_swipes_df["Date"] = pd.to_datetime(entrance_swipes_df["Date"])

    entrance_swipes_df = entrance_swipes_df[
        ["StudentID", "Date", "Entry Time", "Attendance Status", "Entry Type"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        entrance_swipes_df, on=["StudentID", "Date"], how="left"
    )
    attendance_marks_df["DayOfWeek"] = attendance_marks_df["Date"].dt.day_name()

    path = os.path.join(current_app.root_path, f"data/SchoolCalendar.xlsx")
    bell_schedule_df = pd.read_excel(path, sheet_name=f"BellSchedule")
    attendance_marks_df = attendance_marks_df.merge(
        bell_schedule_df, on=["Pd", "DayOfWeek"], how="left"
    )

    for time_col in ["Entry Time", "PeriodStartTime", "PeriodEndTime"]:
        attendance_marks_df[time_col] = pd.to_datetime(attendance_marks_df[time_col])

    attendance_marks_df["swiped_into_building_flag"] = attendance_marks_df.apply(
        return_if_swiped_into_building, axis=1
    )

    attendance_marks_df["swiped_into_building_on_time_flag"] = (
        attendance_marks_df.apply(return_if_swiped_into_building_on_time, axis=1)
    )

    attendance_marks_df = attendance_marks_df.dropna()

    attendance_marks_df["missed_late_flag"] = attendance_marks_df.apply(
        return_if_missed_late, axis=1
    )

    missed_lates_by_course_pvt = (
        pd.pivot_table(
            attendance_marks_df,
            index=["Teacher", "Course", "Section", "Pd"],
            columns="missed_late_flag",
            values="StudentID",
            aggfunc="count",
        )
        .reset_index()
        .fillna(0)
    )
    missed_lates_by_course_pvt["%"] = missed_lates_by_course_pvt[True] / (
        missed_lates_by_course_pvt[True] + missed_lates_by_course_pvt[False]
    )

    missed_lates_by_dept_pvt = (
        pd.pivot_table(
            attendance_marks_df,
            index=["Dept", "Pd"],
            columns="missed_late_flag",
            values="StudentID",
            aggfunc="count",
        )
        .reset_index()
        .fillna(0)
    )
    missed_lates_by_dept_pvt["%"] = missed_lates_by_dept_pvt[True] / (
        missed_lates_by_dept_pvt[True] + missed_lates_by_dept_pvt[False]
    )

    missed_lates_by_student_pvt = (
        pd.pivot_table(
            attendance_marks_df,
            index=["StudentID"],
            columns="missed_late_flag",
            values="Date",
            aggfunc="count",
        )
        .reset_index()
        .fillna(0)
    )

    missed_lates_by_student_pvt = students_df.merge(
        missed_lates_by_student_pvt, on=["StudentID"]
    )
    missed_lates_by_student_pvt = missed_lates_by_student_pvt[
        missed_lates_by_student_pvt[True] > 0
    ]

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    attendance_marks_df.to_excel(writer)
    missed_lates_by_course_pvt.to_excel(writer, sheet_name="missed_lates_by_course")
    missed_lates_by_dept_pvt.to_excel(writer, sheet_name="missed_lates_by_dept")
    missed_lates_by_student_pvt.to_excel(writer, sheet_name="missed_late_by_student")

    writer.close()

    f.seek(0)

    return f, "analysis.xlsx"


def return_if_missed_late(row):
    swiped_into_building_on_time_flag = row["swiped_into_building_on_time_flag"]
    swiped_into_building_flag = row["swiped_into_building_flag"]
    attendance_type = row["Type"]

    return (
        not swiped_into_building_on_time_flag
        and swiped_into_building_flag
        and (attendance_type == "present")
    )


def return_if_swiped_into_building(row):
    attendance_status = row["Attendance Status"]

    if attendance_status == "Absent":
        return False
    swipe_time = row["Entry Time"]
    period_start_time = row["PeriodStartTime"]
    period_end_time = row["PeriodEndTime"]
    if swipe_time < period_end_time:
        return True
    else:
        return False


def return_if_swiped_into_building_on_time(row):
    attendance_status = row["Attendance Status"]

    if attendance_status == "Absent":
        return False
    swipe_time = row["Entry Time"]
    period_start_time = row["PeriodStartTime"]
    period_end_time = row["PeriodEndTime"]
    if swipe_time <= period_start_time:
        return True
    else:
        return False
