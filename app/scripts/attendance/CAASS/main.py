import pandas as pd
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
import datetime as dt 

from app.scripts.attendance.jupiter.process import main as process_jupiter

def process_CAASS():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "CAASS_Swipe_Data", year_and_semester=year_and_semester
    )
    caass_df = utils.return_file_as_df(filename)

    # fix StudentID columns
    caass_df = caass_df.rename(columns={"Student ID": "StudentID"})
    # convert entry date and time to datetime
    caass_df["Entry Datetime"] = pd.to_datetime(
        caass_df["Entry Date"] + " " + caass_df["Entry Time"]
    )
    # convert entry date to datetime
    caass_df["Date"] = pd.to_datetime(caass_df["Entry Date"])
    ## drop system absences
    SYSTEM_MARKED_ABSENCE_STR = "System Marked Absent"
    # caass_df = caass_df[caass_df["Entry Type"] != SYSTEM_MARKED_ABSENCE_STR]
    print(caass_df)

    ## pull in RATR
    filename = utils.return_most_recent_report_by_semester(
        files_df, "RATR", year_and_semester=year_and_semester
    )
    RATR_df = utils.return_file_as_df(filename)
    RATR_df["StudentID"] = RATR_df["STUDENT ID"].str.extract("(\d{9})")
    RATR_df["StudentID"] = RATR_df["StudentID"].astype(int)
    RATR_df["Date"] = RATR_df["SCHOOL DAY"].str.extract("(\d{2}/\d{2}/\d{2})")
    RATR_df["Date"] = pd.to_datetime(RATR_df["Date"])
    RATR_df["Weekday"] = RATR_df["Date"].dt.weekday
    columns = ["StudentID", "Date", "Weekday", "ATTD"]
    RATR_df = RATR_df[columns]

    ## merge RATR_df with CAASS
    df = RATR_df.merge(caass_df, on=["StudentID", "Date"], how="left").dropna()
    
    ## import processed jupiter
    jupiter_df = process_jupiter() 
    jupiter_df["Date"] = pd.to_datetime(jupiter_df["Date"])

    ## merge RATR_df with CAASS
    df = jupiter_df.merge(df, on=["StudentID", "Date"], how="left").dropna()
    
    df['period_start_time'] = df.apply(return_class_start_time, axis=1)
    df['period_end_time'] = df.apply(return_class_end_time, axis=1)
    df['arrived_before_class_started_flag'] = df.apply(arrived_before_class_started_flag, axis=1)
    df['arrived_before_class_ended_flag'] = df.apply(arrived_before_class_ended_flag, axis=1)
    

    ## arrived before class ended up was absent from class

   
    f = BytesIO()

    writer = pd.ExcelWriter(f)

    sheet_name = 'processed'
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    f.seek(0)



    download_name = 'processed_caass.xlsx'
    return f, download_name


def arrived_before_class_started_flag(row):
    period_start_time = row['period_start_time']
    scan_datetime = row['Entry Datetime']
    scan_time = scan_datetime.time()
    return scan_time < period_start_time

def arrived_before_class_ended_flag(row):
    period_start_time = row['period_end_time']
    scan_datetime = row['Entry Datetime']
    scan_time = scan_datetime.time()
    return scan_time < period_start_time

def return_class_start_time(row):
    weekday = row['Weekday']
    period = row['Pd']

    if weekday == 0:
        period_end_time_dict = {
            1:dt.time(9, 45),
            2:dt.time(10, 25),
            3:dt.time(11, 5),
            4:dt.time(11, 45),
            5:dt.time(12, 25),
            6:dt.time(13, 5),
            7:dt.time(13, 45),
            8:dt.time(14, 25),
            9:dt.time(15, 5),
        }
    else:
        period_end_time_dict = {
            1:dt.time(8, 10),
            2:dt.time(9, 00),
            3:dt.time(9, 50),
            4:dt.time(10, 45),
            5:dt.time(11, 35),
            6:dt.time(12, 20),
            7:dt.time(13, 15),
            8:dt.time(14, 5),
            9:dt.time(14, 55),
        }
    
    return period_end_time_dict.get(period)


def return_class_end_time(row):
    weekday = row['Weekday']
    period = row['Pd']

    if weekday == 0:
        period_end_time_dict = {
            1:dt.time(10, 20),
            2:dt.time(11, 00),
            3:dt.time(11, 40),
            4:dt.time(12, 20),
            5:dt.time(13, 00),
            6:dt.time(13, 40),
            7:dt.time(14, 20),
            8:dt.time(15, 00),
            9:dt.time(15, 40),
        }
    else:
        period_end_time_dict = {
            1:dt.time(8, 55),
            2:dt.time(9, 45),
            3:dt.time(10, 40),
            4:dt.time(11, 30),
            5:dt.time(12, 20),
            6:dt.time(13, 10),
            7:dt.time(14, 00),
            8:dt.time(15, 50),
            9:dt.time(15, 40),
        }
    
    return period_end_time_dict.get(period)
