from flask import session

import pandas as pd 
from sklearn.linear_model import LinearRegression

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"   

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session['school_year']
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(utils.return_year_in_hs, args=(school_year,))

    students_df = cr_3_07_df[['StudentID','LastName','FirstName','year_in_hs']]

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    grades_df = utils.return_file_as_df(filename)

    ## keep S1 and S2
    grades_df = grades_df[grades_df['Term'].isin(['S1','S2'])]
    grades_df['Curriculum'] = grades_df['Course'].apply(return_curriculum)

    grades_df['passing?'] = grades_df['Pct'] >= 65

    ## senior_courses_to_graduate

    grades_df = grades_df.merge(students_df, on='StudentID',how='left')
    
    return grades_df

def return_curriculum(Course):
    if Course[0] == 'F':
        return 'LOTE'
    
    if Course[0] == 'E':
        return Course[0:5]
    
    if Course[0:2] == 'PP':
        return 'PE'
    
    if Course[0:2] == 'PH':
        return 'Health'

    if Course[0:2] == 'HV':
        return 'Government'
    if Course[0:2] == 'HE':
        return 'Econ'
    if Course[0:2] == 'HF':
        return 'AP Govt'           