import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO

from flask import session

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    student_subset_title = form.subset_title.data

    student_lst_str = form.subset_lst.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]
        

    course_lst_str = form.course_lst.data
    course_lst = []
    if course_lst_str != '':
        course_lst = course_lst_str.split("\r\n")
        print(course_lst)

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

    rosters_df[student_subset_title] = rosters_df["StudentID"].apply(
        lambda x: x in student_lst
    )

    filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule", year_and_semester=year_and_semester)
    master_schedule = utils.return_file_as_df(filename).fillna('')
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1","Teacher2", "Period"]
    ]

    df = rosters_df.merge(master_schedule, on=["Course", "Section"], how='left').fillna('')
    df = df.merge(student_info_df, on='StudentID', how='left')

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
    teacher_flag = form.teacher.data


    
    if form.inner_or_outer.data == 'inner':
        df = df[df[student_subset_title]==True]
    if form.inner_or_outer.data == 'outer':
        df = df[df[student_subset_title]==False]

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    cols = ['StudentID','LastName','FirstName','Student DOE Email',
            'Course',
            'Section',
            'Period',
            'Room',
            'Teacher1',
            'Teacher2',
            student_subset_title		
            ]

    counselor_cols = [
        'StudentID','LastName','FirstName','Student DOE Email',
        'Counselor',
        student_subset_title		
            ]
    if teacher_flag == 'BOTH':
        teachers_lst = pd.unique(df[["Teacher1", "Teacher2"]].values.ravel("K"))
    if teacher_flag == 'Teacher1':    
        teachers_lst = pd.unique(df[["Teacher1"]].values.ravel("K"))
    if teacher_flag == 'Teacher2':    
        teachers_lst = pd.unique(df[["Teacher2"]].values.ravel("K"))

    teachers_lst.sort()
    

    ## all students with course info
    df[cols].sort_values(by=['Period','Course','Section','LastName','FirstName']).to_excel(writer, index=False, sheet_name='all_rosters')
    
    ## all students with counselor info
    df[counselor_cols].drop_duplicates(subset='StudentID').sort_values(by=['LastName','FirstName']).to_excel(writer, index=False, sheet_name='all_students')

    for teacher in teachers_lst:
        
        if teacher_flag == 'BOTH':
            students_df = df[(df['Teacher1']==teacher) | (df['Teacher2']==teacher)]
        if teacher_flag == 'Teacher1':    
            students_df = df[df['Teacher1']==teacher]
        if teacher_flag == 'Teacher2':    
            students_df = df[df['Teacher2']==teacher]

        
        students_df = students_df[cols].sort_values(by=['Period','Course','Section','LastName','FirstName'])
        students_df.to_excel(writer, index=False, sheet_name=teacher)

    if form.include_counselors_flag.data:
        for Counselor, students_df in df.groupby('Counselor'):
            students_df = students_df[counselor_cols].drop_duplicates(subset='StudentID').sort_values(by=['LastName','FirstName'])
            students_df.to_excel(writer, index=False, sheet_name=Counselor)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()            
    
    writer.close()
    f.seek(0)

    return f
