import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.rdal_file.name]
    class_date = form.class_date.data
    rdal_df = process_rdal_csv_and_save(filename, class_date)

    consecutive_absences_df = return_consecutive_absences_df(class_date)

    f = return_rdal_report(consecutive_absences_df, rdal_df, class_date)

    download_name = f"RDAL_{class_date}.xlsx"

    return f, download_name


def return_rdal_report(consecutive_absences_df, rdal_df, class_date):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    absentee_form_url = utils.return_gsheet_url_by_title(
        gsheets_df, "absentee_form_results", year_and_semester
    )

    absentee_form_df = utils.return_google_sheet_as_dataframe(absentee_form_url)

    absentee_form_df = absentee_form_df.rename(columns={
        'Student Osis (ID) number\nNúmero de estudiante Osis (DNI)':'StudentID',
        'Date of Absence\nFecha de ausencia':'date_of_absence',
        'Expected Date of Return\nFecha prevista de regreso':'date_of_return',
        'Reason for Absence\nMotivo de la ausencia':'reason_for_absence',
       'If OTHER for reason of absence, please include a brief explanation. \nSi es OTRO por motivo de ausencia, incluya una breve explicación.':'brief_explanation'
    })

    class_date = pd.to_datetime(class_date)
    absentee_form_df['date_of_absence'] = pd.to_datetime(absentee_form_df['date_of_absence'], format="mixed")
    absentee_form_df['date_of_return'] = pd.to_datetime(absentee_form_df['date_of_return'], format ="mixed")
    

    mask = (absentee_form_df['date_of_absence'] <= class_date) & (class_date < absentee_form_df['date_of_return'])
    absentee_form_df = absentee_form_df[mask]
    

    absentee_form_df["Notes From Attendance Teacher"] = absentee_form_df["reason_for_absence"] + " - Return Date " + absentee_form_df['date_of_return'].apply(lambda x: x.strftime('%Y-%m-%d')) + '(From Google Form)'

    absentee_form_df = absentee_form_df[['StudentID',"Notes From Attendance Teacher"]]
    

    absent_students_lst = rdal_df["STUDENT ID"]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    print(filename)
    student_schedules_df = utils.return_file_as_df(filename).fillna("")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester=year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "6_42", year_and_semester=year_and_semester
    )
    teacher_reference_df = utils.return_file_as_df(filename)
    teacher_reference_df["TeacherName"] = (
        teacher_reference_df["LastName"]
        + " "
        + teacher_reference_df["FirstName"].str[0]
    )
    teacher_reference_df["DelegatedNickName1"] = teacher_reference_df[
        "TeacherName"
    ].str.upper()
    teacher_reference_df["DelegatedNickName2"] = teacher_reference_df[
        "TeacherName"
    ].str.upper()

    ## attach Teacher 2
    teachers_df = student_schedules_df[
        ["Course", "Section", "Teacher1", "Teacher2"]
    ].drop_duplicates()
    df = master_schedule_df.merge(
        teachers_df,
        left_on=["CourseCode", "SectionID"],
        right_on=["Course", "Section"],
        how="left",
    )
    # drop classes with no students
    df = df[df["Capacity"] > 0]
    # drop classes with no meeting days
    df = df[df["Cycle Day"] != 0]
    # drop classes attached to "staff"
    df = df[df["Teacher Name"] != "STAFF"]
    ## attach delegated nickname
    for teacher_num in [1, 2]:
        df = df.merge(
            teacher_reference_df[["Teacher", f"DelegatedNickName{teacher_num}"]],
            left_on=[f"Teacher{teacher_num}"],
            right_on=[f"Teacher"],
            how="left",
        )
    df_cols = [
        "Course",
        "Section",
        "Course name",
        "DelegatedNickName1",
        "DelegatedNickName2",
    ]
    df = df[df_cols]
    df = df.drop_duplicates(subset=["Course", "Section"])

    student_schedules_df = student_schedules_df.merge(
        df, on=["Course", "Section"], how="left"
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)

    attd_teacher_dict = {
        "3": "OVALLES P",
        "2": "GUILLOT T",
        "1": "AMEH M",
        "4": "CABRERA A",
    }
    RETAINED_ATTD_TEACHER = "AMEH M"
    ATTD_TEACHERS = attd_teacher_dict.values()


    cr_3_07_df["attd_teacher"] = cr_3_07_df["GEC"].apply(
        lambda x: attd_teacher_dict.get(str(x), RETAINED_ATTD_TEACHER)
    )


    cr_3_07_df = cr_3_07_df[
        [
            "StudentID",
            "Student DOE Email",
            "ParentLN",
            "ParentFN",
            "Phone",
            "attd_teacher",
        ]
    ]
    student_schedules_df = student_schedules_df.merge(
        cr_3_07_df, on=["StudentID"], how="left"
    ).fillna("")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor"]]

    student_schedules_df = student_schedules_df.merge(
        cr_1_49_df, on=["StudentID"], how="left"
    ).fillna("")

    student_schedules_df = student_schedules_df[
        student_schedules_df["DelegatedNickName1"] != ""
    ]
    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Student DOE Email",
        "ParentLN",
        "ParentFN",
        "Phone",
        "Course name",
        "Course",
        "Section",
        "Period",
        "DelegatedNickName1",
        "DelegatedNickName2",
        "Counselor",
        "attd_teacher",
    ]
    student_schedules_df = student_schedules_df[output_cols]
    student_schedules_df = student_schedules_df.sort_values(
        by=["Period", "Course", "Section"]
    )

    ## drop the classes taught by attd teachers
    student_schedules_df = student_schedules_df[
        ~student_schedules_df["DelegatedNickName1"].isin(ATTD_TEACHERS)
    ]

    absent_students_df = student_schedules_df[
        student_schedules_df["StudentID"].isin(absent_students_lst)
    ]

    absent_students_df = absent_students_df.merge(
        consecutive_absences_df, on="StudentID", how="left"
    )

    absent_students_df = absent_students_df.merge(
        absentee_form_df, on="StudentID", how="left"
    ).fillna('')
    

    f = BytesIO()
    rdal_df.to_excel(f, index=False)
    f.seek(0)

    f = return_rdal_report_xlsx(absent_students_df)

    return f


def return_rdal_report_xlsx(absent_students_df):
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    wellness_team_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "attd_teacher",
        "Counselor",
        "ParentLN",
        "ParentFN",
        "Phone",
        "consecutive_absences",
        "total_absences",
        "Notes From Attendance Teacher",
        "Notes From Classroom Teachers",
    ]
    students_by_attd_teacher = absent_students_df.drop_duplicates(subset=["StudentID"])
    # students_by_attd_teacher["Notes From Attendance Teacher"] = ""
    for attd_teacher, students_df in students_by_attd_teacher.groupby("attd_teacher"):
        students_df = students_df.sort_values(
            by=["consecutive_absences", "total_absences"], ascending=[False, False]
        )
        students_df = students_df.reset_index(drop=True)
        students_df.index = np.arange(2, len(students_df) + 2)
        students_df["Notes From Classroom Teachers"] = students_df.apply(
            return_classroom_teacher_filter, axis=1
        )

        students_df[wellness_team_cols].to_excel(
            writer, sheet_name=attd_teacher, index=False
        )

    teacher_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "attd_teacher",
        "Counselor",
        "Teacher",
        "Course",
        "Section",
        "Period",
        "ParentLN",
        "ParentFN",
        "Phone",
        "consecutive_absences",
        "total_absences",
        "Notes From Classroom Teacher",
        "Notes From Other Classroom Teachers",
        "Notes From Attendance Teacher",

    ]

    teachers_lst = pd.unique(
        absent_students_df[["DelegatedNickName1", "DelegatedNickName2"]].values.ravel(
            "K"
        )
    )
    teachers_lst = sorted(teachers_lst)
    teachers_lst = [teacher for teacher in teachers_lst if teacher != ""]

    combined_teacher_list = []
    for teacher in teachers_lst:
        students_df = absent_students_df[
            (absent_students_df["DelegatedNickName1"] == teacher)
            | (absent_students_df["DelegatedNickName2"] == teacher)
        ]
        students_df = students_df.sort_values(by=["Period", "Course"])
        students_df = students_df.reset_index(drop=True)

        students_df.index = np.arange(2, len(students_df) + 2)
        students_df["Teacher"] = teacher

        students_df["Notes From Attendance Teacher"] = students_df.apply(
            return_attd_teacher_lookup_formula, axis=1
        )
        students_df["Notes From Classroom Teacher"] = ""
        students_df["Notes From Other Classroom Teachers"] = ""
        students_df["Notes From Other Classroom Teachers"] = students_df.apply(
            return_classroom_teacher_filter, axis=1
        )
        students_df[teacher_cols].to_excel(writer, sheet_name=teacher, index=False)
        combined_teacher_list.append(students_df[teacher_cols])

    # lists + info by counselors
    students_by_counselor_df = absent_students_df.drop_duplicates(subset=["StudentID"])
    for counselor, students_df in students_by_counselor_df.groupby("Counselor"):
        students_df = students_df.sort_values(
            by=["consecutive_absences", "total_absences"], ascending=[False, False]
        )
        students_df = students_df.reset_index(drop=True)
        students_df.index = np.arange(2, len(students_df) + 2)
        students_df["Notes From Attendance Teacher"] = students_df.apply(
            return_attd_teacher_lookup_formula, axis=1
        )
        students_df["Notes From Classroom Teachers"] = ""
        students_df["Notes From Classroom Teachers"] = students_df.apply(
            return_classroom_teacher_filter, axis=1
        )
        students_df[wellness_team_cols].to_excel(
            writer, sheet_name=counselor, index=False
        )

    ## list of all students to absorb teacher note
    students_df = pd.concat(combined_teacher_list)
    students_df = students_df.sort_values(by="StudentID")
    students_df.index = np.arange(2, len(students_df) + 2)
    students_df["Notes From Attendance Teacher"] = ''
    students_df.apply(return_attd_teacher_lookup_formula, axis=1)
    students_df["Notes From Classroom Teacher"] = students_df.apply(return_classroom_teacher_lookup_formula, axis=1)
    students_df[teacher_cols].to_excel(writer, sheet_name="AllTeachers", index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()

    f.seek(0)
    return f


def return_classroom_teacher_filter(row):
    lookup_sheet = "AllTeachers"
    lookup_match = "A:A"
    lookup_index = "O:O"
    lookup_match_range = f"'{lookup_sheet}'!{lookup_match}"
    lookup_index_range = f"'{lookup_sheet}'!{lookup_index}"
    lookup_val_range = f"A{row.name}"

    formula_str = f"=join(char(10),unique(filter({lookup_index_range},{lookup_match_range}={lookup_val_range})))"
    
    return formula_str


def return_classroom_teacher_lookup_formula(row):
    lookup_sheet = row["Teacher"]
    lookup_match = "A:A"
    lookup_index = "O:O"
    lookup_match_range = f"'{lookup_sheet}'!{lookup_match}"
    lookup_index_range = f"'{lookup_sheet}'!{lookup_index}"
    lookup_val_range = f"A{row.name}"

    formula_str = f'="{lookup_sheet} - "&index({lookup_index_range}, match({lookup_val_range}, {lookup_match_range},0) , 0)'
    
    return formula_str


def return_attd_teacher_lookup_formula(row):
    lookup_sheet = row["attd_teacher"]
    lookup_match = "A:A"
    lookup_index = "k:k"
    lookup_match_range = f"'{lookup_sheet}'!{lookup_match}"
    lookup_index_range = f"'{lookup_sheet}'!{lookup_index}"
    lookup_val_range = f"A{row.name}"

    formula_str = f"=index({lookup_index_range}, match({lookup_val_range}, {lookup_match_range},0) , 0)"
    
    return formula_str


def process_rdal_csv_and_save(filename, class_date):

    rdal_df = pd.read_csv(filename, skiprows=2, skipfooter=1)

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = f"{year_and_semester}_{class_date}_RDAL.xlsx"

    path = os.path.join(current_app.root_path, f"data/{year_and_semester}/RDAL")
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    full_filename = os.path.join(path, filename)

    rdal_df.to_excel(full_filename, index=False)

    return rdal_df


import pandas as pd
import numpy as np
import datetime as dt
import glob


def return_consecutive_absences_df(class_date):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    RDAL_filenames = glob.glob(f"app/data/{year_and_semester}/RDAL/*.xlsx")

    RDAL_df_lst = []
    for RDAL_filename in RDAL_filenames:
        RDAL_df = pd.read_excel(RDAL_filename)[["STUDENT ID", "ABSENCE", "CLS"]]
        RDAL_df["ABSENCE"] = pd.to_datetime(RDAL_df["ABSENCE"], format="mixed")

        RDAL_dt = RDAL_df.iloc[0]["ABSENCE"].date()
        if class_date >= RDAL_dt:
            RDAL_df_lst.append(RDAL_df)

    RDAL_df = pd.concat(RDAL_df_lst)

    df = (
        pd.pivot_table(
            RDAL_df,
            index="STUDENT ID",
            columns=["ABSENCE"],
            values="STUDENT ID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )

    df = pd.melt(df, id_vars="STUDENT ID")

    students_lst = []
    for StudentID, absences_df in df.groupby("STUDENT ID"):
        absences_df = absences_df.sort_values("ABSENCE", ascending=False)
        absences_lst = [int(x) for x in absences_df["value"]]
        consecutive_absences = return_consective_absences(absences_lst)
        student_dict = {
            "StudentID": StudentID,
            "consecutive_absences": consecutive_absences,
            "total_absences": sum(absences_lst),
        }
        students_lst.append(student_dict)

    consecutive_absences_df = pd.DataFrame(students_lst)
    return consecutive_absences_df


def return_consective_absences(absences_lst):
    consecutive_absences = 0
    for absence in absences_lst:
        if absence == 0:
            return consecutive_absences
        else:
            consecutive_absences += 1
    return consecutive_absences
