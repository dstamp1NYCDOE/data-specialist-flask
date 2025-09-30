import pandas as pd
import numpy as np



import app.scripts.utils as utils
import app.scripts.programming.post_summer.utils as post_summer_utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO


from app.scripts.utils_v2.stars.analyze_regents_max import main as analyze_regents_max_main
from app.scripts.utils_v2.stars.analyze_transcript import main as analyze_transcript_main

from app.scripts.programming.post_summer.incoming_ninth_requests import main as incoming_ninth_requests_main
from app.scripts.programming.post_summer.incoming_tenth_requests import main as incoming_tenth_requests_main
from app.scripts.programming.post_summer.update_requests import main as update_requests_main

def main():
    """
    Take in
    1. Current Requests 
    2. SESIS
    3. Transcripts
    4. Regents Max
    Return updated requests.  
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


    # load student requests from CR 4_01
    cr_4_01_filename = utils.return_most_recent_report_by_semester(files_df, "4_01", year_and_semester=year_and_semester)
    cr_4_01_df = utils.return_file_as_df(cr_4_01_filename)
    
    # Students with ZA
    students_with_ZA = cr_4_01_df[cr_4_01_df["Course"] == "ZA"]["StudentID"].unique()
    


    # iterate through the register
    output_list = []
    lst = [236868329,
240603449,
248569659,
259097707,]
    if lst:
        cr_3_07_df=cr_3_07_df[cr_3_07_df['StudentID'].isin(lst)]
        
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
        requests = cr_4_01_df[cr_4_01_df['StudentID']==StudentID]['Course'].to_list()

        student_data = {
            'StudentID':StudentID,
            'year_in_hs': year_in_hs,
            'requests': requests,
            'progress_towards_graduation': progress_towards_graduation,
            'recommended_program': recommended_program,
            'regents_max': regents_max,
            'transcript': transcript,
            'SWD_flag': recommended_program != {},
        }
        temp_dict = {
            'StudentID':StudentID,
            'is_new_admit': is_new_admit,
            'year_in_hs': year_in_hs,
            'student_courses':[],
            'SWD_flag': recommended_program != {},
        }

        if is_new_admit and year_in_hs == 1 and requests==[]:
            new_requests = incoming_ninth_requests_main(student_data)
            temp_dict['student_courses'] = new_requests
            output_list.append(temp_dict)

        elif is_new_admit and year_in_hs == 2 and requests==[]:
            new_requests = incoming_tenth_requests_main(student_data)
            temp_dict['student_courses'] = new_requests
            output_list.append(temp_dict)

        else:
            new_requests = update_requests_main(student_data)
            temp_dict['student_courses'] = new_requests
            output_list.append(temp_dict)


    # return ''
    wide_format = []
    long_format = []

    for student in output_list:
        StudentID = student["StudentID"]
        year_in_hs = student["year_in_hs"]
        is_new_admit = student["is_new_admit"]
        wide_format_dict = {"StudentID": StudentID, "year_in_hs": year_in_hs, "is_new_admit": is_new_admit}
        long_format_dict = {"StudentID": StudentID, "year_in_hs": year_in_hs, "is_new_admit": is_new_admit}

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

    requests_pivot_tbl = pd.pivot_table(
        long_format_df,
        values="StudentID",
        columns="year_in_hs",
        index="Course",
        aggfunc="count",
        margins=True,
    ).fillna(0)

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    wide_format_df.to_excel(writer, sheet_name="WideFormat", index=False)
    long_format_df.to_excel(writer, sheet_name="LongFormat", index=False)
    requests_pivot_tbl.to_excel(
        writer,
        sheet_name="counts",
    )

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.autofit()

    writer.close()

    f.seek(0)
    download_name = f"Fall_{school_year+1}_course_requests.xlsx"

    # return requests_pivot_tbl.to_html()
    # f, download_name = requests_pivot_tbl()
    return f, download_name
