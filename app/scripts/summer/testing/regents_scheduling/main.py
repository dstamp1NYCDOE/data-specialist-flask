import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    dataframe_dict = {}

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"


    filename = utils.return_most_recent_report(files_df, "1_08")
    registrations_df = utils.return_file_as_df(filename)
    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
    ]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SummerSectionProperties")

    ## drop inactivies
    registrations_df = registrations_df[registrations_df["Status"] == True]
    registrations_df = registrations_df[cols]

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    registrations_df = registrations_df.merge(cr_s_01_df, on=["StudentID"], how="left")    

    ## keep only exams offered
    exams_offered = regents_calendar_df['CourseCode']
    registrations_df = registrations_df[registrations_df['Course'].isin(exams_offered)]

    # ## exam_info

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    testing_accommodations_df = return_student_accommodations(request,form)

    print(testing_accommodations_df)

    registrations_df = registrations_df.merge(
        testing_accommodations_df, on=["StudentID"], how="left"
    ).fillna(False)

    

    ## attach number of exams students are taking per day and flag potential conflicts

    num_of_exams_by_student_by_day = pd.pivot_table(
        registrations_df,
        index=["StudentID", "Day"],
        columns=["Time"],
        values="Course",
        aggfunc="count",
    ).fillna(0)
    num_of_exams_by_student_by_day["Total"] = num_of_exams_by_student_by_day.sum(axis=1)
    num_of_exams_by_student_by_day.columns = [
        f"{col}_#_of_exams_on_day" for col in num_of_exams_by_student_by_day.columns
    ]
    num_of_exams_by_student_by_day["Conflict?"] = num_of_exams_by_student_by_day[
        "Total_#_of_exams_on_day"
    ].apply(lambda x: x > 1)

    num_of_exams_by_student_by_day = num_of_exams_by_student_by_day.reset_index()

    registrations_df = registrations_df.merge(
        num_of_exams_by_student_by_day, on=["StudentID", "Day"], how="left"
    ).fillna(0)

    ## attach conflict flags

    registrations_df['AM_Conflict?'] = registrations_df.apply(return_am_conflict_status, axis=1)
    registrations_df['PM_Conflict?'] = registrations_df.apply(return_pm_conflict_status, axis=1)
    registrations_df['AM_PM_Conflict?'] = registrations_df.apply(return_am_pm_conflict_status, axis=1)

    print(section_properties_df.columns)
    print(registrations_df.columns)

    ## attach default section
    merge_cols = [
        'SWD?', 'ENL?', 'time_and_a_half?', 'double_time?',
       'read_aloud?', 'scribe?', 'large_print?', 'AM_Conflict?',
       'PM_Conflict?', 'AM_PM_Conflict?'
    ]
    dff = section_properties_df.drop_duplicates(subset=['Type'])
    dff = dff[dff['Section']>2]
    df = registrations_df.merge(dff, on=merge_cols, how='left').fillna(1)

    ## apply special assignment rules
    df['Section'] = df.apply(assign_scribe_kids,axis=1)
    df['Section'] = df.apply(reassign_gen_ed,axis=1)

    enrollment_pvt = pd.pivot_table(
        df,index=['Day','Time','ExamTitle'],columns=['Section','Type'], values='StudentID',aggfunc='count'
    ).fillna(0)

    return enrollment_pvt

def assign_scribe_kids(student_row):
    is_scribe = student_row['scribe?']
    if not is_scribe:
        return student_row['Section']
    elif student_row['AM_Conflict?']:
        return 61
    elif student_row['AM_PM_Conflict?']:
        return 62
    elif student_row['PM_Conflict?']:
        return 63
    return 60

def reassign_gen_ed(student_row):
    current_section = student_row['Section']
    dbn = student_row['Sending school']
    ## HSFI
    if dbn=='02M600' and current_section == 3:
        current_section = 15
    ## YABC
    if dbn=='79M379' and current_section == 3:
        current_section = 14
    ## UAG
    if dbn=='02M507' and current_section == 3:
        current_section = 13
    ## A&D
    if dbn=='02M630' and current_section == 3:
        current_section = 12
    ## LaGuardia
    if dbn=='03M485' and current_section == 3:
        current_section = 11
    ## BOSS
    if dbn=='02M393' and current_section == 3:
        current_section = 10

    return current_section

def return_am_conflict_status(student_row):
    num_of_am_exams = student_row['AM_#_of_exams_on_day']
    num_of_pm_exams = student_row['PM_#_of_exams_on_day']
    total_num_of_exams = student_row['Total_#_of_exams_on_day']

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams == 0 and num_of_am_exams > 1:
        return True
    return False

def return_pm_conflict_status(student_row):
    num_of_am_exams = student_row['AM_#_of_exams_on_day']
    num_of_pm_exams = student_row['PM_#_of_exams_on_day']
    total_num_of_exams = student_row['Total_#_of_exams_on_day']

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams > 1 and num_of_am_exams == 1:
        return True
    return False

def return_am_pm_conflict_status(student_row):
    num_of_am_exams = student_row['AM_#_of_exams_on_day']
    num_of_pm_exams = student_row['PM_#_of_exams_on_day']
    total_num_of_exams = student_row['Total_#_of_exams_on_day']

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams >= 1 and num_of_am_exams >= 1:
        return True
    return False



def return_student_accommodations(request,form):
    student_exam_registration = request.files[
        form.combined_regents_registration_spreadsheet.name
    ]
    df_dict = pd.read_excel(student_exam_registration, sheet_name=None)

    sheets_to_ignore = ["Directions", "HomeLangDropdown"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")  

    ## what has exams registered for
    exam_cols = ['Alg1','ELA','Alg2','Global','Chem','ES','USH','Geo','LE']
    
    df = df[df[exam_cols].any(axis=1)]

    pvt_tbl = pd.pivot_table(df, index='school_name', values='StudentID', aggfunc='count').reset_index()
    
    print(pvt_tbl.sort_values(by='StudentID'))
    cols = [
        "StudentID",
        "SWD?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",
        "special_notes",
    ]

    boolean_cols = [
        "SWD?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",        
    ]

    df[boolean_cols] = df[boolean_cols].astype(bool)
    df['SWD?'] = df.apply(check_SWD_flag, axis=1)

    return df[cols]  


def check_SWD_flag(student_row):
    SWD_cols = ["SWD?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",]
    return student_row[SWD_cols].any()