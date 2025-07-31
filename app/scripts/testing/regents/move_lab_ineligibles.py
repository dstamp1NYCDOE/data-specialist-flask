import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session
from io import BytesIO

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    regents_calendar_df["Curriculum"] = regents_calendar_df["CulminatingCourse"].str[
        0:2
    ]
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties")

    regents_courses = regents_calendar_df["CourseCode"]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename).fillna("")

    ## keep science regents exams
    science_regents_exams = [
        "SXR2E",  # Earth and Space Science
        "SXR3E",  # Biology
        "SXRPE",  # Physical Setting/Physics
        "SXRXE",  # Physical Setting/Chemistry
    ]
    science_regents_df = cr_1_01_df[
        cr_1_01_df["Course"].isin(science_regents_exams)
    ]
    science_regents_df = science_regents_df.rename(columns={"Course": "ExamCode",'Section': 'ExamSection'})
    science_regents_df = science_regents_df[['StudentID', 'ExamCode', 'ExamSection']]
    ## keep lab courses only
    lab_grades_df = cr_1_01_df[cr_1_01_df["Course"].str[-2:] == "QL"]
    lab_grades_df["ExamCode"] = lab_grades_df["Course"].apply(convert_lab_to_exam_code)
    lab_grades_df = lab_grades_df[['StudentID','LastName','FirstName','ExamCode','FinalMark']] 
    

    df = science_regents_df.merge(lab_grades_df, on=["StudentID", "ExamCode"], how="left")
    df['UpdatedExamSection'] = df.apply(return_new_section, axis=1)
    

    ## keep only students with a change
    df = df[df["ExamSection"] != df["UpdatedExamSection"]]
    df = df.rename(columns={"ExamCode": "Course", "UpdatedExamSection": "Section"})
    df['Action'] = 'Replace'
    df['GradeLevel'] = ''
    df['OfficialClass'] = ''
    final_cols = ['StudentID',
                  'LastName',
                  'FirstName',
                  'GradeLevel',
                  'OfficialClass',
                  'Course',
                  'Section',
                  'Action']
    df = df[final_cols]

    f = BytesIO()
    df.to_excel(
        f,
        index=False,
        sheet_name="Lab Ineligibles",
    )

    f.seek(0)
    return f

def return_new_section(row):
    current_exam_section = row["ExamSection"]
    lab_grade = row["FinalMark"]
    if lab_grade == 'F':
        return 88
    else:
        if current_exam_section == 88:
            return 1
        else:
            return current_exam_section


def convert_lab_to_exam_code(course_code):
    if course_code[0:2] == "SJ":
        return "SXR2E"
    if course_code[0:2] == "SB":
        return "SXR3E"
    if course_code[0:2] == "SP":
        return "SXRPE"
    if course_code[0:2] == "SC":
        return "SXRXE"
