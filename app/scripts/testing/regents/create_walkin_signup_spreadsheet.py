import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from flask import current_app, session



def main():
    school_year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "1_49")
    students_df = utils.return_file_as_df(filename).fillna({'Counselor':'D75'})

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties").fillna('')
    regents_courses = regents_calendar_df['CourseCode']

    filename = utils.return_most_recent_report_by_semester(files_df, "1_01", year_and_semester=year_and_semester)
    cr_1_01_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_01_df[['StudentID', 'LastName', 'FirstName', 'Section', 'Course','Room']]
    current_registrations_df = cr_1_08_df[cr_1_08_df['Course'].isin(regents_courses)]

    registrations_pvt = pd.pivot_table(current_registrations_df, index='StudentID',columns='Course', values='Section', aggfunc='max')
    registrations_pvt = registrations_pvt.fillna(0)
    registrations_pvt = registrations_pvt.apply(lambda x: x>0)
    registrations_pvt = registrations_pvt.reset_index()
    
    students_df = students_df[['StudentID','LastName','FirstName','Counselor']]

    students_df = students_df.merge(registrations_pvt, on='StudentID',how='left').fillna(False)
    students_df = students_df.sort_values(by=['Counselor','LastName','FirstName'])

    return students_df
    