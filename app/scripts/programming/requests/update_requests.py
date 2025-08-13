import pandas as pd
import numpy as np



import app.scripts.utils as utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO


from app.scripts.utils_v2.stars.analyze_regents_max import main as analyze_regents_max_main
from app.scripts.utils_v2.stars.analyze_transcript import main as analyze_transcript_main

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    # process regents_max_data by loading CR 1_42 and passing it to the analyze_regents_max_main function
    cr_1_42_filename = utils.return_most_recent_report_by_semester(files_df, "1_42",year_and_semester=year_and_semester)        
    cr_1_42_df = utils.return_file_as_df(cr_1_42_filename)
    regents_max_df = analyze_regents_max_main(cr_1_42_df)
    

    # process transcript by loading CR 1_14 and passing it to the analyze_transcript function
    cr_1_14_filename = utils.return_most_recent_report_by_semester(files_df, "1_14",year_and_semester=year_and_semester)        
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    transcript_df = analyze_transcript_main(cr_1_14_df)
    


    # load student requests from CR 4_01
    cr_4_01_filename = utils.return_most_recent_report_by_semester(files_df, "4_01", year_and_semester=year_and_semester)
    cr_4_01_df = utils.return_file_as_df(cr_4_01_filename)
    
    # Students with ZA
    students_with_ZA = cr_4_01_df[cr_4_01_df["Course"] == "ZA"]["StudentID"].unique()
    
    ## remove students on the students_with_ZA list from CR_4_01_df
    cr_4_01_df = cr_4_01_df[~cr_4_01_df["StudentID"].isin(students_with_ZA)]

    ## loop through each students with a groupby to look at their requests
    grouped = cr_4_01_df.groupby("StudentID")
    students_lst = []
    for student_id, requests_df in grouped:
        student_transcript_dict = transcript_df[transcript_df["StudentID"] == student_id].to_dict('records')
        
        if len(student_transcript_dict) == 1:
            student_transcript_dict = student_transcript_dict[0]
        else:
            student_transcript_dict = {}
        student_regents_max_dict = regents_max_df[regents_max_df["StudentID"] == student_id].to_dict('records')
        if len(student_regents_max_dict) == 1:
            student_regents_max_dict = student_regents_max_dict[0]
        else:
            student_regents_max_dict = {}

        updated_student_requests = []
        for requested_course in requests_df["Course"].unique():
            if requested_course[0] not in ['S','M']:
                updated_student_requests.append(requested_course)
            else:
                updated_student_requests.append(update_student_course_request(requested_course,student_transcript_dict,student_regents_max_dict))
        students_lst.append({
            "StudentID": student_id,
            "student_courses": updated_student_requests
        })

     

    ## convert the list of dictionaries to a DataFrame in a wide format
    wide_format = []
    long_format = []

    for student in students_lst:
        StudentID = student["StudentID"]

        wide_format_dict = {"StudentID": StudentID, }
        long_format_dict = {"StudentID": StudentID, }

        i = 0
        for course in student["student_courses"]:
            i += 1
            long_format_dict["Course"] = course
            if course != "":
                long_format.append(long_format_dict.copy())

            wide_format_dict[f"Course{i}"] = course

        wide_format.append(wide_format_dict)

    wide_format_df = pd.DataFrame(wide_format)
    long_format_df = pd.DataFrame(long_format)  
    
    updated_requests_df = pd.DataFrame(long_format_df)
    updated_requests_df = updated_requests_df.fillna("")
    return updated_requests_df
    

def update_student_course_request(requested_course,student_transcript_dict,student_regents_max_dict):
    dept = requested_course[0]
    curriculum = requested_course[0:2]
    if curriculum == "MG":
        updated_course = check_geometry_request(requested_course, student_transcript_dict, student_regents_max_dict)
        return updated_course
    if curriculum == "SJ":
        updated_course = check_ess_request(requested_course, student_transcript_dict, student_regents_max_dict)
        return updated_course
    if curriculum in ["SW",'SD']:
        updated_course = check_elective_science_request(requested_course, student_transcript_dict, student_regents_max_dict)
        print(updated_course)
        return updated_course    
    if curriculum == "SC":
        updated_course = check_chem_request(requested_course, student_transcript_dict, student_regents_max_dict)
        return updated_course
    return requested_course

def check_geometry_request(requested_course, student_transcript_dict, student_regents_max_dict):
    """
    Check if the student has passed at least one math regents. If yes, return the original request course code. If not, check if the student has earned 0 algebra (ME) credits. If no, replace the G in the requested math course with an E so the student repeats the algebra course. If no, check the student's Alg1 regents score. If it's below a 55, replace the '21' in the original requested course code with a '43' so take a repeaters course. Otherwise, leave in the original requested course
    """
    num_math_passed = student_regents_max_dict.get("M Passed Count", 0)
    me_credits = student_transcript_dict.get("ME_earned", 0)
    alg1_regents = student_regents_max_dict.get("ALGEBRA REG Passed?", 0)
    alg1_score = student_regents_max_dict.get("ALGEBRA REG NumericEquivalent", 0)

    if num_math_passed >= 1:
        return requested_course
    elif requested_course[-2:] == 'QM':
        return requested_course.replace("G", "E").replace("21", "43")
    elif me_credits == 0:
        return requested_course.replace("G", "E")
    elif alg1_score < 55:
        return requested_course.replace("G", "E").replace("21", "43")
    else:
        return requested_course

def check_ess_request(requested_course, student_transcript_dict, student_regents_max_dict):
    num_science_passed = student_regents_max_dict.get("S Passed Count", 0)
    bio_credits = student_transcript_dict.get("SB_earned", 0)
    
    bio_regents = student_regents_max_dict.get("LIVING ENV REG Passed?", 0)
    bio_score = student_regents_max_dict.get("LIVING ENV REG NumericEquivalent", 0)
    

    if num_science_passed >= 1:
        return requested_course
    elif requested_course[-2:] == 'QM':
        return requested_course.replace("J", "B").replace("21", "43")
    elif bio_credits == 0:
        return requested_course.replace("J", "B")
    elif bio_score < 55:
        return requested_course.replace("J", "B").replace("21", "43")
    else:
        return requested_course    
    
def check_chem_request(requested_course, student_transcript_dict, student_regents_max_dict):
    num_science_passed = student_regents_max_dict.get("S Passed Count", 0)
    bio_credits = student_transcript_dict.get("SB_earned", 0)
    bio_regents = student_regents_max_dict.get("LIVING ENV REG Passed?", 0)
    bio_score = student_regents_max_dict.get("LIVING ENV REG NumericEquivalent", 0)
    alg1_regents = student_regents_max_dict.get("ALGEBRA REG Passed?", 0)
    alg1_score = student_regents_max_dict.get("ALGEBRA REG NumericEquivalent", 0)

    if num_science_passed >= 1 and alg1_regents:
        return requested_course
    else:
        return requested_course.replace("C", "J").replace("21", "43")        


def check_elective_science_request(requested_course, student_transcript_dict, student_regents_max_dict):
    num_science_passed = student_regents_max_dict.get("S Passed Count", 0)
    bio_credits = student_transcript_dict.get("SB_earned", 0)
    LE_credits = student_transcript_dict.get("SL_earned", 0)
    
    bio_regents = student_regents_max_dict.get("LIVING ENV REG Passed?", 0)
    bio_score = student_regents_max_dict.get("LIVING ENV REG NumericEquivalent", 0)
    
    second_character = requested_course[1]
    if num_science_passed >= 1:
        return requested_course
    elif (bio_credits + LE_credits) == 0: 
        return requested_course.replace(second_character, "B")
    elif bio_score < 55:
        return requested_course.replace(second_character, "B").replace("21", "43")
    else:
        return requested_course  