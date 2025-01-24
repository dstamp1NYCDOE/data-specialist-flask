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
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]
    students_lst = cr_3_07_df['StudentID']

    jupiter_attd_filenames = utils.return_most_recent_report_per_semester(files_df, "jupiter_period_attendance")
    
    attendance_marks_df_lst = []
    for jupiter_attd_filename in jupiter_attd_filenames:
        
        term = jupiter_attd_filename[9:9+6]
        attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
        attendance_marks_df['Term'] = term
        attendance_marks_df_lst.append(attendance_marks_df)
    
    attendance_marks_df = pd.concat(attendance_marks_df_lst)
    

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]



    attd_by_student_by_day = pd.pivot_table(
            attendance_marks_df,
            index=["StudentID", "Date"],
            columns="Type",
            values="Pd",
            aggfunc="count",
        ).fillna(0)

    attd_by_student_by_day["in_school?"] = (
        attd_by_student_by_day["present"] + attd_by_student_by_day["tardy"]
    ) >= 2
    attd_by_student_by_day = attd_by_student_by_day.reset_index()[
        ["StudentID", "Date", "in_school?"]
    ]



    attendance_marks_df = attendance_marks_df.merge(
        attd_by_student_by_day, on=["StudentID", "Date"], how="left"
    ).fillna(False)

    first_period_present_by_student_by_day = pd.pivot_table(
        attendance_marks_df[attendance_marks_df["in_school?"]],
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="min",
    ).reset_index()
    first_period_present_by_student_by_day['StudentID'] = first_period_present_by_student_by_day['StudentID'].astype(int)

    first_period_present_by_student_by_day["first_period_present"] = (
        first_period_present_by_student_by_day[["present", "tardy"]].min(axis=1)
    )

    first_period_present_by_student_by_day = first_period_present_by_student_by_day[
        ["StudentID", "Date", "first_period_present"]
    ]
    attendance_marks_df['StudentID'] = attendance_marks_df['StudentID'].astype(int)
    attendance_marks_df = attendance_marks_df.merge(
        first_period_present_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    attendance_marks_df["potential_cut"] = attendance_marks_df.apply(
        determine_potential_cut, axis=1
    )

    
    cuts_by_teacher_pvt = pd.pivot_table(attendance_marks_df,index=['Teacher','Pd','Term'], columns='potential_cut',values='StudentID',aggfunc='count')


    

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID","Term","Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student['total'] = attd_by_student.sum(axis=1)
    attd_by_student = attd_by_student[attd_by_student['total']>5]

    attd_by_student["%_late"] = attd_by_student["tardy"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student["%_absent"] = attd_by_student["unexcused"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student = attd_by_student.fillna(0)
    attd_by_student = attd_by_student.reset_index()
    students_df = students_df.merge(attd_by_student, on=["StudentID"], how='left') 

    


    students_pvt_df = pd.pivot_table(students_df,index=['StudentID','LastName','FirstName','year_in_hs'], columns=['Term','Pd'],values=['%_late','%_absent'],aggfunc='max').fillna('')
    students_pvt_df = students_pvt_df.reorder_levels([1,2,0],axis=1)
    students_pvt_df = students_pvt_df.sort_values(by=['year_in_hs','LastName','FirstName','StudentID'])
    f = BytesIO()
    # students_pvt_df[students_pvt_df['StudentID'].isin(students_lst)].to_excel(f, sheet_name='CurrentStudentsByPeriod')

    cuts_by_teacher_pvt.reset_index().to_excel(f,sheet_name='cuts_by_teacher')

    f.seek(0)
    download_name = 'HistoricalJupiterAnalysis.xlsx'

    return f, download_name



def determine_potential_cut(student_row):
    is_in_school = student_row["in_school?"]

    if is_in_school == False:
        return False

    attendance_type = student_row["Type"]
    period = student_row["Pd"]
    first_period_present = student_row["first_period_present"]
    if attendance_type == "unexcused" and period >= first_period_present:
        return True

    return False