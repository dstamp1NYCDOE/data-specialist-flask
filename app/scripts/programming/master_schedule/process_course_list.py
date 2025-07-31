import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

from flask import current_app, session

import pandas as pd

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
    # Fill missing values in Capacity column with -1
    df['ReducedClassSize'] = df['ReducedClassSize'].fillna(False)
    df['ReducedClassSize'] = df['ReducedClassSize'].apply(lambda x: True if x == '25' or x == '40' else False)
    print(df)
    ## use Default Room unless Speciic Room is provided
    df['Room'] = df.apply(lambda x: x['Room'] if pd.notna(x['Room']) and x['Room'] != '' else x['DefaultRoom'], axis=1)

    ## attach course_info
    df = df.merge(course_info_df, how='left', on='course_code')
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


    ## process_half_credit_courses
    half_credit_df = df[df['HalfCreditFlag'] == True].copy()
    half_credit_mappings = ["10101","01010","00101"]
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
    
    
    df = pd.concat([df[df['HalfCreditFlag'] == False], mapped_df,double_period_df,half_credit_df], ignore_index=True)

        


    output_cols = [
        'SchoolDBN', 'SchoolYear', 'TermID', 'CourseCode', 'SectionID','Course Name',
        'PeriodID', 'Cycle Day', 'Capacity', 'Remaining Capacity','Gender','Teacher Name','Room','Mapped Course','Mapped Section',"Bell Schedule"]


    return df[output_cols].to_dict(orient='records')


def return_half_credit_section_number(course_row):
    TeacherID = course_row['TeacherID']
    period = course_row['period']
    cycle_day = course_row['Cycle Day']
    
    if course_row['CourseCode'][0] == 'P':
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
    return course_code

def return_section_number(course_row):
    TeacherID = course_row['TeacherID']
    period = course_row['period']
    course_code = course_row['course_code']
    section = int(TeacherID) * 10 + int(period)
    return section


def return_capacity(course_row):
    capacity = course_row['Capacity']
    reduced_class_size_flag = course_row['ReducedClassSize']
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
        GENED = 34
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