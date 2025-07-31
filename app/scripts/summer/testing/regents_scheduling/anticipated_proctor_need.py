import pandas as pd
import numpy as np
import os
import math
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    exams_in_order = regents_calendar_df.sort_values(by=["Day", "Time", "ExamTitle"])[
        "ExamTitle"
    ]

    student_exam_registration = request.files[
        form.combined_regents_registration_spreadsheet.name
    ]
    df_dict = pd.read_excel(student_exam_registration, sheet_name=None)

    sheets_to_ignore = ["Directions", "HomeLangDropdown", "YABC"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")



    walkins_df = df

    walkins_df = walkins_df.dropna(subset=["StudentID"])
    walkins_df["GradeLevel"] = ""
    walkins_df["OfficialClass"] = ""
    walkins_df["Section"] = 1

    exams = [
        ("ELA", "EXRCG"),
        ("Alg1", "MXRFG"),
        ("Global", "HXRCG"),
        ("Alg2", "MXRNG"),
        ("USH", "HXRKG"),
        ("ES", "SXRUG"),
        ("Chem", "SXRXG"),
        ("Geo", "MXRJG"),
        ("LE", "SXRKG"),
        ("Bio", "SXR3G"),
        ("ESS", "SXR2G"),
    ]

    output_df_lst = []
    output_cols_needed = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "Section",
        "Action",
        "school_name",
    ]

    for exam, exam_code in exams:
        for status, action in [(True, "Add")]:
            to_register_df = walkins_df[walkins_df[exam] == status]
            to_register_df["Course"] = exam_code
            to_register_df["Action"] = action
            to_register_df = to_register_df[output_cols_needed]
            output_df_lst.append(to_register_df)
    
    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "school_name",
    ]
    registrations_df = pd.concat(output_df_lst)[cols]


    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    # regents_calendar_df["exam_num"] = (
    #     regents_calendar_df.groupby(["Day", "Time"])["CourseCode"].cumcount() + 1
    # )
    section_properties_df = pd.read_excel(path, sheet_name="SummerSectionProperties")
    rooms_list = [
        "AM1_ROOM",
        "AM2_ROOM",
        "PM1_ROOM",
        "PM2_ROOM",
        "AM3_ROOM",
        "PM3_ROOM",
    ]
    replacement_dict = {room: 202 for room in rooms_list}
    section_properties_df = section_properties_df.fillna(replacement_dict)
    rooms_df = section_properties_df[
        [
            "Section",
            "AM1_ROOM",
            "AM2_ROOM",
            "PM1_ROOM",
            "PM2_ROOM",
            "AM3_ROOM",
            "PM3_ROOM",
        ]
    ]
    rooms_df = rooms_df.rename(columns={"Section": "FinalSection"})


    ## keep only exams offered
    exams_offered = regents_calendar_df["CourseCode"]
    registrations_df = registrations_df[registrations_df["Course"].isin(exams_offered)]

    # ## exam_info

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    registrations_df["exam_id"] = registrations_df["Time"] + registrations_df[
        "exam_num"
    ].astype(str)

    testing_accommodations_df = return_student_accommodations(request, form)

    registrations_df = registrations_df.merge(
        testing_accommodations_df, on=["StudentID"], how="left"
    ).fillna(False)

    exam_sequence_by_student_by_day_pvt = pd.pivot_table(
        registrations_df.sort_values(by=["Time", "exam_num"]),
        index=["StudentID", "Day"],
        values="exam_id",
        aggfunc=lambda x: "_".join(str(v) for v in x),
    )
    exam_sequence_by_student_by_day_pvt["exam_id"] = (
        exam_sequence_by_student_by_day_pvt["exam_id"].apply(
            lambda x: x if x.count("_") > 0 else "_"
        )
    )
    exam_sequence_by_student_by_day_pvt = (
        exam_sequence_by_student_by_day_pvt.reset_index()
    )
    exam_sequence_by_student_by_day_pvt["exam_id"] = (
        exam_sequence_by_student_by_day_pvt["exam_id"]
    ).apply(remove_exam3_from_exam_str)
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

    registrations_df = (
        registrations_df.drop(columns=["exam_id"])
        .merge(exam_sequence_by_student_by_day_pvt, on=["StudentID", "Day"], how="left")
        .fillna("")
    )

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
        "AM_Conflict?",
        "PM_Conflict?",
        "AM_PM_Conflict?",
        "exam_id",
    ]
    dff = section_properties_df.drop_duplicates(subset=["Type", "exam_id"])
    dff = dff[dff["Section"] >= 2]

    dff = dff.drop(
        columns=["AM1_ROOM", "AM2_ROOM", "PM1_ROOM", "PM2_ROOM", "AM3_ROOM", "PM3_ROOM"]
    )
    df = registrations_df.merge(dff, on=merge_cols, how="left").fillna(1)

    ## apply special assignment rules
    df["Section"] = df.apply(assign_scribe_kids, axis=1)
    df["Section"] = df.apply(reassign_gen_ed, axis=1)
    df["Section"] = df.apply(reassign_gen_ed_am_pm_conflicts, axis=1)

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

    students_df["FinalSection"] = students_df.apply(set_final_section, axis=1).fillna(
        202
    )
    students_df = students_df.merge(rooms_df, on="FinalSection", how="left")

    students_df["GradeLevel"] = ""
    students_df["OfficialClass"] = ""
    students_df["Action"] = "Replace"

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


    ## flag students with more than >2 exams on one day or 2+ exams in PM
    overenrolled_df = students_df[
        (students_df["PM_#_of_exams_on_day"] >= 2)
        | (students_df["Total_#_of_exams_on_day"] > 2)
    ]
    overenrolled_output_cols = [
        "school_name",
        "StudentID",
        "LastName",
        "FirstName",
        "Day",
        "Time",
        "Course",
        "ExamTitle",
        "PM_#_of_exams_on_day",
        "Total_#_of_exams_on_day",
    ]
    overenrolled_df = overenrolled_df[overenrolled_output_cols].sort_values(
        by=["school_name", "LastName", "FirstName"]
    )

    ## flag double time students taking two exams on one day
    two_exam_double_time_df = students_df[
        (students_df["double_time?"] == True)
        & (students_df["Total_#_of_exams_on_day"] >= 2)
    ]
    two_exam_double_time_df = two_exam_double_time_df[
        overenrolled_output_cols
    ].sort_values(by=["school_name", "LastName", "FirstName"])



    f = BytesIO()
    writer = pd.ExcelWriter(f)

    students_df[students_df["FinalSection"] == 1].to_excel(
        writer, sheet_name="Check", index=False
    )
    overenrolled_df.to_excel(writer, sheet_name="Overenrolled", index=False)
    two_exam_double_time_df.to_excel(
        writer, sheet_name="MultipleDoubleTimeExams", index=False
    )

    students_df[students_df["special_notes"] != False].sort_values(
        by=["school_name", "StudentID"]
    ).to_excel(writer, sheet_name="IEP_CHECK", index=False)

    students_df.to_excel(writer, sheet_name="StudentsDataDump", index=False)
    writer.close()
    f.seek(0)

    return f


def remove_exam3_from_exam_str(exam_str):
    if "3" in exam_str:
        ## CHEM = 3, ES = 2, USH = 1
        swap_dict = {
            "AM1_AM3": "AM1_AM2",
            # "AM1_AM3_PM2": "",
            "AM3_PM1": "AM1_PM1",
            # "AM3_PM1_PM2": "",
            "AM3_PM2": "AM2_PM2",
        }
        return swap_dict.get(exam_str, exam_str)
    else:
        return exam_str


def set_final_section(student_row):
    NumberOfSections = student_row["NumberOfSections"]
    section = student_row["Section"]
    index = student_row["index"]
    exam_code = student_row["Course"]

    if NumberOfSections == 1:
        return section

    if section == 19:
        extra_space = 8
        index = student_row["index"] - extra_space
        if index <= 0:
            return section
    if section == 2:
        extra_space = 5
        if exam_code in ["EXRCG", "HXRKG"]:
            extra_space = 15
        if exam_code in ["HXRCG"]:
            extra_space = 10

        if student_row["index"] < extra_space * NumberOfSections:
            offset = (index) % (NumberOfSections - 1)
            return section + offset + 1

    offset = (index) % NumberOfSections

    return section + offset


def determine_number_of_sections(course_section):
    num_of_students = course_section["StudentID"]
    course = course_section["Course"]
    section = course_section["Section"]

    GEN_ED_TARGET = 34
    SPED_TARGET = 15

    if section < 14:
        SECTION_TYPE = "GENED"
        CURRENT_TARGET = GEN_ED_TARGET
        CAP = 45
        if section < 11:
            MAX_NUMBER_OF_SECTIONS = 9
        else:
            MAX_NUMBER_OF_SECTIONS = 1
    else:
        SECTION_TYPE = "SPED"
        CURRENT_TARGET = SPED_TARGET
        CAP = 25
        MAX_NUMBER_OF_SECTIONS = 1
        if section in [19, 20]:
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

    if section < 11:
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
        return 16
    elif student_row["AM_PM_Conflict?"]:
        return 17
    elif student_row["PM_Conflict?"]:
        return 18
    return 15


def reassign_gen_ed_am_pm_conflicts(student_row):
    current_section = student_row["Section"]
    if (
        student_row["AM_#_of_exams_on_day"] < 2
        and student_row["PM_#_of_exams_on_day"] < 2
    ):
        if student_row["SWD?"] == False and student_row["ENL?"] == False:
            return 2
    return current_section


def reassign_gen_ed(student_row):
    current_section = student_row["Section"]
    if current_section == 13:
        return 2
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

    sheets_to_ignore = ["Directions", "HomeLangDropdown", "YABC"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")
    df = df.drop_duplicates(subset=["StudentID"])

    ## what has exams registered for
    exam_cols = ["Alg1", "ELA", "Alg2", "Global", "Chem", "ES", "USH", "Geo", "LE"]

    df = df[df[exam_cols].any(axis=1)]

    pvt_tbl = pd.pivot_table(
        df, index="school_name", values="StudentID", aggfunc="count"
    ).reset_index()

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
