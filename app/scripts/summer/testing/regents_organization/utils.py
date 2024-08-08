from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

def return_hub_location(section_row):
    Room = section_row["Room"]
    Time = section_row["Time"]
    exam_num = section_row["exam_num"]
    Section = section_row["Section"]

    if Room == 329:
        return 329
    if Room > 800:
        return {1: 919, 2: 823}.get(exam_num, 823)
    return {1: 727, 2: 519}.get(exam_num, 519)


def return_processed_registrations():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df.fillna({"Room": 202})
    cr_1_08_df["Room"] = cr_1_08_df["Room"].astype(int)

    cr_1_08_df["ExamAdministration"] = f"{month} {school_year+1}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    regents_calendar_df["exam_num"] = (
        regents_calendar_df.groupby(["Day", "Time"])["CourseCode"].cumcount() + 1
    )
    section_properties_df = pd.read_excel(
        path, sheet_name="SummerSectionProperties"
    )

    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )
    cr_1_08_df = cr_1_08_df.merge(section_properties_df[['Section','Type']], on=["Section"], how="left")

    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(return_full_exam_title)
    cr_1_08_df['hub_location'] = cr_1_08_df.apply(return_hub_location, axis=1)
    cr_1_08_df["Flag"] = "Student"

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left").fillna({"Sending school":'X'})
    cr_1_08_df = cr_1_08_df.drop_duplicates(subset=['StudentID','Course'])
    return cr_1_08_df

def return_full_exam_title(ExamTitle):

    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trigonometry",
        "LE": "Living Environment",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics",
    }
    return exam_title_dict.get(ExamTitle)
