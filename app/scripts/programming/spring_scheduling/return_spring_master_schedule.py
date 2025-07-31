import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session


def main():

    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterScheduleFinal", year_and_semester=year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/Annualization.xlsx")
    course_annualization_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_annualization_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}-Crossover")

    df = master_schedule_df.merge(
        course_annualization_df[["Course Code", "TeacherCourseCode"]],
        on=["Course Code"],
    )
    df = df.dropna(subset=["TeacherCourseCode"])

    df["Room"] = df.apply(update_rooms, axis=1)
    df["Cycle"] = df.apply(update_meeting_days, axis=1)
    df["Cycle"] = df.apply(convert_meeting_days_to_cycle, axis=1)

    df["SchoolDBN"] = "02M600"
    df["SchoolYear"] = f"{school_year}-{school_year+1}"
    df["TermID"] = "2"
    df["CourseCode"] = df["TeacherCourseCode"]
    df["Cycle day"] = df["Cycle"]
    df["SectionID"] = df["Section"]
    df["PeriodID"] = df["PD"]
    # df["Capacity"] = df["Active"]
    # df["Remaining Capacity"] = df["Active"]
    df["Gender"] = "0"
    df["Teacher Name"] = df["Teacher Name"]
    df["Course name"] = ""
    df["Mapped Section"] = ""
    df["Mapped Course"] = ""
    df["ErrDescription"] = ""
    df["Bell Schedule"] = "A"

    # courses_to_dupe
    courses_to_dupe = [
        ('GQS22QA','GQS21QA'),
        ('GQS22QB','GQS21QB')
    ]

    dfs_lst = [df]

    for course_1, course_2 in courses_to_dupe:
        df_ = df[df['CourseCode']==course_1]
        df_['CourseCode']= course_2
        dfs_lst.append(df_)

    df = pd.concat(dfs_lst)

    output_cols = [
        "SchoolDBN",
        "SchoolYear",
        "TermID",
        "CourseCode",
        "SectionID",
        'Course name',
        "PeriodID",
        "Cycle day",
        "Capacity",
        "Remaining Capacity",
        "Gender",
        "Teacher Name",
        "Room",
        "Mapped Course",
        "Mapped Section",
        "ErrDescription",
        "Bell Schedule",
    ]



    

    ## assign students
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)    

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename) 
    cr_3_07_df = cr_3_07_df[['StudentID','IEPFlag','GEC']].fillna('N')
    cr_3_07_df['year_in_hs'] = cr_3_07_df['GEC'].apply(utils.return_year_in_hs, args=(school_year,))
    cr_1_01_df = cr_1_01_df.merge(cr_3_07_df, on=['StudentID'], how='left')
    

    cr_1_01_df = cr_1_01_df.merge(
        course_annualization_df[["Course Code", "StudentCourseCode"]],
        right_on=["Course Code"],left_on=['Course']
    )
    cr_1_01_df = cr_1_01_df.dropna(subset=["StudentCourseCode"])
    cr_1_01_df['TEMP_CODE'] = cr_1_01_df.apply(process_sped_status,axis=1)
    
    cr_1_01_df = cr_1_01_df.merge(
        section_annualization_df,
        on=["Course",'Section','StudentCourseCode'],how='left'
    )
    cr_1_01_df['StudentSection'] = cr_1_01_df['StudentSection'].fillna(cr_1_01_df['Section'])
    
    
    


    master_schedule_check =  df[['CourseCode','SectionID','Teacher Name']]
    cr_1_01_df = cr_1_01_df.merge(master_schedule_check, left_on=['TEMP_CODE','StudentSection'],right_on=['CourseCode','SectionID'], how='left')
    cr_1_01_df = cr_1_01_df.drop_duplicates(subset=['StudentID','CourseCode'])
    cr_1_01_df['Course'] = cr_1_01_df['CourseCode'].fillna(cr_1_01_df['StudentCourseCode'])
    cr_1_01_df['Section'] = cr_1_01_df['SectionID'].fillna(cr_1_01_df['StudentSection'])



    cr_1_01_df['GradeLevel'] = cr_1_01_df['Grade']
    cr_1_01_df['OfficialClass'] = cr_1_01_df['OffClass']

     ### add extra courses based on student enrollement
    group_by_cols = ['StudentID',
                           'LastName',
                           'FirstName',
                           'GradeLevel',
                           'OfficialClass',
                           'year_in_hs']
    junior_apps_df = df[df['CourseCode'].isin(['GQS21QA','GQS21QB'])]
    
    ninth_grade_extra_lunch = []
    junior_college_apps = []
    for (StudentID, LastName, FirstName, GradeLevel, OfficialClass, year_in_hs), classes_df in cr_1_01_df.groupby(group_by_cols):
        if year_in_hs == 1:
            temp_df = classes_df[classes_df['Course'] == 'GAS82QA']
            if len(temp_df) > 0:
                temp_df['Course'] = 'ZL9'
                temp_df['Section'] = temp_df['Period']
                ninth_grade_extra_lunch.append(temp_df)
        if year_in_hs == 3:        
            temp_df = classes_df[classes_df['Course'].str[0:2] == 'PP']
            if len(temp_df) > 0:
                if temp_df.iloc[0,:]['Course'][-2:] == 'QB':
                    temp_df['Course'] = 'GQS21QA'
                elif temp_df.iloc[0,:]['Course'][-2:] == 'QA':
                    temp_df['Course'] = 'GQS21QB'
                
                junior_college_apps.append(temp_df)                    

    junior_college_apps_df = pd.concat(junior_college_apps)
    ninth_grade_extra_lunch_df = pd.concat(ninth_grade_extra_lunch)
    


    junior_apps_dff = junior_college_apps_df[['StudentID',
                           'LastName',
                           'FirstName',
                           'GradeLevel',
                           'OfficialClass',
                           'Course',
                           'Section',
                           'Period']].merge(junior_apps_df[['CourseCode','SectionID','PeriodID']], left_on=['Course','Period'], right_on=['CourseCode','PeriodID'], how='left')
    junior_apps_dff['keep'] = junior_apps_dff['StudentID'] + junior_apps_dff['SectionID'] + junior_apps_dff.index
    junior_apps_dff['keep_mask'] = junior_apps_dff['keep'].apply(lambda x: x % 2 == 0)
    
    junior_apps_dff = junior_apps_dff[junior_apps_dff['keep_mask']]
    junior_apps_dff['Section'] = junior_apps_dff['SectionID']
    junior_apps_dff['Action'] = 'Add'


    cr_1_01_df['Action'] = 'Add'
    
    student_output_cols = ['StudentID',
                           'LastName',
                           'FirstName',
                           'GradeLevel',
                           'OfficialClass',
                           'Course',
                           'Section',
                           'Action']
    
    dff = cr_1_01_df[student_output_cols]
    junior_apps_dff = junior_apps_dff[student_output_cols]

    dff = pd.concat([dff,junior_apps_dff,ninth_grade_extra_lunch_df])
    

    student_counts = pd.pivot_table(dff,index=['Course','Section'], values='StudentID',aggfunc='count')
    student_counts = student_counts.reset_index()
    student_counts['StudentID'] = student_counts.apply(adjust_capacity, axis=1)
    student_counts['Capacity'] = student_counts['StudentID']
    student_counts["Remaining Capacity"] = student_counts['StudentID']
    student_counts = student_counts.drop(columns=['StudentID'])
    student_counts = student_counts.rename(columns={'Course':"CourseCode",'Section':"SectionID"})
    df = df.merge(student_counts,on=['CourseCode','SectionID'], how='left').fillna(0)
    

    ## check

    check_df = cr_1_01_df[['Course','Section']].merge(df[['CourseCode','SectionID','Teacher Name']],left_on=['Course','Section'], right_on=['CourseCode','SectionID'], how='left').drop_duplicates(subset=['Course','Section'])
    


    f = BytesIO()
    writer = pd.ExcelWriter(f)

    df[output_cols].to_excel(writer, sheet_name='MasterSchedule')
    dff.to_excel(writer, sheet_name='StudentScheduleEditFile')
    check_df.to_excel(writer, sheet_name='Check')

    writer.close()
    f.seek(0)

    download_name = f"{school_year}_2_Master_Schedule.xlsx"
    return f, download_name

def adjust_capacity(row):
    course = row['Course']
    capacity = row['StudentID']

    if course == 'ZL':
        return max(capacity, 450)    

    if course[-2:0] == 'QT':
        return max(capacity,12)
    if course[-3:0] in ['QCT','QDT']:
        return max(capacity,12)    
    if course[-2:0] == 'QM':
        return max(capacity,15)

    return capacity
    


def process_sped_status(row):
    course = row['StudentCourseCode']
    sped_status = row['IEPFlag']
    if course[0] in ['S','M','E','H'] and course[-2:]!='QM' and sped_status=='Y':
        return return_ict_course_code(course)
    return course


def return_ict_course_code(course_code):
    if course_code[-1] in ['H','X']:
        return course_code
    if course_code[-2:] in ['QL']:
        return course_code    
    if course_code[0:4] in ['MQS2','MKS2']:
        return course_code
    if course_code in ['EQS11QQI','EQS11']:
        return course_code
    if len(course_code) == 5:
        return course_code + 'QT'
    if len(course_code) == 7:
        return course_code + 'T'
    if course_code[0:2] in ['SW','SD'] and course_code[6] != 'H': 
        return course_code[0:5] + 'QT'
    return course_code

def convert_meeting_days_to_cycle(row):
    days = row["Cycle"]
    cycle_str = ""
    for day in days:
        if day == "-":
            cycle_str += "0"
        else:
            cycle_str += "1"
    return cycle_str


def update_meeting_days(row):
    days = row["Days"]
    course_code = row['TeacherCourseCode']
    
    updated_days_dict = {
        "MTWRF": "MTWRF",
        "-----": "-----",
        "M----": "M----",
        "M-W-F": "-T-R-",
        "-T-R-": "M-W-F",
        "--W-F": "-T-R-",
    }
    if course_code in ['ZLYL'] or course_code[0]=='G':
        updated_days_dict["-T-R-"] = "--W-F"


    return updated_days_dict.get(days, "check")


def update_rooms(row):
    course_code = row["TeacherCourseCode"]
    section = row["Section"]

    room = row["Room"]

    if course_code[1] == "X":
        if section != 89:
            return 202
        else:
            return 329

    return room
