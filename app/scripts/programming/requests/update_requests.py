import pandas as pd
import numpy as np



import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"


    # load student requests from CR 4_01
    cr_4_01_filename = utils.return_most_recent_report_by_semester(files_df, "4_01", year_and_semester=year_and_semester)
    cr_4_01_df = utils.return_file_as_df(cr_4_01_filename)
    print(cr_4_01_df)
    # Students with ZA
    students_with_ZA = cr_4_01_df[cr_4_01_df["Course"] == "ZA"]["StudentID"].unique()
    print(students_with_ZA)
    ## remove students on the students_with_ZA list from CR_4_01_df
    cr_4_01_df = cr_4_01_df[~cr_4_01_df["StudentID"].isin(students_with_ZA)]

    ## loop through each students with a groupby to look at their requests
    grouped = cr_4_01_df.groupby("StudentID")
    students_lst = []
    for student_id, requests_df in grouped:
        updated_student_requests = []
        for requested_course in requests_df["Course"].unique():
            if requested_course[0] not in ['S','M']:
                updated_student_requests.append(requested_course)
            else:
                updated_student_requests.append(update_student_course_request(requested_course))
        students_lst.append({
            "StudentID": student_id,
            "UpdatedRequests": updated_student_requests
        })

    print(students_lst)    

    ## convert the list of dictionaries to a DataFrame in a wide format
    wide_format = []
    long_format = []

    for student in students_lst:
        StudentID = student["StudentID"]
        UpdatedRequests = student["UpdatedRequests"]
        wide_format_dict = {"StudentID": StudentID}

        i = 0
        for course in UpdatedRequests:
            i += 1
            wide_format_dict[f"Course{i}"] = course

        wide_format.append(wide_format_dict)    
    
    updated_requests_df = pd.DataFrame(wide_format)
    updated_requests_df = updated_requests_df.fillna("")
    print(updated_requests_df)

def update_student_course_request(course):
    return course + '1'

