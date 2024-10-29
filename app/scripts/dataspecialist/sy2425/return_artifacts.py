import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    attendance_flowables = return_attendance_flowables(year_and_semester)
    assignments_flowables = return_assignments_flowables(year_and_semester)
    combined_flowables = return_attendance_and_assignments_flowables(year_and_semester)

    flowables = combined_flowables



    download_name = "2024-2025_DataSpecialistProject_Artifacts.pdf"
    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=1 * inch,
        leftMargin=1.5 * inch,
        rightMargin=1.5 * inch,
        bottomMargin=1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f, download_name 


def return_attendance_flowables(year_and_semester):
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )

    ## keep period 1&2 only
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Pd'].isin([1,2])]        
    ## Drop z codes
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course'].str[0]!='Z']  

    attendance_by_teacher_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["Teacher",'Course','Pd','Section'],
        columns="Type",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)

    attendance_by_teacher_pvt['tardy_%'] =100* attendance_by_teacher_pvt['tardy'] / (attendance_by_teacher_pvt['tardy'] + attendance_by_teacher_pvt['present'] )
    attendance_by_teacher_pvt['tardy_%'] = attendance_by_teacher_pvt['tardy_%'].astype(int)



    attendance_by_teacher_pvt = attendance_by_teacher_pvt.reset_index()
    attendance_by_teacher_pvt = attendance_by_teacher_pvt.sort_values(by=['Pd','tardy_%'])

    attendance_by_teacher_pvt_T = utils.return_df_as_table(attendance_by_teacher_pvt)

    return [attendance_by_teacher_pvt_T]


def return_assignments_flowables(year_and_semester):
    filename = utils.return_most_recent_report_by_semester(files_df, "assignments", year_and_semester=year_and_semester)
    
    student_assignments_df = utils.return_file_as_df(filename)
    
    ## drop duplicates
    subset = ['Teacher','Course','Section','Assignment','Objective','Category','CategoryWeight','DueDate']
    assignments_df = student_assignments_df.drop_duplicates(subset=subset)
    ## keep "performance" + "practice"
    assignments_df = assignments_df[assignments_df['Category'].isin(['Practice','Performance'])]

    assignments_pvt = pd.pivot_table(
        assignments_df, index=['Teacher','Course','Section'], columns='Category',values='WorthPoints', aggfunc=['count','sum'],
    ).fillna(0)
    assignments_pvt = assignments_pvt.reset_index()
    assignments_pvt.columns = ['Teacher','Course','Section','#_Performance','#_Practice','PerformancePts','PracticePts']
    

    assignments_pvt_T = utils.return_df_as_table(assignments_pvt)

    return [assignments_pvt_T]


def return_attendance_and_assignments_flowables(year_and_semester):
    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    students_df = utils.return_file_as_df(filename)
    students_df = students_df[['StudentID','LastName','FirstName']]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )      
    ## Drop z + G codes
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course'].str[0]!='Z']
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course'].str[0]!='G']  
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course'].str[0]!='R']
    courses_to_drop = [
        'MQS21','MQS22','EQS11QQI',
    ]  
    attendance_marks_df = attendance_marks_df[~attendance_marks_df['Course'].isin(courses_to_drop)]
    ## keep marks during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attendance_by_teacher_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["Teacher",'Course','Pd','Section'],
        columns="Type",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)

    attendance_by_teacher_pvt['tardy_%'] =100* attendance_by_teacher_pvt['tardy'] / (attendance_by_teacher_pvt['tardy'] + attendance_by_teacher_pvt['present'] )
    attendance_by_teacher_pvt['tardy_%'] = attendance_by_teacher_pvt['tardy_%'].fillna(0)
    attendance_by_teacher_pvt['tardy_%'] = attendance_by_teacher_pvt['tardy_%'].astype(int)

    attendance_by_teacher_pvt['absent_%'] =100* (attendance_by_teacher_pvt['unexcused'] + attendance_by_teacher_pvt['excused']) / (attendance_by_teacher_pvt['unexcused'] + attendance_by_teacher_pvt['excused'] + attendance_by_teacher_pvt['tardy'] + attendance_by_teacher_pvt['present'] )
    attendance_by_teacher_pvt['absent_%'] = attendance_by_teacher_pvt['absent_%'].fillna(0)
    attendance_by_teacher_pvt['absent_%'] = attendance_by_teacher_pvt['absent_%'].astype(int)    

    attendance_by_teacher_pvt = attendance_by_teacher_pvt.reset_index()
    attendance_by_teacher_pvt = attendance_by_teacher_pvt[['Teacher','Course','Section','Pd','tardy_%','absent_%']]

    filename = utils.return_most_recent_report_by_semester(files_df, "assignments", year_and_semester=year_and_semester)
    
    student_assignments_df = utils.return_file_as_df(filename)
    
    ## drop duplicates
    subset = ['Teacher','Course','Section','Assignment','Objective','Category','CategoryWeight','DueDate']
    assignments_df = student_assignments_df.drop_duplicates(subset=subset)
    ## keep "performance" + "practice"
    assignments_df = assignments_df[assignments_df['Category'].isin(['Practice','Performance'])]

    assignments_pvt = pd.pivot_table(
        assignments_df, index=['Teacher','Course','Section'], columns='Category',values='WorthPoints', aggfunc=['count','sum'],
    ).fillna(0)
    assignments_pvt = assignments_pvt.reset_index()
    assignments_pvt.columns = ['Teacher','Course','Section','#_Performance','#_Practice','PerformancePts','PracticePts']


    df = attendance_by_teacher_pvt.merge(assignments_pvt.drop(columns=['Teacher']), on=['Course','Section'], how='left')  

    df = df.sort_values(by=['#_Practice']) 

    pvt_T = utils.return_df_as_table(df)


    ## Student Specific

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    
    grades_df = utils.return_file_as_df(jupiter_attd_filename)
    grades_df = grades_df[grades_df['Term'].isin(['S1','S2'])]
    grades_df = grades_df[['StudentID','Course','Section','Teacher1','Pct']]
    

    student_assignments_pvt = pd.pivot_table(
        student_assignments_df, index=['StudentID','Course','Section'], columns=['Category','Missing'],values='WorthPoints', aggfunc=['count'],
    ).fillna(0)
    print(student_assignments_pvt)
    student_assignments_pvt = student_assignments_pvt.reset_index()
    student_assignments_pvt.columns = ['StudentID','Course','Section','#_Performance_Submitted','#_Performance_Missing','#_Practice_Submitted','#_Practice_Missing']

    grades_df = grades_df.merge(student_assignments_pvt, on=['StudentID','Course','Section'])

    attendance_by_student_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID",'Course','Pd','Section'],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)

    attendance_by_student_pvt['tardy_%'] =100* attendance_by_student_pvt['tardy'] / (attendance_by_student_pvt['tardy'] + attendance_by_student_pvt['present'] )
    attendance_by_student_pvt['tardy_%'] = attendance_by_student_pvt['tardy_%'].fillna(0)
    attendance_by_student_pvt['tardy_%'] = attendance_by_student_pvt['tardy_%'].astype(int)

    attendance_by_student_pvt['absent_%'] =100* (attendance_by_student_pvt['unexcused'] + attendance_by_student_pvt['excused']) / (attendance_by_student_pvt['unexcused'] + attendance_by_student_pvt['excused'] + attendance_by_student_pvt['tardy'] + attendance_by_student_pvt['present'] )
    attendance_by_student_pvt['absent_%'] = attendance_by_student_pvt['absent_%'].fillna(0)
    attendance_by_student_pvt['absent_%'] = attendance_by_student_pvt['absent_%'].astype(int)    

    attendance_by_student_pvt = attendance_by_student_pvt.reset_index()
    attendance_by_student_pvt = attendance_by_student_pvt[['StudentID','Course','Section','Pd','tardy_%','absent_%']]

    combined_df = grades_df.merge(attendance_by_student_pvt, on=['StudentID','Course','Section'])
    combined_df = combined_df.merge(students_df, on=['StudentID'], how='left')

    
    ## failing class and missing no assignments
    mask = (combined_df['#_Performance_Missing'] == 0) & (combined_df['#_Practice_Missing'] == 0) & (combined_df['Pct'] < 65)

    failing_class_and_no_missing_assignments_df = combined_df[mask]
    print(failing_class_and_no_missing_assignments_df)


    failing_class_and_no_missing_assignments_teacher_pvt = pd.pivot_table(failing_class_and_no_missing_assignments_df, index=['Teacher1','Course','Section'], values='StudentID', aggfunc='count')
    print(failing_class_and_no_missing_assignments_teacher_pvt)
    return [pvt_T]


      