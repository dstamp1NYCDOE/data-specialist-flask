import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"    
    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    ## student pvt by day and period
    student_pvt_tbl = pd.pivot_table( 
        attendance_marks_df, 
        index=['StudentID'], columns=['Date','Pd'],
        values='Type', aggfunc=return_value_agg_func
    ).fillna(0)

    # student_pvt_tbl = student_pvt_tbl.head(10)

    student_pvt_tbl['top_correl'] = student_pvt_tbl.apply(return_top_correlation, args=(student_pvt_tbl,), axis=1)
    student_pvt_tbl = student_pvt_tbl.reset_index()
    student_pvt_tbl = student_pvt_tbl.droplevel('Pd', axis=1)
    student_pvt_tbl = student_pvt_tbl[['StudentID','top_correl']]


    student_pvt_tbl = student_pvt_tbl.merge(
        students_df, on=['StudentID'], how='left'
    )
    student_pvt_tbl = student_pvt_tbl.merge(
        students_df, left_on=['top_correl'], right_on=['StudentID'], how='left',
    )

    return student_pvt_tbl

def return_top_correlation(student_row,all_students_df):
    df = all_students_df.copy()
    df['correl'] = df.apply(lambda x: x.corr(student_row),axis=1)
    df = df.dropna(subset='correl')
    return df[['correl']].sort_values(by=['correl']).index[-2]
    

def return_value_agg_func(x):
    
    if 'presemt' in x.to_list():
        return 1
    if 'tardy' in x.to_list():
        return 0.5
    else:
        return 0