import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO

def create():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    
    ## student_info


    jupiter_filenames = utils.return_most_recent_report_per_semester(files_df, "3_07")
    df_lst = []
    for jupiter_filename in jupiter_filenames:
        df = utils.return_file_as_df(jupiter_filename)
        df_lst.append(df)

    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    current_students = cr_3_07_df['StudentID'].unique().tolist()

    students_df = pd.concat(df_lst).drop_duplicates(subset=['StudentID'],keep='last')
    students_df = students_df[['StudentID','LastName','FirstName','GEC']]
    students_df['still_enrolled'] = students_df['StudentID'].apply(lambda x: x in current_students)


    jupiter_filenames = utils.return_most_recent_report_per_semester(files_df, "rosters_and_grades")
    
    df_lst = []
    for jupiter_filename in jupiter_filenames:
        
        term = jupiter_filename[9:9+6]
        df = utils.return_file_as_df(jupiter_filename)
        df['Term'] = term
        df = df.drop_duplicates(subset=['StudentID', 'Course'])
        df_lst.append(df)
    
    df = pd.concat(df_lst)

    ## courses to exclude
    df = df[~df['Course'].str[0].isin(['G','Z'])]


    from app.scripts.scholarship.jupiter.historical.teacher_analysis import analyze_teacher_impact
    from app.scripts.scholarship.jupiter.historical.student_analysis import analyze_student_trajectories
    from app.scripts.scholarship.jupiter.historical.output_generator import generate_excel_output

    # Run analyses with student info
    teacher_analysis = analyze_teacher_impact(df, students_df)
    student_analysis = analyze_student_trajectories(df, students_df)

    # Generate Excel output
    f = generate_excel_output(teacher_analysis, student_analysis)

    download_name = 'HistoricalJupiterAnalysis.xlsx'

    return f, download_name
