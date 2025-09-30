import pandas as pd
import numpy as np



import app.scripts.utils as utils
import app.scripts.programming.post_summer.utils as post_summer_utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO


from app.scripts.utils_v2.stars.analyze_regents_max import main as analyze_regents_max_main
from app.scripts.utils_v2.stars.analyze_transcript import main as analyze_transcript_main


def main():
    """
    Take in
    1. Transcripts
    2. Regents Max
    Return updated fall opening day assignments.  
    """

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    # load student info from CR 3_07
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    cr_3_07_df['AdmitDate'] = pd.to_datetime(cr_3_07_df['AdmitDate'], errors='coerce')
    cr_3_07_df['new_admit?'] = cr_3_07_df.apply(lambda row: post_summer_utils.return_new_to_hsfi(row['AdmitDate'], school_year), axis=1)
    cr_3_07_df['year_in_hs'] = cr_3_07_df.apply(lambda row: utils.return_year_in_hs(row['GEC'], school_year), axis=1)

    # process regents_max_data by loading CR 1_42 and passing it to the analyze_regents_max_main function
    cr_1_42_filename = utils.return_most_recent_report_by_semester(files_df, "1_42",year_and_semester=year_and_semester)        
    cr_1_42_df = utils.return_file_as_df(cr_1_42_filename)
    regents_max_df = analyze_regents_max_main(cr_1_42_df)
    

    # process transcript by loading CR 1_14 and passing it to the analyze_transcript function
    cr_1_14_filename = utils.return_most_recent_report_by_semester(files_df, "1_14",year_and_semester=year_and_semester)        
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    transcript_df = analyze_transcript_main(cr_1_14_df)



    ## process SESIS
    from app.scripts.programming.requests.process_ieps import main as process_ieps_main
    sesis_filename = utils.return_most_recent_report_by_semester(files_df, "Recommended_Programs", year_and_semester=year_and_semester)
    sesis_df = utils.return_file_as_df(sesis_filename, skiprows=1)
    recommended_programs_dict = process_ieps_main(sesis_df)
    
    ## return processed progress towards graduation
    from app.scripts.progress_towards_graduation.analyze_progress_towards_graduation import process_1_68
    progress_towards_graduation_df = process_1_68()


    # iterate through the register
    output_list = []
    lst = []
    if lst:
        cr_3_07_df=cr_3_07_df[cr_3_07_df['StudentID'].isin(lst)]
    
    ## assign type of group
    for index, student in cr_3_07_df.iterrows():
        is_new_admit = student['new_admit?']
        year_in_hs = student['year_in_hs']
        StudentID = student['StudentID']
        try:
            regents_max = regents_max_df[regents_max_df['StudentID']==StudentID].to_dict('records')[0]
        except IndexError:
            regents_max = {}
        try:
            transcript = transcript_df[transcript_df['StudentID']==StudentID].to_dict('records')[0]
        except IndexError:
            transcript = {}

        recommended_program = recommended_programs_dict.get(StudentID, {})
        progress_towards_graduation = progress_towards_graduation_df[progress_towards_graduation_df['StudentID']==StudentID].to_dict('records')[0]


        student_data = {
            'year_in_hs': year_in_hs,
            'progress_towards_graduation': progress_towards_graduation,
            'recommended_program': recommended_program,
            'regents_max': regents_max,
            'transcript': transcript,
            'SWD_flag': recommended_program != {},
        }
        temp_dict = {
            'StudentID':StudentID,
            'GroupType': return_type_of_group(student_data)
        }
        output_list.append(temp_dict)

    output_df = pd.DataFrame(output_list)

    print(output_df)

    return ''
    ## Split Groups into even sizes



    f = BytesIO()
    writer = pd.ExcelWriter(f)
    student_assignments_df = pd.DataFrame()
    student_assignments_df.to_excel(writer, sheet_name="StudentAssignments", index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.autofit()

    writer.close()

    f.seek(0)
    download_name = f"Fall_{school_year+1}_first_day_of_school_groups.xlsx"


    return f, download_name


def return_type_of_group(student_data):
    return 'A'