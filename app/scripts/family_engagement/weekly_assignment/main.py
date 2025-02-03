from flask import render_template, request, send_file, session

from app.scripts import scripts, files_df
import app.scripts.utils as utils
import pandas as pd
import itertools


import sys 
sys.setrecursionlimit(10000)

def return_weekly_assignments(form, request):
    recent_attendance_analysis_df = analyze_recent_attendance(form, request)
    recent_assignment_analysis_df = analyze_recent_assignments(form, request)

    df = assign_students_to_staff()

    f = ''
    download_name = ''
    return f, download_name



def analyze_recent_attendance(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    attendance_marks_df['date'] = pd.to_datetime(attendance_marks_df['Date'])
    attendance_marks_df['week_number'] = attendance_marks_df['date'].dt.isocalendar().week

    week_of = form.week_of.data
    

    return ''


def analyze_recent_assignments(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(files_df, "assignments", year_and_semester=year_and_semester)
    assignments_df = utils.return_file_as_df(filename)
    assignments_df['date'] = pd.to_datetime(assignments_df['DueDate'])
    assignments_df['week_number'] = assignments_df['date'].dt.isocalendar().week

    week_of = form.week_of.data
    

    return ''


def assign_students_to_staff():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    rosters_df = utils.return_file_as_df(filename) 
    rosters_df = rosters_df.drop_duplicates(subset=['StudentID','Course','Section']).fillna('')

    resident_preferences = return_student_preferences(rosters_df)
    hospital_preferences, hospital_capacities = return_teacher_preferences_and_capacities(rosters_df)

    from matching.games import HospitalResident 
    
    game = HospitalResident.create_from_dictionaries(
    resident_preferences, hospital_preferences, hospital_capacities
    )
    solution = game.solve(optimal="hospital")

    solution_df = convert_matching_solution_to_dataframe(solution)



def convert_matching_solution_to_dataframe(solution):
    lst = []
    for teacher,students in solution.items():
        for student in students:
            lst.append({'StudentID':student,'Teacher':teacher})

    return pd.DataFrame(lst)


def return_student_preferences(rosters_df):

    teacher_preferences, teacher_capacities = return_teacher_preferences_and_capacities(rosters_df)
    rosters_df['Teachers'] = rosters_df[['Teacher1','Teacher2']].values.tolist()
    students_df = pd.pivot_table(rosters_df, index='StudentID', values='Teachers', aggfunc=return_list_of_teachers)
    student_preferences_dict = students_df.to_dict('index')
    student_preferences_dict = {k:v['Teachers'] for k, v in student_preferences_dict.items()}
    return student_preferences_dict


def return_teacher_preferences_and_capacities(rosters_df):
    teachers_lst = pd.unique(rosters_df[["Teacher1", "Teacher2"]].values.ravel("K"))
    teachers_lst = [teacher for teacher in teachers_lst if teacher!='']
    teachers_lst.sort()
    teacher_preferences = {}
    teacher_capacities = {}

    teacher_capacity = len(rosters_df['StudentID'].unique()) / len(teachers_lst)
    teacher_capacity = round(teacher_capacity,0) + 2
    for teacher in teachers_lst:
        students_df = rosters_df[(rosters_df['Teacher1']==teacher) | (rosters_df['Teacher2']==teacher)]
        teacher_preferences[teacher] = students_df['StudentID'].unique()
        teacher_capacities[teacher] = teacher_capacity

    return teacher_preferences, teacher_capacities

def return_list_of_teachers(x):
    temp_lst = []
    for i in x:
        for j in i:
            if j not in temp_lst and j != '':
                temp_lst.append(j)
    return temp_lst