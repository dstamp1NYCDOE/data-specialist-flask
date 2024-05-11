import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session


def main():
    school_year = session["school_year"]
    term = session["term"]

    dataframe_dict = {}

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

    filename = utils.return_most_recent_report(files_df, "1_08")
    registrations_df = utils.return_file_as_df(filename)
    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "Grade",
        "senior?",
    ]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    regents_calendar_df["Curriculum"] = regents_calendar_df["CulminatingCourse"].str[
        0:2
    ]
    section_properties_df = pd.read_excel(path, sheet_name="SectionProperties")

    registrations_df["senior?"] = registrations_df["Grade"].apply(lambda x: x == "12")

    ## drop inactivies
    registrations_df = registrations_df[registrations_df["Status"] == True]
    registrations_df = registrations_df[cols]

    ## get lab eligibility
    filename = utils.return_most_recent_report(files_df, "lab_eligibility")
    lab_eligibility_df = utils.return_file_as_df(filename)

    # ## exam_info

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    ## attach lab eligibility
    registrations_df = registrations_df.merge(
        lab_eligibility_df, on=["StudentID", "Curriculum"], how="left"
    )
    print(registrations_df)

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    # rosters_df = rosters_df[rosters_df['Term']==f"S{term}"]
    rosters_df = rosters_df[["StudentID", "Course", "Teacher1"]].drop_duplicates(
        subset=["StudentID", "Course"]
    )
    rosters_df["CulminatingCourse"] = rosters_df["Course"].apply(lambda x: x[0:5])
    rosters_df = rosters_df[["StudentID", "CulminatingCourse", "Teacher1"]]

    registrations_df = registrations_df.merge(
        rosters_df, on=["StudentID", "CulminatingCourse"], how="left"
    ).fillna("")

    ## attach testing accommodations info
    filename = utils.return_most_recent_report(
        files_df, "testing_accommodations_processed"
    )
    testing_accommodations_df = utils.return_file_as_df(filename)
    testing_accommodations_df = testing_accommodations_df.drop_duplicates(
        keep="first", subset=["StudentID"]
    )
    testing_accommodations_df["SWD?"] = testing_accommodations_df["Grouping"].apply(
        lambda x: x in ["HSFI", "D75", "504s"]
    )
    testing_accommodations_df["D75?"] = testing_accommodations_df["Grouping"].apply(
        lambda x: x in ["D75"]
    )
    condition_cols = [
        "StudentID",
        "SWD?",
        "D75?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "one_on_one?",
        "Technology?",
        "large_print?",
    ]
    testing_accommodations_df = testing_accommodations_df[condition_cols]

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

    ## flag double time students with multiple exams on a day
    double_time_multiple_exams = registrations_df[
        registrations_df["double_time?"]
        & (registrations_df["Total_#_of_exams_on_day"] > 1)
    ]
    if len(double_time_multiple_exams):
        dataframe_dict["double_time_multiple_exams"] = double_time_multiple_exams

    ## output sections needed
    flags_cols = [
        "senior?",
        "SWD?",
        "D75?",
        "ENL?",
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "one_on_one?",
        "Technology?",
        "large_print?",
        "Conflict?",
    ]

    sections_df = (
        registrations_df[flags_cols].drop_duplicates().sort_values(by=flags_cols)
    )
    sections_df["Section"] = sections_df.apply(return_section_number, axis=1)
    dataframe_dict["sections"] = sections_df.merge(
        section_properties_df, on=["Section"], how="left"
    )

    ## attach default_section_number
    registrations_df = registrations_df.merge(sections_df, on=flags_cols)
    registrations_df["Section"] = registrations_df.apply(remove_lab_ineligible, axis=1)

    ## number_of_students_per_section
    registrations_df["running_total"] = (
        registrations_df.sort_values(by=["Teacher1", "LastName", "FirstName"])
        .groupby(["Course", "Section"])["StudentID"]
        .cumcount()
        + 1
    )

    ## adjust sections based on enrollment

    registrations = []
    for (exam, section), exam_section_df in registrations_df.groupby(
        ["Course", "Section"]
    ):
        if section < 18 or section in [20, 25, 30, 34, 35, 54, 55]:
            max_capacity = return_gen_ed_section_capacity(exam, month)
        elif section == 88:
            max_capacity = 99
        else:
            max_capacity = 15

        current_capacity = len(exam_section_df)

        if current_capacity <= max_capacity:
            for index, student in exam_section_df.iterrows():
                student["NewSection"] = section
                registrations.append(student)
        else:
            current_capacity = 1
            # current_section = section - 1
            current_section = section

            for teacher, teacher_df in exam_section_df.groupby("Teacher1"):
                for index, student in teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)
                if teacher == "":
                    pass
                else:
                    if current_section < 19:
                        current_section += 1

    registrations_df = pd.DataFrame(registrations)
    registrations_df = registrations_df.merge(
        section_properties_df, on=["Section"], how="left"
    )

    registrations_pvt_tbl = pd.pivot_table(
        registrations_df,
        index=["Course", "NewSection", "Teacher1"],
        values="StudentID",
        aggfunc="count",
    ).reset_index()

    # output_filename = "output/registrations.xlsx"
    # writer = pd.ExcelWriter(output_filename)
    registrations_df = registrations_df.sort_values(
        by=["Day", "Time", "Course", "NewSection"]
    )
    print(registrations_df.columns)
    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "ExamTitle",
        "Teacher1",
        "NewSection",
        "Type",
    ]
    dataframe_dict["registrations"] = registrations_df[cols]
    dataframe_dict["pivot"] = registrations_pvt_tbl

    registrations_df["Action"] = "Replace"
    registrations_df["GradeLevel"] = ""
    registrations_df["OfficialClass"] = ""
    stars_upload_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "NewSection",
        "Action",
    ]
    dataframe_dict["STARS"] = registrations_df[stars_upload_cols]
    students_taking_exams_lst = registrations_df["StudentID"].unique()

    accommodations_to_check = testing_accommodations_df[
        testing_accommodations_df["StudentID"].isin(students_taking_exams_lst)
    ]
    dataframe_dict["AccommodationsToCheck"] = accommodations_to_check

    return dataframe_dict


def return_gen_ed_section_capacity(exam_code, month):

    if month == "January":
        if exam_code[0] == "E":
            return 34
        else:
            return 40
    if month == "June":
        if exam_code[0] == "E":
            return 40
        else:
            return 34


def remove_lab_ineligible(row):
    course = row["CourseCode"]
    LabEligible = row["LabEligible"]
    if course[0] == "S" and LabEligible == 0:
        return 88
    else:
        return row["Section"]


def return_section_number(row):

    senior = row["senior?"]
    SWD = row["SWD?"]
    D75 = row["D75?"]
    ENL = row["ENL?"]

    time_and_a_half = row["time_and_a_half?"]
    double_time = row["double_time?"]
    QR = row["read_aloud?"]
    conflict = row["Conflict?"]

    scribe = row["scribe?"]
    one_on_one = row["one_on_one?"]
    Technology = row["Technology?"]
    large_print = row["large_print?"]

    if not SWD and not D75 and not ENL:
        if conflict:
            if senior:
                return 2
            else:
                return 3
        else:
            if senior:
                return 4
            else:
                return 5

    if scribe or Technology or one_on_one:
        return 89

    temp_str = ""
    for attribute in [senior, conflict, ENL, QR, time_and_a_half, double_time]:
        if attribute:
            temp_str += "1"
        else:
            temp_str += "0"

    section_dict = {
        "000010": 24,
        "100010": 31,
        "001010": 32,
        "101010": 33,
        "001000": 34,
        "101000": 35,
        "000001": 36,
        "100001": 37,
        "001001": 38,
        "101001": 39,
        "000110": 40,
        "100110": 43,
        "001110": 44,
        "101110": 45,
        "000101": 46,
        "100101": 47,
        "001101": 48,
        "101101": 49,
        "010010": 50,
        "110010": 51,
        "011010": 52,
        "111010": 53,
        "011000": 54,
        "111000": 55,
        "010001": 56,
        "110001": 57,
        "011001": 58,
        "111001": 59,
        "010110": 62,
        "110110": 63,
        "011110": 64,
        "111110": 65,
        "010101": 66,
        "110101": 67,
        "011101": 68,
        "111101": 69,
    }

    return section_dict.get(temp_str, 20)
