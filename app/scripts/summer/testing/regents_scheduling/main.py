import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session

import math

import app.scripts.summer.testing.regents_scheduling.return_exambook as return_exambook


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
    exams_offered = regents_calendar_df["CourseCode"]
    registrations_df = registrations_df[registrations_df["Course"].isin(exams_offered)]

    # ## exam_info

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    testing_accommodations_df = return_student_accommodations(request, form)

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

    registrations_df["AM_Conflict?"] = registrations_df.apply(
        return_am_conflict_status, axis=1
    )
    registrations_df["PM_Conflict?"] = registrations_df.apply(
        return_pm_conflict_status, axis=1
    )
    registrations_df["AM_PM_Conflict?"] = registrations_df.apply(
        return_am_pm_conflict_status, axis=1
    )

    ## attach default section
    merge_cols = [
        "SWD?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",
        "AM_Conflict?",
        "PM_Conflict?",
        "AM_PM_Conflict?",
    ]
    dff = section_properties_df.drop_duplicates(subset=["Type"])
    dff = dff[dff["Section"] > 2]
    df = registrations_df.merge(dff, on=merge_cols, how="left").fillna(1)

    ## apply special assignment rules
    df["Section"] = df.apply(assign_scribe_kids, axis=1)
    df["Section"] = df.apply(reassign_gen_ed, axis=1)
    df["Type"] = df["Type"].apply(
        lambda x: "GenEd" if x == "GenEd_AM_PM_Conflict" else x
    )
    df["index"] = df.groupby(["Course", "Section"]).cumcount() + 1

    students_per_section_pvt = pd.pivot_table(
        df, index=["Course", "Section"], values="StudentID", aggfunc="count"
    ).reset_index()

    students_per_section_pvt["Capacity"] = students_per_section_pvt.apply(
        determine_capacity, axis=1
    )
    students_per_section_pvt["NumberOfSections"] = students_per_section_pvt.apply(
        determine_number_of_sections, axis=1
    )

    students_df = df.merge(
        students_per_section_pvt[["Course", "Section", "NumberOfSections"]],
        on=["Course", "Section"],
    ).fillna(1)

    students_df["FinalSection"] = students_df.apply(set_final_section, axis=1)
    students_df["GradeLevel"] = ""
    students_df["OfficialClass"] = ""
    students_df["Action"] = "Update"
    output_cols_needed = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "FinalSection",
        "Action",
    ]

    exambook_df, room_check_df = return_exambook.main(students_df)

    # return room_check_df

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    exambook_df.to_excel(writer, sheet_name="ExamBook", index=False)
    room_check_df.to_excel(writer, sheet_name="RoomCheck")
    students_df[students_df["FinalSection"] == 1].to_excel(
        writer, sheet_name="Check", index=False
    )
    students_df[output_cols_needed].to_excel(
        writer, sheet_name="StudentFileEdit", index=False
    )
    writer.close()
    f.seek(0)

    return f


def set_final_section(student_row):
    NumberOfSections = student_row["NumberOfSections"]
    section = student_row["Section"]
    if NumberOfSections == 1:
        return section

    index = student_row["index"]
    offset = (index) % NumberOfSections

    return section + offset


def determine_number_of_sections(course_section):
    num_of_students = course_section["StudentID"]
    course = course_section["Course"]
    section = course_section["Section"]

    GEN_ED_TARGET = 34
    SPED_TARGET = 15

    if section < 20:
        SECTION_TYPE = "GENED"
        CURRENT_TARGET = GEN_ED_TARGET
        CAP = 45
        if section < 15:
            MAX_NUMBER_OF_SECTIONS = 12
        else:
            MAX_NUMBER_OF_SECTIONS = 1
    else:
        SECTION_TYPE = "SPED"
        CURRENT_TARGET = SPED_TARGET
        CAP = 25
        MAX_NUMBER_OF_SECTIONS = 1
        if section in [20, 30, 40]:
            MAX_NUMBER_OF_SECTIONS = 2

    BASE_SHOWUP_RATE = 0.6

    if course == "SXRUG":
        BASE_SHOWUP_RATE = 0.4
        CAP = 50

    if num_of_students <= CURRENT_TARGET / BASE_SHOWUP_RATE:
        return 1

    for num_of_sections in range(1, 10):
        num_per_section = math.ceil(num_of_students / num_of_sections)
        for offset in range(0, 5):
            if num_per_section <= (CAP + offset):
                return min(num_of_sections, MAX_NUMBER_OF_SECTIONS)


def determine_capacity(course_section):
    num_of_students = course_section["StudentID"]
    course = course_section["Course"]
    section = course_section["Section"]

    GEN_ED_TARGET = 34
    SPED_TARGET = 15

    if section < 20:
        SECTION_TYPE = "GENED"
        CURRENT_TARGET = GEN_ED_TARGET
        CAP = 45
    else:
        SECTION_TYPE = "SPED"
        CURRENT_TARGET = SPED_TARGET
        CAP = 25

    BASE_SHOWUP_RATE = 0.6

    if course == "SXRUG":
        BASE_SHOWUP_RATE = 0.4
        CAP = 50

    if num_of_students <= CURRENT_TARGET:
        return CURRENT_TARGET

    if num_of_students <= CURRENT_TARGET / BASE_SHOWUP_RATE:
        return math.ceil(CURRENT_TARGET / BASE_SHOWUP_RATE)

    for num_of_sections in range(1, 10):
        num_per_section = math.ceil(num_of_students / num_of_sections)
        for offset in range(0, 5):
            if num_per_section <= (CAP + offset):
                return num_per_section


def assign_scribe_kids(student_row):
    is_scribe = student_row["scribe?"]
    if not is_scribe:
        return student_row["Section"]
    elif student_row["AM_Conflict?"]:
        return 61
    elif student_row["AM_PM_Conflict?"]:
        return 62
    elif student_row["PM_Conflict?"]:
        return 63
    return 60


def reassign_gen_ed(student_row):
    current_section = student_row["Section"]
    dbn = student_row["Sending school"]
    if current_section == 17:
        return 3
    return current_section


def return_am_conflict_status(student_row):
    num_of_am_exams = student_row["AM_#_of_exams_on_day"]
    num_of_pm_exams = student_row["PM_#_of_exams_on_day"]
    total_num_of_exams = student_row["Total_#_of_exams_on_day"]

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams == 0 and num_of_am_exams > 1:
        return True
    return False


def return_pm_conflict_status(student_row):
    num_of_am_exams = student_row["AM_#_of_exams_on_day"]
    num_of_pm_exams = student_row["PM_#_of_exams_on_day"]
    total_num_of_exams = student_row["Total_#_of_exams_on_day"]

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams > 1 and num_of_am_exams == 1:
        return True
    return False


def return_am_pm_conflict_status(student_row):
    num_of_am_exams = student_row["AM_#_of_exams_on_day"]
    num_of_pm_exams = student_row["PM_#_of_exams_on_day"]
    total_num_of_exams = student_row["Total_#_of_exams_on_day"]

    if total_num_of_exams == 1:
        return False
    if num_of_pm_exams >= 1 and num_of_am_exams >= 1:
        return True
    return False


def return_student_accommodations(request, form):
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
    exam_cols = ["Alg1", "ELA", "Alg2", "Global", "Chem", "ES", "USH", "Geo", "LE"]

    df = df[df[exam_cols].any(axis=1)]

    pvt_tbl = pd.pivot_table(
        df, index="school_name", values="StudentID", aggfunc="count"
    ).reset_index()

    print(pvt_tbl.sort_values(by="StudentID"))
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
    df["SWD?"] = df.apply(check_SWD_flag, axis=1)

    return df[cols]


def check_SWD_flag(student_row):
    SWD_cols = [
        "SWD?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",
    ]
    return student_row[SWD_cols].any()
