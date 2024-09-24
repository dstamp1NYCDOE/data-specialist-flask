import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.date_to_marking_period import return_mp_from_date

def main():
    school_year = session["school_year"]

    term = session["term"]

    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"
    
    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance",year_and_semester=year_and_semester)
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    print(attendance_marks_df)
    ## convert date and insert marking period
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(return_mp_from_date, args=(school_year,))
    ## keep current semester
    attendance_marks_df = attendance_marks_df[attendance_marks_df["Term"].str[1]==str(term)]
    ## aggregate attendace by teacher, date, Course, Section
    print(attendance_marks_df)
    df = pd.pivot_table( 
        attendance_marks_df[attendance_marks_df['Type']=='present'],
        index=['Teacher','Course','Section'],
        columns=['Date'],
        values='StudentID',aggfunc='count'
    ).fillna(0)
    df = df.apply(lambda x: x>0)

    df['days_with_attendance'] = df.sum(axis=1)

    return df.reset_index()