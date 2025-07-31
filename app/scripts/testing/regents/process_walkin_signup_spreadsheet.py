import pandas as pd
import numpy as np

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import create_walkin_signup_spreadsheet

from flask import current_app, session
import os

def main(form, request):
    walkin_spreadsheet_file = request.files[form.walkin_spreadsheet_file.name]

    updated_df = pd.read_excel(walkin_spreadsheet_file, sheet_name=0, skiprows=1)
    updated_df = updated_df.melt(
        id_vars=["StudentID", "LastName", "FirstName", "Counselor"],
        var_name="Course",
        value_name="final_signup?",
    ).fillna('')

    original_df = create_walkin_signup_spreadsheet.main()
    
    original_df = original_df.melt(
        id_vars=["StudentID", "LastName", "FirstName", "Counselor"],
        var_name="Course",
        value_name="current_registration?",
    )
    

    merged_df = pd.merge(
        updated_df,
        original_df,
        on=["StudentID", "LastName", "FirstName", "Counselor", "Course"],
        how="left",
    ).fillna(False)

    changes_df = merged_df[
        merged_df["final_signup?"] != merged_df["current_registration?"]
    ]

    changes_df["Action"] = merged_df["final_signup?"].apply(
        lambda x: "Add" if x else "Drop"
    )

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
    
    current_sections_df = current_registrations_df[['StudentID','Course','Section']]
    

    changes_df = changes_df.merge(current_sections_df, on=['StudentID','Course'], how='left').fillna(1)

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "Section",
        "Action",
    ]
    changes_df["GradeLevel"] = ""
    changes_df["OfficialClass"] = ""
    

    changes_df = changes_df[cols]

    return changes_df
