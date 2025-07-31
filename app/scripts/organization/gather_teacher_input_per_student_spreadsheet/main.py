import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO

from flask import session

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

        

    course_lst_str = form.course_lst.data
    course_lst = []
    if course_lst_str != '':
        course_lst = course_lst_str.split("\r\n")
    
    input_cols_str = form.input_cols.data
    input_cols = []
    if input_cols_str != '':
        input_cols = input_cols_str.split("\r\n")

    data_validation_values_str = form.data_validation_values.data
    data_validation_values = []
    if data_validation_values_str != '':
        data_validation_values = data_validation_values_str.split("\r\n")      
        data_validation_default_value = data_validation_values[0]  

    filename = utils.return_most_recent_report_by_semester(files_df, "1_49", year_and_semester=year_and_semester)
    
    counselors_df = utils.return_file_as_df(filename)
    counselors_df = counselors_df[['StudentID','Counselor']]

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[['StudentID','LastName','FirstName','Student DOE Email']]

    student_info_df = student_info_df.merge(counselors_df, on='StudentID', how='inner')

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()
    if course_lst_str != '':
        rosters_df = rosters_df[rosters_df['Course'].isin(course_lst)]


    filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule", year_and_semester=year_and_semester)
    master_schedule = utils.return_file_as_df(filename).fillna('')
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1","Teacher2", "Period"]
    ]

    df = rosters_df.merge(master_schedule, on=["Course", "Section"], how='left').fillna('')
    df = df.merge(student_info_df, on='StudentID', how='left')

    for input_col in input_cols:
        df[input_col] = data_validation_default_value

    ## computer labs only
    if form.computer_labs_flag.data:
        computer_labs = [201,221,319,519,603,704,729,901,919]
        df = df[df['Room'].isin(computer_labs)]

    ## periods
    periods = form.periods.data
    if 'ALL' in periods:
        pass
    else:
        periods = [x for x in periods if x!='ALL']
        period_regex_match = ''.join(periods)
        df = df[df['Period'].str.contains(f"[{period_regex_match}]")]

     ## teacher
    

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    cols = ['StudentID','LastName','FirstName',
            'Course',
            'Section',
            'Period',
            
            'Teacher1',
            'Teacher2',		
            ]  + input_cols

    counselor_cols = [
        'StudentID','LastName','FirstName','Student DOE Email',
        'Counselor',		
            ] + input_cols
    
    teachers_lst = []
    teacher_flag = form.teacher.data
    if teacher_flag == 'BOTH':
        teachers_lst = pd.unique(df[["Teacher1", "Teacher2"]].values.ravel("K"))
    if teacher_flag == 'Teacher1':    
        teachers_lst = pd.unique(df[["Teacher1"]].values.ravel("K"))
    if teacher_flag == 'Teacher2':    
        teachers_lst = pd.unique(df[["Teacher2"]].values.ravel("K"))

    teachers_lst.sort()
    

    # Student duplicates flag
    student_duplicates_flag = form.include_student_duplicates_flag.data

    for teacher in teachers_lst:
        
        if teacher_flag == 'BOTH':
            students_df = df[(df['Teacher1']==teacher) | (df['Teacher2']==teacher)]
        if teacher_flag == 'Teacher1':    
            students_df = df[df['Teacher1']==teacher]
        if teacher_flag == 'Teacher2':    
            students_df = df[df['Teacher2']==teacher]

        
        students_df = students_df[cols].sort_values(by=['Period','Course','Section','LastName','FirstName'])
        if student_duplicates_flag == False:
            students_df = students_df.drop_duplicates(subset=['StudentID'])
        
        if teacher_flag != 'NoTeacherPages':
            students_df.to_excel(writer, index=False, sheet_name=teacher)

    if form.include_counselors_flag.data:
        for Counselor, students_df in df.groupby('Counselor'):
            students_df = students_df[counselor_cols].drop_duplicates(subset='StudentID').sort_values(by=['LastName','FirstName'])
            students_df.to_excel(writer, index=False, sheet_name=Counselor)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()   
        
        if "," in sheet:
            start_col_index = 8
        else:
            start_col_index = 5 

        worksheet.data_validation(
            1, start_col_index, 1000, start_col_index+len(input_cols)-1, {"validate": "list", "source": data_validation_values}
        )   
    
    writer.close()
    f.seek(0)

    return f
