import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

from flask import current_app, session

import pandas as pd
import numpy as np

def main(dept_name):
    
    course_info_df = utils.return_master_schedule_by_sheet('CourseInfo')
    flags = ['DoublePeriodFlag', 'CTEFlag','HalfCreditFlag']
    for col in flags:
        if col in course_info_df.columns:
            course_info_df[col] = course_info_df[col].astype(str).str.upper().map({'TRUE': True, 'FALSE': False})
            
    df = utils.return_master_schedule_by_sheet(dept_name)

    df = pd.melt(df,
                  id_vars=['department', 'first_name', 'last_name',"DefaultRoom"],
                  value_vars=[f'Period{i}' for i in range(1, 10)],  # Period1 through Period9
                  var_name='period',
                  value_name='course_str')
    df['period'] = df['period'].str.replace('Period', '').astype(int)
    df = df[df['course_str']!='']
    # look at the "course_str" column, count the number of "|" characters and append additional "|" if there are less than 3 so there is exactly 3
    df['course_str'] = df['course_str'].apply(lambda x: x + '|' * (3 - x.count('|')) if x.count('|') < 3 else x)
    # Split by | and expand into columns
    df[['course_code', 'TeacherID', 'Room', 'ReducedClassSize']] = df['course_str'].str.split('|', expand=True)
    ## if a particular course has a different class size number, update the capacity column. If the reducedclasssize column isn't there, keep what is in the capacity column (where it's a value from the spreadsheet or blank)
    # Convert the reduced class size string to an integer unless it's not there, then leave as it is
    df['ClassSize'] = df['ReducedClassSize'].str.extract('(\d+)').astype(float)
    df['ReducedClassSize'] = df['ReducedClassSize'].fillna(False)
    df['ReducedClassSize'] = df['ReducedClassSize'].apply(lambda x: True if x == '25' or x == '40' else False)
    
    ## use Default Room unless Specific Room is provided
    df['Room'] = df.apply(lambda x: x['Room'] if pd.notna(x['Room']) and x['Room'] != '' else x['DefaultRoom'], axis=1)

    ## attach course_info
    courses_in_spreadsheet = course_info_df['course_code'].unique()
    courses_not_in_spreadsheet = df[~df['course_code'].isin(courses_in_spreadsheet)]['course_code']


    df = df.merge(course_info_df, how='left', on='course_code')
    
    ### capacity reconcile
    df['Capacity'] = df['Capacity'].fillna('')
    


    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    df['SchoolDBN'] = '02M600'
    df['SchoolYear'] = school_year_str
    df['TermID'] = TermID
    df['Bell Schedule'] = 'A'
    df['Gender'] = '0'
    df['Mapped Course'] = ''
    df['Mapped Section'] = ''
    df['Course Name'] = ''
    df['PeriodID'] = df['period']

    df['CourseCode'] = df.apply(return_course_code, axis=1)
    df['Cycle Day'] = df.apply(return_cycle, axis=1)
    df['Teacher Name'] = df.apply(return_teacher_name, axis=1)
    df['SectionID'] = df.apply(return_section_number, axis=1)

    df['Capacity'] = df.apply(return_capacity, axis=1)    
    df['Remaining Capacity'] = df['Capacity']

    ## duplicate for mapped courses
    mapped_df = df.copy()
    mapped_df = mapped_df[mapped_df['Mapped Course'] != '']
    mapped_df['CourseCode'] = mapped_df['Mapped Course']
    mapped_df['SectionID'] = mapped_df['Mapped Section']
    mapped_df['Mapped Course'] = ''
    mapped_df['Mapped Section'] = ''




    ## duplicate for double period courses
    double_period_df = df[df['DoublePeriodFlag'] == True].copy()
    double_period_df['PeriodID'] = double_period_df['PeriodID'] +1

    ## duplicate for QP sections
    courses_to_not_add_QP = ['ESS81']
    qp_sections = df[df['course_code'].str.len() == 5]
    qp_sections = qp_sections[~qp_sections['course_code'].isin(courses_to_not_add_QP)]
    qp_sections = qp_sections[qp_sections['course_code'].str[0].isin(['M','S','H','E'])]
    qp_sections = qp_sections[qp_sections['department'].isin(['ela','math','science','ss'])]
    qp_sections['Mapped Course'] = qp_sections['CourseCode']
    qp_sections['Mapped Section'] = qp_sections['SectionID']
    qp_sections['CourseCode'] = qp_sections['Mapped Course'] + 'QP'
    qp_sections = qp_sections.drop(columns=['Capacity'])

    qp_course_info_df = course_info_df[course_info_df['course_code'].str.endswith('QP')]
    qp_course_info_df['Capacity'] = qp_course_info_df['Capacity'].apply(lambda x: 2 if x=='' else x)
    qp_course_info_df = qp_course_info_df.rename(columns={'course_code':'CourseCode'})
    qp_course_info_df = qp_course_info_df[['CourseCode','Capacity']] 
    
    qp_sections = qp_sections.merge(qp_course_info_df, how='left', on='CourseCode')
    qp_sections['Remaining Capacity'] = qp_sections['Capacity']

    ## special QP section
    qp_sections_2 = df[df['course_code']=='EES81QQE']
    qp_sections_2['Mapped Course'] = qp_sections_2['CourseCode']
    qp_sections_2['Mapped Section'] = qp_sections_2['SectionID']
    qp_sections_2['CourseCode'] = 'EES81QP'
    qp_sections_2['Capacity'] = 10
    qp_sections_2['Remaining Capacity'] = qp_sections_2['Capacity']

    if len(qp_sections_2) > 0:
        qp_sections = pd.concat([qp_sections, qp_sections_2], ignore_index=True)

    ## process_half_credit_courses
    half_credit_df = df[df['HalfCreditFlag'] == True].copy()
    half_credit_mappings = ["10101","01010","00101",'11110','11111']
    half_credit_dfs = []
    for half_credit_mapping in half_credit_mappings:
        half_credit_temp_df = half_credit_df[half_credit_df['HalfCreditMapping'].str.contains(half_credit_mapping)].copy()
        if len(half_credit_temp_df) > 0:
            half_credit_temp_df['Cycle Day'] = half_credit_mapping
            half_credit_temp_df['SectionID'] = half_credit_temp_df.apply(return_half_credit_section_number, axis=1)
            half_credit_dfs.append(half_credit_temp_df)
    if len(half_credit_dfs) > 0:
        half_credit_df = pd.concat(half_credit_dfs, ignore_index=True)
    else:
        half_credit_df = pd.DataFrame(columns=df.columns)


    ## EE YL Sections
    ee_yl_df = half_credit_df[half_credit_df['CourseCode'].isin(['GSS81'])].copy()
    ee_yl_df['CourseCode'] = 'GLS11'
    ee_yl_df['Cycle Day'] = ee_yl_df['Cycle Day'].apply(lambda x: '1' + x[1:])
    ee_yl_df['Capacity'] = ee_yl_df['Remaining Capacity']= 5


    df = pd.concat([df[df['HalfCreditFlag'] == False], mapped_df,double_period_df,half_credit_df,ee_yl_df,qp_sections], ignore_index=True)

    output_cols = [
        'SchoolDBN', 'SchoolYear', 'TermID', 'CourseCode', 'SectionID','Course Name',
        'PeriodID', 'Cycle Day', 'Capacity', 'Remaining Capacity','Gender','Teacher Name','Room','Mapped Course','Mapped Section',"Bell Schedule"]

    return df[output_cols].to_dict(orient='records')


def return_half_credit_section_number(course_row):
    TeacherID = course_row['TeacherID']
    period = course_row['period']
    cycle_day = course_row['Cycle Day']
    course_code = course_row['CourseCode']

    if course_code[0:4] == "RQS4":
        return 1

    if course_code == 'P':
        section = int(period) * 10 + (2*int(TeacherID)-1) + int(cycle_day[-1])
        return int(str(section)[::-1])
    else:
        section = int(period) * 10 + int(TeacherID) + int(cycle_day[-1])
        return section

def return_teacher_name(teacher_row):
    first_name = str(teacher_row["first_name"])

    last_name = str(teacher_row["last_name"])
    if len(first_name) > 0:
        return (
            last_name.replace(" ", "").replace("-", "").upper()
            + " "
            + first_name[0].upper()
        )
    else:
        return last_name.replace(" ", "").replace("-", "").upper()


def return_cycle(course_row):
    return "11111"

def return_course_code(course_row):
    course_code = course_row['course_code']
    
    if course_code[0] in ["P", "G", "A", "B", "T", "Z"]:
        return course_code
    if len(course_code) == 7:
        if course_code[5] != 5 and course_code[-2:] == "QA":
            return course_code[0:5]
    if course_code[-1] == 'A':
        return course_code[0:-1]
    return course_code

def return_section_number(course_row):
    TeacherID = course_row['TeacherID']
    period = course_row['period']
    course_code = course_row['course_code']

    if course_code[0:4] == "RQS4":
        return 1

    try:
        section = int(TeacherID) * 10 + int(period)
    except ValueError:
        print(f"Invalid TeacherID '{TeacherID}' for course '{course_code}'")
        return ''
    return section


def return_capacity(course_row):
    capacity = course_row['Capacity']
    reduced_class_size_flag = course_row['ReducedClassSize']
    class_size = course_row['ClassSize']

    if class_size > 0 and not reduced_class_size_flag:
        return int(class_size)

    if capacity != '' and not reduced_class_size_flag:
        return int(capacity)
    course_code = course_row['course_code']
    section = course_row['SectionID']

    is_cte = course_row['CTEFlag']
    if is_cte:
        return 25

    reduced_class_size_flag = course_row['ReducedClassSize']
    if reduced_class_size_flag:
        GENED = 25
        ICT_SWD = 10
        ICT_GENED = 15
        SC = 15
        if course_code[0:2] == 'PP':
            GENED = 40
    else:
        GENED = 32
        ICT_SWD = 12
        ICT_GENED = 22
        SC = 15
        if course_code[0:2] == 'PP':
            GENED = 50

    if course_code[-2:] == "QT" or course_code[-3:] == "QET":
        return ICT_SWD
    if course_code[-2:] == "QA":
        return ICT_GENED
    if course_code[-2:] == "QM":
        return SC
    
    return GENED