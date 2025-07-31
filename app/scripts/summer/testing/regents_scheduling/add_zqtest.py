
from io import BytesIO
from flask import current_app, session
from dotenv import load_dotenv


import pandas as pd

import os
import numpy as np

import datetime as dt
from app.scripts import scripts, files_df, photos_df, gsheets_df
import app.scripts.utils.utils as utils

from app.scripts.summer.programming import programming_utils



def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"


    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)

    students_df = cr_1_01_df[['StudentID','LastName','FirstName']].drop_duplicates()

    cr_1_01_df['is_exam_code'] = cr_1_01_df['Course'].apply(is_exam_code)

    exams_pvt = pd.pivot_table(cr_1_01_df[cr_1_01_df['Course'].str[0]!='Z'], index='StudentID',columns='is_exam_code',values='Section',aggfunc='count').fillna(0)
    exams_pvt['exam_only'] = (exams_pvt[True] > 0) & (exams_pvt[False] == 0)
    exams_pvt = exams_pvt.reset_index()

    exam_only_df = exams_pvt[exams_pvt['exam_only']][['StudentID']]
    
    
    students_already_with_zqtest = cr_1_01_df[cr_1_01_df['Course']=='ZQTEST']['StudentID']

    students_who_need_zqtest_df = exam_only_df[~exam_only_df['StudentID'].isin(students_already_with_zqtest)]
    

    students_who_need_zqtest_df = students_who_need_zqtest_df.merge(students_df, on='StudentID',how='left')

    students_who_need_zqtest_df["GradeLevel"] = ""
    students_who_need_zqtest_df["OfficialClass"] = ""
    students_who_need_zqtest_df["Course"] = 'ZQTEST'
    students_who_need_zqtest_df["Section"] = 1
    students_who_need_zqtest_df["Action"] = "Add"

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    students_who_need_zqtest_df.to_excel(writer)
    writer.close()
    f.seek(0)
    return f
    

def is_exam_code(course_code):
    return course_code[1:3] == 'XR'