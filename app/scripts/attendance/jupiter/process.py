import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import files_df

import re

period_regex = re.compile(r'\d+')




def main(week_number=None, day_of=None):
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"  

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]
    cr_1_49_filename = utils.return_most_recent_report_by_semester(files_df, "1_49", year_and_semester=year_and_semester)
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)

    students_df = students_df.merge(cr_1_49_df[['StudentID','Counselor']], on=['StudentID'], how='left').fillna('')


    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    
    jupiter_attd_df = utils.return_file_as_df(jupiter_attd_filename)

    jupiter_attd_df['week_number'] = pd.to_datetime(jupiter_attd_df['Date'])
    jupiter_attd_df['week_number'] = jupiter_attd_df['week_number'].dt.isocalendar().week

    if week_number:
        jupiter_attd_df = jupiter_attd_df[jupiter_attd_df['week_number']==int(week_number)]

    if day_of:
        jupiter_attd_df = jupiter_attd_df[jupiter_attd_df['Date']==day_of]

    ## only keep students still on register
    jupiter_attd_df = jupiter_attd_df[jupiter_attd_df['StudentID'].isin(students_df['StudentID'])]

    jupiter_attd_df['Pd'] = jupiter_attd_df['Period'].apply(period_to_pd)
    
    

    jupiter_attd_df = jupiter_attd_df.sort_values(
        by=['StudentID', 'Date', 'Pd'])

    attd_by_date_by_student = pd.pivot_table(
        jupiter_attd_df,
        values='Period',
        index=['StudentID', 'Date'],
        columns=['Type'],
        aggfunc='count',
    ).fillna(0)

    

    attd_by_date_by_student['in_school?'] = attd_by_date_by_student.apply(
        in_school, axis=1)
    attd_by_date_by_student['num_of_periods_in_class'] = attd_by_date_by_student.apply(
        return_number_of_periods_present, axis=1)
    attd_by_date_by_student['only_present_one_period'] = attd_by_date_by_student.apply(
        return_only_present_one_period, axis=1)
    # Merge in overall school absent/present
    jupiter_attd_df = jupiter_attd_df.merge(attd_by_date_by_student.reset_index(
    )[['StudentID', 'Date', 'in_school?', 'num_of_periods_in_class', 'only_present_one_period']], on=['StudentID', 'Date'], how='left')

    # determine_first_period_present
    df = jupiter_attd_df[jupiter_attd_df['in_school?']]
    df = jupiter_attd_df[~jupiter_attd_df['Type'].isin(['absent', 'excused'])]
    df = df.drop_duplicates(subset=['StudentID', 'Date'])
    df['first_period_present'] = df['Pd']
    df['first_period_attd_type'] = df['Type']
    df = df[['StudentID', 'Date', 'first_period_present', 'first_period_attd_type']]

    # merge in first_period_present
    jupiter_attd_df = jupiter_attd_df.merge(
        df, on=['StudentID', 'Date'], how='left').fillna(-1)

    df = jupiter_attd_df.drop_duplicates(subset=['StudentID', 'Date'])
    df['num_of_periods_late'] = df.apply(num_of_periods_late, axis=1)

    jupiter_attd_df = jupiter_attd_df.merge(
        df[['StudentID', 'Date', 'num_of_periods_late']], on=['StudentID', 'Date'], how='left').fillna(-1)

    # determine if cutting
    jupiter_attd_df['cutting?'] = jupiter_attd_df.apply(is_cutting, axis=1)

    number_of_cuts_df = pd.pivot_table(
        jupiter_attd_df[['StudentID','cutting?','Period']],
        values='Period',
        index=['StudentID'],
        columns=['cutting?'],
        aggfunc='count',
    ).fillna(0).reset_index()[['StudentID',True]]
    number_of_cuts_df.columns = ['StudentID','num_of_cuts']

    # number of days absent
    number_of_days_absent_df = pd.pivot_table(
        jupiter_attd_df[['StudentID', 'in_school?', 'Date']],
        values='Date',
        index=['StudentID'],
        columns=['in_school?'],
        aggfunc='nunique',
    ).fillna(0).reset_index()[['StudentID', False]]
    number_of_days_absent_df.columns = ['StudentID', 'num_of_days_absent']

    ## Late to school
    jupiter_attd_df['late_to_school?'] = jupiter_attd_df.apply(
        is_late_to_school, axis=1)
    number_of_lates_to_school_df = pd.pivot_table(
        jupiter_attd_df[['StudentID', 'late_to_school?', 'Date']],
        values='Date',
        index=['StudentID'],
        columns=['late_to_school?'],
        aggfunc='nunique',
    ).fillna(0).reset_index()[['StudentID', True]]
    number_of_lates_to_school_df.columns = ['StudentID', 'num_of_late_to_school']

    jupiter_attd_df = jupiter_attd_df.merge(
        number_of_cuts_df, on=['StudentID'], how='left').fillna(0)
    jupiter_attd_df = jupiter_attd_df.merge(
        number_of_lates_to_school_df, on=['StudentID'], how='left').fillna(0)
    jupiter_attd_df = jupiter_attd_df.merge(
        number_of_days_absent_df, on=['StudentID'], how='left').fillna(0)

    jupiter_attd_df['attd_error'] = jupiter_attd_df.apply(detect_attd_error, axis=1)
    

    jupiter_attd_df = jupiter_attd_df.merge(
        students_df, on=['StudentID'], how='left')
    

    return jupiter_attd_df


def detect_attd_error(student_row):
    only_present_one_period = student_row['only_present_one_period']
    attd_type = student_row['Type']
    return only_present_one_period and (attd_type in ['present', 'late'])

def num_of_periods_late(row):
    pd = row['Pd']
    first_period_attd_type = row['first_period_attd_type']
    first_period_present = row['first_period_present']

    if first_period_present == -1:
        return -1

    elif first_period_attd_type == 'tardy':
        return first_period_present - pd + 0.5

    return first_period_present - pd


def is_late_to_school(row):
    num_of_periods_late = row['num_of_periods_late']
    in_school = row['in_school?']
    if in_school:
        return num_of_periods_late > 0
    else:
        return False


def is_cutting(student_row):
    attendance_mark = student_row['Attendance']
    if attendance_mark == 'C':
        return True
    
    first_period_present = student_row['first_period_present']
    class_period = student_row['Pd']
    in_school = student_row['in_school?']
    Type = student_row['Type']

    return ((Type in ['unexcused']) and (class_period >= first_period_present) and in_school)



def return_number_of_periods_present(row):
    excused = row['excused']
    present = row['present']
    tardy = row['tardy']
    unexcused = row['unexcused']
    return present + tardy


def return_only_present_one_period(row):
    num_of_periods_present = row['num_of_periods_in_class']
    return num_of_periods_present == 1

def in_school(row):
    excused = row['excused']
    present = row['present']
    tardy = row['tardy']
    unexcused = row['unexcused']
    
    if present + tardy >= 2:
        return True
    else:
        return False


def period_to_pd(Period):
    mo = period_regex.search(Period)
    return int(mo.group())
