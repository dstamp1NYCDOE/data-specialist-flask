import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session


def main():
    school_year = session["school_year"]
    term = session["term"]

    dataframe_dict = {}

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"


    year_and_semester = f"{school_year}-{term}"
    
    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties").fillna('')
    regents_courses = regents_calendar_df['CourseCode']

    filename = utils.return_most_recent_report_by_semester(files_df, "1_01", year_and_semester=year_and_semester)
    cr_1_01_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_01_df[['StudentID', 'LastName', 'FirstName', 'Section', 'Course','Room']]
    registrations_df = cr_1_08_df[cr_1_08_df['Course'].isin(regents_courses)]


    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties")

    
    
    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    ## attach testing accommodations info
    filename = utils.return_most_recent_report(
        files_df, "testing_accommodations_processed"
    )
    testing_accommodations_df = utils.return_file_as_df(filename)
    testing_accommodations_df = testing_accommodations_df.drop_duplicates(
        keep="first", subset=["StudentID"]
    )

    
    condition_cols = [
        "StudentID",
        "ENL?",
        "HomeLang"

    ]
    testing_accommodations_df = testing_accommodations_df[condition_cols]

    registrations_df = registrations_df.merge(
        testing_accommodations_df, on=["StudentID"], how="left"
    ).fillna(False)

    registrations_df = registrations_df[registrations_df['ENL?']]
    registrations_df = registrations_df.sort_values(by=['Day','Time','Room','Section'])
    dataframe_dict['ENL_Glossaries'] = registrations_df


    # pivot table by exam
    pvt_tbl = pd.pivot_table( 
        registrations_df, index='ExamTitle', columns='HomeLang',values='StudentID',aggfunc='count'
    ).fillna(0).reset_index()

    dataframe_dict['ENL_Glossaries_count'] = pvt_tbl

    for exam_title, students_df in registrations_df.groupby('ExamTitle'):
        dataframe_dict[exam_title] = students_df[['LastName','FirstName','ExamTitle','Section','Room','HomeLang']]

    return dataframe_dict
