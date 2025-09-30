import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

import math


def main():
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    section_properties_df = pd.read_excel(
        path, sheet_name="SectionProperties"
    ).dropna(subset='Type')

    section_properties_df = section_properties_df.fillna(202)


    output_lst = []
    for _,exam in regents_calendar_df.iterrows():
        for _, section in section_properties_df.iterrows():
            course_row = return_course_row(exam, section, school_year_str, TermID)
            exam_code = exam['CourseCode']
            SectionID = section['Section']
            if SectionID == 88 and exam_code[0] != 'S':
                pass
            else:
                output_lst.append(course_row)

    
    return pd.DataFrame(output_lst)



def return_course_row(exam, section, school_year_str,TermID):
    SchoolDBN = '02M600'
    
    exam_code = exam['CourseCode']
    SectionID = section['Section']

    exam_num =  exam['exam_num']
    exam_time =  exam['Time']
    room_col = f'{exam_time}{int(exam_num)}_ROOM'

    exam_room = '202'
    exam_room = f"{int(section[room_col])}"

    cycle_day = "'00000"

    exam_type = section['Type']
    if exam_type == 'LAB INELIGIBLE':
        teacher_name = 'LAB INELIGIBLE'
        exam_room = '619'
    else:
        teacher_name = 'EXAM'

    temp_dict = {
    'SchoolDBN':'02M600',
    'SchoolYear':school_year_str,
    'TermID':TermID,
    'CourseCode':exam_code,
    'SectionID':SectionID,
    'Course Name':'',
    'PeriodID':f"{10}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(SectionID),
    'Remaining Capacity':return_capacity(SectionID),
    'Gender':'0',
    'Teacher Name':teacher_name,
    'Room':exam_room,
    'Mapped Course':'',
    'Mapped Section':'',
    'Bell Schedule':'A',
    }
    return temp_dict

def return_capacity(section):
    if section < 20:
        return 33
    else:
        return 15
