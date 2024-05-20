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

    filename = utils.return_most_recent_report(files_df, "1_08")
    registrations_df = utils.return_file_as_df(filename)


    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties")

    
    

    ## drop inactivies
    registrations_df = registrations_df[registrations_df["Status"] == True]
    
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

    dataframe_dict['ENL_Glossaries'] = registrations_df

    return dataframe_dict
