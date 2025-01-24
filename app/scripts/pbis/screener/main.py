import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.file.name]

    dfs_dict = pd.read_excel(filename, sheet_name=None)
    df = process_screener_data(dfs_dict)

    f = return_download_file(df)

    download_name = f"UniveralScreenerAnalysis.xlsx"

    return f, download_name


def return_screener_questions(columns):
    return [x for x in columns if "?" in x]


def process_screener_data(dfs_dict):
    non_surveys = ['Students','Families']
    surveys_list = [df for (sheet, df) in dfs_dict.items() if not sheet in non_surveys]

    student_responses_df = dfs_dict['Students']
    student_responses_df = student_responses_df.drop(columns=['LastName','FirstName'])
    
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_49_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester=year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor"]]

    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    cr_3_07_df = cr_3_07_df[["StudentID", "GEC","IEPFlag"]]

    

    
    cr_1_01_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(cr_1_01_filename)
    lunch_df = cr_1_01_df[cr_1_01_df['Course'].isin(['ZL','ZL4','ZL5','ZL6','ZL7'])]
    lunch_df['LunchPeriod'] = lunch_df['Period']
    lunch_df = lunch_df[['StudentID','LunchPeriod']]


    df = pd.concat(surveys_list)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    df = df.merge(cr_1_49_df, on="StudentID", how="left")
    df = df.merge(cr_3_07_df, on="StudentID", how="left")
    df = df.merge(lunch_df, on="StudentID", how="left")
    

    screener_questions = return_screener_questions(df.columns)
    student_pvt = return_student_pivot(df, screener_questions)
    
    student_by_teacher_pvt = return_student_by_teacher_pvt(df, screener_questions)

    dff = df.merge(student_pvt, on=['StudentID','LastName','FirstName'], how='left')
    dff = dff.merge(student_by_teacher_pvt, on=['StudentID','LastName','FirstName','Teacher1'], how='left')
    dff = dff.merge(student_responses_df, on=['StudentID'], how='left')

    
    return dff


def return_sheets_by_cohort(dff, screener_questions):
    sheets = []

    cols = ['StudentID', 'LastName', 'FirstName',
       'Counselor', 'GEC',"IEPFlag","LunchPeriod", 'Total Above Average', 'Total Average',
       'Total Below Average', 'Total Net', 'I feel like I belong at HSFI',
       'I feel like my HSFI classmates care about me',
       'I feel comfortable interacting with other students in my classes',
       'I have friends at HSFI I feel a connection with and can go to if I have concerns',
       'I need help from the school with making friends at HSFI',
       'I have an adult at HSFI I feel a connection with and can go to if I have concerns',
       'I need help from the school with getting to HSFI on time every day.',
       'I need help from the school with learning how to control my emotions',
       'I need help from the school with learning how to improve my work habits to reach my academic potential',
       'Which of the following clubs have you participated in this year',
       'Who is an adult at HSFI you feel connected to and can go to if you have questions/concerns?']
    dff = dff[cols]
    dff = dff.sort_values(by=['Total Net'])
    students_df = dff.drop_duplicates(subset='StudentID')

    for cohort, cohort_students_df in students_df.groupby('GEC'):
        sheets.append((f'{cohort}', cohort_students_df))

    return sheets
        



def return_student_by_teacher_pvt(df, screener_questions):
    id_vars = [x for x in df.columns if x not in screener_questions]
    dff = df.melt(id_vars=id_vars, var_name="Question", value_name="TeacherResponse")

    pvt_lst = []
    for _ in ['Above Average', 'Below Average']:
        pvt = pd.pivot_table(dff[dff['TeacherResponse']==_],index="StudentID", columns='Question', values='Teacher1', aggfunc=lambda x: '\n'.join(x)).fillna('')
        pvt.columns = [f"{x} - {_}" for x in pvt.columns]
        # pvt = pvt.reset_index()
        pvt_lst.append(pvt)

    teachers_pvt = pd.concat(pvt_lst, axis=1).fillna('')
    


    student_pvt = pd.pivot_table(
        dff,
        index=["StudentID", "LastName", "FirstName","Teacher1"],
        columns="TeacherResponse",
        values="Counselor",
        aggfunc="count",
    ).fillna(0)
    student_pvt['total'] = student_pvt.sum(axis=1)
    student_pvt['overall_net'] = (student_pvt['Above Average'] - student_pvt['Below Average']) / student_pvt['total']
    
    student_pvt.columns = ['Teacher Above Average', 'Teacher Average', 'Teacher Below Average', 'total', 'Teacher Net']
    student_pvt = student_pvt[['Teacher Above Average', 'Teacher Average', 'Teacher Below Average', 'Teacher Net']].reset_index()

    student_pvt = student_pvt.merge(teachers_pvt, on=['StudentID'], how='left').fillna('')

    return student_pvt


def return_student_pivot(df, screener_questions):
    id_vars = [x for x in df.columns if x not in screener_questions]
    dff = df.melt(id_vars=id_vars, var_name="Question", value_name="TeacherResponse")
    student_pvt = pd.pivot_table(
        dff,
        index=["StudentID", "LastName", "FirstName"],
        columns="TeacherResponse",
        values="Teacher1",
        aggfunc="count",
    ).fillna(0)
    student_pvt['total'] = student_pvt.sum(axis=1)
    student_pvt['overall_net'] = (student_pvt['Above Average'] - student_pvt['Below Average']) / student_pvt['total']
    
    student_pvt.columns = ['Total Above Average', 'Total Average', 'Total Below Average', 'total', 'Total Net']

    return student_pvt[['Total Above Average', 'Total Average', 'Total Below Average', 'Total Net']].reset_index()




def return_download_file(df):

    screener_questions = return_screener_questions(df.columns)

    sheets = []

    counselor_sheets = return_sheets_by_cohort(df, screener_questions)
    sheets.extend(counselor_sheets)


    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()
    f.seek(0)

    return f
