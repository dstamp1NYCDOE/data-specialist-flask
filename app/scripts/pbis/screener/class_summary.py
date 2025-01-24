import pandas as pd
from pandas.api.types import CategoricalDtype

import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


from app.scripts.pbis.screener.main import process_screener_data


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.file.name]

    dfs_dict = pd.read_excel(filename, sheet_name=None)
    
    f = return_download_file(dfs_dict)

    download_name = f"UniversalScreenerAnalysisByClassByQuestion.xlsx"
    # return '', ''
    return f, download_name


def return_download_file(dfs_dict):
    sheets = []


    non_surveys = ['Students','Families']
    surveys_list = [df for (sheet, df) in dfs_dict.items() if not sheet in non_surveys]

    student_responses_df = dfs_dict['Students']
    student_responses_df = student_responses_df.drop(columns=['LastName','FirstName'])
    
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"



    df = pd.concat(surveys_list)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')] 

    ## remove non-credit bearing course
    df = df[df['Course'].str[0]!='G']
    df = df[df['Course'].str[0]!='R']
    df = df[df['Course'].str[0]!='Z']
    df = df[df['Course']!='EQS11QQI']


    screener_questions = return_screener_questions(df.columns)
    


    ## student val
    student_pvts = []
    for question in screener_questions:
        pvt = pd.pivot_table(df, index=["StudentID"], columns=question, values='Course',aggfunc='count').fillna(0)
        pvt['StudentAvg_'+question] = (pvt['Above Average'] - pvt['Below Average']) / pvt.sum(axis=1)
        student_pvts.append(pvt['StudentAvg_'+question])

    student_pvts = pd.concat(student_pvts, axis=1).reset_index()
    
    df = df.merge(student_pvts, on='StudentID', how='left')

    for question in screener_questions:
        question_str = 'StudentAvg_'+question
        pvt_1 = pd.pivot_table(df, index=["Teacher1","Period","Course","Section"], columns=question, values=question_str,aggfunc='count').fillna(0)
        pvt_1['TeacherAvg_'+question] = (pvt_1['Above Average'] - pvt_1['Below Average']) / pvt_1.sum(axis=1)
        pvt_1 = pvt_1[['TeacherAvg_'+question]]
        
        pvt_2 = pd.pivot_table(df, index=["Teacher1","Period","Course","Section"], values=question_str,aggfunc='mean')
        pvt_2 = pvt_2[question_str]


        merged_pvt = pvt_1.merge(pvt_2,on=["Teacher1","Period","Course","Section"], how='left').reset_index()
        merged_pvt = merged_pvt.sort_values(by=[question_str])

        sheets.append((question[0:31], merged_pvt))
    

    f = BytesIO()

    writer = pd.ExcelWriter(f)


    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()
    f.seek(0)

    return f


def return_screener_questions(columns):
    return [x for x in columns if "?" in x]

