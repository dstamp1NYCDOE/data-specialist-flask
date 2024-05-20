import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from io import BytesIO
from flask import current_app, session


def main():

    filename = utils.return_most_recent_report(files_df, "3_07")
    students_df = utils.return_file_as_df(filename)
    school_year = session["school_year"]

    students_df["year_in_hs"] = students_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )
    cols = ["StudentID", "LastName", "FirstName", "year_in_hs", "Student DOE Email"]
    students_df = students_df[cols]

    regents_max_df = process_regents_max.main()

    regents_max_pvt = pd.pivot_table(
        regents_max_df,
        index="StudentID",
        columns="Exam",
        values="Mark",
        aggfunc=return_reg_mark,
    )

    students_df = students_df.merge(regents_max_pvt, on="StudentID", how="left")

    ### department GPA

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)

    ## attach numeric equivalent
    cr_1_14_filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left"
    )

    cr_1_14_df["dept"] = cr_1_14_df["Course"].str[0]

    student_department_gpa = pd.pivot_table(
        cr_1_14_df,
        index=["StudentID"],
        columns=["dept"],
        values="NumericEquivalent",
        aggfunc="mean",
    )
    student_department_gpa = student_department_gpa[["E", "M", "S", "H", "A"]]
    student_department_gpa.columns = [
        "ELA GPA",
        "Math GPA",
        "Science GPA",
        "Soc Stud GPA",
        "Art GPA",
    ]
    students_df = students_df.merge(student_department_gpa, on="StudentID", how="left")

    ## prior APs taken
    AP_courses_df = cr_1_14_df[cr_1_14_df["Course Title"].str[0:3] == "AP "]
    AP_courses_pvt = pd.pivot_table(
        AP_courses_df,
        index=["StudentID"],
        columns=["Course Title"],
        values="NumericEquivalent",
        aggfunc="mean",
    )

    students_df = students_df.merge(AP_courses_pvt, on="StudentID", how="left").fillna(
        ""
    )

    ## most recent semester attendance
    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report(
        files_df, "jupiter_period_attendance"
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## drop SAGA
    attendance_marks_df = attendance_marks_df[attendance_marks_df["Course"] != "MQS22"]

    ## convert date and insert marking period
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student["total"] = attd_by_student.sum(axis=1)

    attd_by_student["%_present"] = 100 * (
        1 - attd_by_student["unexcused"] / attd_by_student["total"]
    )
    attd_by_student["%_on_time"] = (
        100
        * attd_by_student["present"]
        / (attd_by_student["present"] + attd_by_student["tardy"])
    )
    attd_by_student = attd_by_student.fillna(0)
    attd_by_student = attd_by_student.reset_index()

    student_on_time_pvt = pd.pivot_table(
        attd_by_student,
        index="StudentID",
        columns="Pd",
        values="%_on_time",
        aggfunc="mean",
    )
    student_on_time_pvt.columns = [
        f"P{x}_%_on_time" for x in student_on_time_pvt.columns
    ]

    student_present_pvt = pd.pivot_table(
        attd_by_student,
        index="StudentID",
        columns="Pd",
        values="%_present",
        aggfunc="mean",
    )
    student_present_pvt.columns = [
        f"P{x}_%_present" for x in student_present_pvt.columns
    ]

    students_df = students_df.merge(
        student_present_pvt, on="StudentID", how="left"
    ).fillna("")
    students_df = students_df.merge(
        student_on_time_pvt, on="StudentID", how="left"
    ).fillna("")

    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)
    import app.scripts.attendance.attendance_tiers as attendance_tiers

    df_dict = attendance_tiers.main(RATR_df)
    ytd_attd_df = df_dict["ytd"]

    ytd_attd_dff = ytd_attd_df[["StudentID", "AttdTier"]]
    students_df = students_df.merge(ytd_attd_dff, on="StudentID", how="left")

    return students_df


def return_reg_mark(marks):
    return marks.to_list()[0]

def merge_with_interest_forms(data):
    vetting_df = main()
    vetting_df = vetting_df.drop(columns=['FirstName','LastName'])
    request = data['request']
    form = data['form']
    advanced_course_survey_file = request.files[form.advanced_course_survey_file.name]

    df_dict = pd.read_excel(advanced_course_survey_file, sheet_name=None)

    df_lst = []
    for course, df in df_dict.items():
        df['Course'] = course
        df_lst.append(df)

    df = pd.concat(df_lst)

    # keep interested students
    df = df[df['I am...']=='interested']

    # keep last submission
    df = df.drop_duplicates(subset=['StudentID','Course'], keep='last')
    cols = ['StudentID', 'FirstName', 'LastName',
       'Course', 'Rate your interest level in this course',
       'In a few sentences, why do you want to take this course?']
    df = df[cols]
    ## figure out interest level by all APs

    pvt_df = pd.pivot_table(df,index='StudentID',columns='Course',values='Rate your interest level in this course',aggfunc='max').reset_index()

    df['decision'] = ''
    df = df.merge(pvt_df, on='StudentID', how='left')
    

    df = df.merge(vetting_df, on='StudentID', how='left')
    
    
    df = df.sort_values(by=['Course','AttdTier','Rate your interest level in this course'])

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    df.to_excel(writer, sheet_name='combined', index=False)
    
    for course, dff in df.groupby('Course'):
        dff = dff.sort_values(by=['Course','AttdTier','Rate your interest level in this course'])
        dff.to_excel(writer, sheet_name=course, index=False)


    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()
        worksheet.data_validation('G2:G200', {'validate': 'list',
                                 'source': ['Yes','No','Waitlist'],
                                 })

    writer.close()

    f.seek(0)
    
    return f