import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report(files_df, "jupiter_period_attendance")
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


    

    attd_by_student_by_day = pd.pivot_table(attendance_marks_df,index=['StudentID','Date'], columns='Type',values='Pd',aggfunc='count').fillna(0)
    

    attd_by_student_by_day['in_school?'] = (attd_by_student_by_day['present'] + attd_by_student_by_day['tardy']) >= 2
    attd_by_student_by_day = attd_by_student_by_day.reset_index()[['StudentID','Date','in_school?']]

    attendance_marks_df = attendance_marks_df.merge(attd_by_student_by_day, on=['StudentID','Date'],how='left')

    first_period_present_by_student_by_day = pd.pivot_table(
        attendance_marks_df[attendance_marks_df['in_school?']],
        index=['StudentID','Date'],
        columns='Type',
        values='Pd', 
        aggfunc='min'
    ).reset_index()
    

    first_period_present_by_student_by_day['first_period_present'] = first_period_present_by_student_by_day[['present','tardy']].min(axis=1)

    first_period_present_by_student_by_day = first_period_present_by_student_by_day[['StudentID','Date','first_period_present']]

    attendance_marks_df = attendance_marks_df.merge(first_period_present_by_student_by_day, on=['StudentID','Date'],how='left')
    
    attendance_marks_df['potential_cut'] = attendance_marks_df.apply(determine_potential_cut,axis=1)
    
    print(attendance_marks_df)

    for period,cuts_df in attendance_marks_df[attendance_marks_df['potential_cut']].groupby('Pd'):
        cuts_pvt = pd.pivot_table(cuts_df,index=['StudentID'],columns='Pd',aggfunc='count',values='Section')
        cuts_pvt = cuts_pvt.sort_values(by=period)
        cuts_pvt = cuts_pvt.tail(10)
        print(cuts_pvt)



def determine_potential_cut(student_row):
    is_in_school = student_row['in_school?']
    
    if is_in_school == False:
        return False
    
    attendance_type = student_row['Type']
    if attendance_type in ['present','excused','tardy']:
        return False 
    
    return True
    
    period = student_row['Pd']
    first_period_present = student_row['first_period_present']
    if attendance_type == 'unexcused' and period >= first_period_present:
        return True 
    
    return False