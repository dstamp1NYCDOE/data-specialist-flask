import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math


def main(request, form):
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    student_schedules_df = utils.return_file_as_df(filename).fillna("")
    student_schedules_df = student_schedules_df[student_schedules_df['Course'].str[0].isin(['E','M','H','S'])]
    student_schedules_df = student_schedules_df[student_schedules_df['Course'].str[-2:] != 'QL']
    course_to_exclude = ['EQS11QQI','EQS11','EES81QQE']
    student_schedules_df = student_schedules_df[~student_schedules_df['Course'].isin(course_to_exclude)]
    student_schedules_df['CourseCode'] = student_schedules_df.apply(return_jupiter_course, axis=1)

    student_schedules_df = student_schedules_df[ student_schedules_df['Course']!= student_schedules_df['CourseCode']]

    to_remove_df = student_schedules_df[['StudentID','LastName','FirstName','Course','Section']]
    to_remove_df['Action'] = 'Drop'
    to_remove_df = to_remove_df.rename(columns = {'Course':'Course'})

    to_add_df = student_schedules_df[['StudentID','LastName','FirstName','CourseCode','Section']]
    to_add_df['Action'] = 'Add'
    to_add_df = to_add_df.rename(columns = {'CourseCode':'Course'})

    df = pd.concat([to_remove_df,to_add_df])

    cols = ['StudentID','LastName','FirstName','GradeLevel','OfficialClass','Course','Section','Action']
    for col in filter(lambda x: x not in df.columns, cols):
        df[col] = ''

    return df[cols].to_html(index=False)





def return_jupiter_course(row):
    course_code = row["Course"]
    if len(course_code) <= 5:
        return course_code
    if course_code[0] in ["A", "T", "B", "Z"]:
        return course_code
    if course_code[5] in ["T", "X", "H"]:
        return course_code
    if course_code[0:7] in ["EES87QC", "EES87QD","EES87QW", "EES87QF", "EES87QG","EES81QE","EES83QE","EES85QE","EES88QC", "EES88QD", "EES88QF", "EES88QG","EES88QW","EES82QE","EES84QE","EES86QE"]:
        return course_code[0:7]
    if course_code[0:7] in ["MQS11QF", "MQS11QG", "EES87QF", "EES87QG", "EES88QF", "EES88QG"]:
        return course_code[0:7]
    if course_code in ['HGS41QQ','MES43QQ','SJS21QQ','HGS43QQ','EES83QQ','EES81QQ']:
        return course_code
    if course_code[-2:] == 'QM':
        return course_code
    try:
        if int(course_code[-1]) >0:
            return course_code
    except:
        pass

    if course_code[5] == "Q":
        return course_code[0:5]
    
    return course_code
