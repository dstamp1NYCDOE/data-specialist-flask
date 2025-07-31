import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

    dataframe_dict = {}

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

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

    regents_courses = regents_calendar_df["CourseCode"]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_01_df[
        ["StudentID", "LastName", "FirstName", "Course", "Grade", "Section"]
    ]
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Course"].isin(regents_courses)]
    cr_1_08_df["OldSection"] = cr_1_08_df["Section"]
    registrations_df = cr_1_08_df[cr_1_08_df["Course"].isin(regents_courses)]
    registrations_df["senior?"] = registrations_df["Grade"].apply(lambda x: x == "12")
    registrations_df["LabEligible?"] = registrations_df["Section"].apply(
        lambda x: x != 88
    )

    registrations_df = registrations_df.drop(columns=["Section"])

    # ## exam_info

    ## attach exam info to registrations
    registrations_df = registrations_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "rosters_and_grades", year_and_semester=year_and_semester
    )
    rosters_df = utils.return_file_as_df(filename)
    
    rosters_df = rosters_df[["StudentID", "Course", "Teacher1"]].drop_duplicates(
        subset=["StudentID", "Course"]
    )
    rosters_df["CulminatingCourse"] = rosters_df["Course"].apply(lambda x: x[0:5])
    rosters_df = rosters_df[["StudentID", "CulminatingCourse", "Teacher1"]]

    registrations_df = registrations_df.merge(
        rosters_df, on=["StudentID", "CulminatingCourse"], how="left"
    ).fillna("")

    ## attach testing accommodations info
    filename = utils.return_most_recent_report_by_semester(
        files_df,
        "testing_accommodations_processed",
        year_and_semester=year_and_semester,
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

    ## swap in "distributed" for Teacher1 name for those exams to minimize number of sections
    def swap_teacher_name(row):
        if row["DistributedScoring"] == True:
            return "Distributed"
        elif row["Section"] == 3:
            return "AAA"
        elif row["Teacher1"] == "":
            return "AAA"
        else:
            return row["Teacher1"]

    registrations_df["Teacher1"] = registrations_df.apply(swap_teacher_name, axis=1)


    ## adjust sections based on enrollment

    registrations = []

    ENL_SECTIONS = [20, 25, 30, 34, 35, 54, 55]
    LAB_INELIGIBLE_SECTION = 88
    for exam, exam_registrations_df in registrations_df.groupby("Course"):
        ## speciality gen ed sections 
        speciality_gen_ed_registrations_df =  exam_registrations_df[exam_registrations_df['Section']<5]
        ## gen ed sections 
        gen_ed_registrations_df = exam_registrations_df[(exam_registrations_df['Section']>=5) & (exam_registrations_df['Section']<18)]
        ## small group sections 
        small_group_sections_df = exam_registrations_df[(exam_registrations_df['Section']!=LAB_INELIGIBLE_SECTION) &(exam_registrations_df['Section']>=18) & (~exam_registrations_df['Section'].isin(ENL_SECTIONS))]
        ## ENL sections
        enl_registrations_df = exam_registrations_df[exam_registrations_df['Section'].isin(ENL_SECTIONS)] 
        ## lab ineligible registrations
        lab_ineligible_registrations =  exam_registrations_df[exam_registrations_df['Section']==LAB_INELIGIBLE_SECTION]

        for index, student in lab_ineligible_registrations.iterrows():
            student["NewSection"] = 88
            registrations.append(student)

        for section, section_df in enl_registrations_df.groupby("Section"):
            for teacher, students_by_teacher_df in section_df.groupby("Teacher1"):
                max_capacity = 33
                current_capacity = 1   
                current_section = section          
                for index, student in students_by_teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)

        for section, section_df in small_group_sections_df.groupby("Section"):
            grouped = section_df.groupby("Teacher1")
            sorted_group_names = (
                grouped.size().sort_values(ascending=False).index.tolist()
            )
            for teacher in sorted_group_names:
                students_by_teacher_df = grouped.get_group(teacher)
                max_capacity = 15
                current_capacity = 1   
                current_section = section          
                for index, student in students_by_teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)

        for section, section_df in speciality_gen_ed_registrations_df.groupby("Section"):
            grouped = section_df.groupby("Teacher1")
            sorted_group_names = (
                grouped.size().sort_values(ascending=False).index.tolist()
            )
            max_capacity = 33
            current_capacity = 1  
            for teacher in sorted_group_names:
                students_by_teacher_df = grouped.get_group(teacher)
     
                current_section = section          
                for index, student in students_by_teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)
        
        # num of available seats from the speciality gen ed sections
        num_of_gened_speciality_students = len(speciality_gen_ed_registrations_df)
        num_of_remaining_seats = 33 - num_of_gened_speciality_students % 33
        
        ## first, split the gened sections grouped by teacher into a dataframe that is a multiple of 33 and the remainder that isn't

        multiple_of_33_dfs = []
        remainder_dfs = []

        if len(gen_ed_registrations_df) > 0:
            for teacher, registrations_by_teacher_df in gen_ed_registrations_df.groupby("Teacher1"):
                total_rows = len(registrations_by_teacher_df)
                if total_rows < 33:
                    df_multiple_33 = pd.DataFrame(columns=registrations_by_teacher_df.columns)  # Empty dataframe with same columns
                    df_remainder = registrations_by_teacher_df.copy()
                else:
                    # Find the largest multiple of 33 that doesn't exceed total_rows
                    multiple_33_rows = (total_rows // 33) * 33
                    
                    # Split the dataframe
                    df_multiple_33 = registrations_by_teacher_df.iloc[:multiple_33_rows].copy()
                    print(df_multiple_33)
                    df_remainder = registrations_by_teacher_df.iloc[multiple_33_rows:].copy()
                
                multiple_of_33_dfs.append(df_multiple_33)
                remainder_dfs.append(df_remainder)
            
            multiple_of_33_dfs = pd.concat(multiple_of_33_dfs, ignore_index=True)
            remainder_dfs = pd.concat(remainder_dfs, ignore_index=True)

            current_capacity = num_of_remaining_seats
            max_capacity = 33
            current_section = 5
            
            grouped = remainder_dfs.groupby("Teacher1")
            sorted_group_names = (
                    grouped.size().sort_values(ascending=False).index.tolist()
                )
            for teacher in sorted_group_names:
                students_by_teacher_df = grouped.get_group(teacher) 
                for index, student in students_by_teacher_df.iterrows():
                    if current_capacity < max_capacity:
                        current_capacity += 1
                        section = current_section
                    else:
                        current_capacity = 1
                        current_section += 1

                    student["NewSection"] = section
                    registrations.append(student)        


            for section, section_df in multiple_of_33_dfs.groupby("Section"):
                grouped = section_df.groupby("Teacher1")
                sorted_group_names = (
                    grouped.size().sort_values(ascending=False).index.tolist()
                )
                max_capacity = 33
                current_capacity = 1
                current_section = section + 4  
                for teacher in sorted_group_names:
                    students_by_teacher_df = grouped.get_group(teacher)          
                    for index, student in students_by_teacher_df.iterrows():
                        if current_capacity < max_capacity:
                            current_capacity += 1
                            section = current_section
                        else:
                            current_capacity = 1
                            current_section += 1

                        student["NewSection"] = section
                        registrations.append(student)
        
        

    registrations_df = pd.DataFrame(registrations)


    # return ''




    # for (exam, section), exam_section_df in registrations_df.groupby(
    #     ["Course", "Section"]
    # ):

    #     num_of_students = len(exam_section_df)
    #     if section < 5:
    #         max_capacity = 33
    #     elif section < 18 or section in [20, 25, 30, 34, 35, 54, 55]:
    #         max_capacity = return_gen_ed_section_capacity(exam, month, num_of_students)
    #     elif section == 88:
    #         max_capacity = 99
    #     else:
    #         max_capacity = 15

    #     current_capacity = len(exam_section_df)

    #     if current_capacity <= max_capacity:
    #         for index, student in exam_section_df.iterrows():
    #             student["NewSection"] = section
    #             registrations.append(student)
    #     else:
    #         current_capacity = 1
    #         current_section = section


    #         exam_teachers = exam_section_df["Teacher1"].unique()

    #         grouped = exam_section_df.groupby("Teacher1")
    #         sorted_group_names = (
    #             grouped.size().sort_values(ascending=False).index.tolist()
    #         )

    #         for teacher in sorted_group_names:             
    #             teacher_df = grouped.get_group(teacher)
    #             for index, student in teacher_df.iterrows():
    #                 if current_capacity < max_capacity:
    #                     current_capacity += 1
    #                     section = current_section
    #                 else:
    #                     current_capacity = 1
    #                     current_section += 1

    #                 student["NewSection"] = section
    #                 registrations.append(student)
    #             if teacher == "":
    #                 pass
    #             else:
    #                 if current_section < 19:
    #                     if teacher != "AAA":
    #                         current_section += 1

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

    dataframe_dict["STARS"] = registrations_df[
        registrations_df["OldSection"] != registrations_df["NewSection"]
    ][stars_upload_cols]
    STARS_reset_df = registrations_df.copy()
    STARS_reset_df["NewSection"] = STARS_reset_df["NewSection"].apply(
        lambda x: 88 if x == 88 else 1
    )
    dataframe_dict["STARS-Reset"] = STARS_reset_df[stars_upload_cols]
    students_taking_exams_lst = registrations_df["StudentID"].unique()

    accommodations_to_check = testing_accommodations_df[
        testing_accommodations_df["StudentID"].isin(students_taking_exams_lst)
    ]
    dataframe_dict["AccommodationsToCheck"] = accommodations_to_check

    dataframe_dict["Review"] = registrations_df[
        (registrations_df["Course"] == "HXRCE")
        & (registrations_df["Teacher1"] == "Trapani, J.")
    ]

    return dataframe_dict


def return_gen_ed_section_capacity(exam_code, month, num_of_students):
    return 33
    if month == "January":
        if exam_code[0] == "E":
            return calculate_class_size(num_of_students)
        else:
            return calculate_class_size(num_of_students, max_class_size=40)
    if month == "June":
        if exam_code[0] == "E":
            return calculate_class_size(num_of_students, max_class_size=40)
        else:
            return calculate_class_size(num_of_students)


def calculate_class_size(total_students, max_class_size=33, ideal_class_size=33):
    """
    Calculate the optimal class size given total number of students.

    Rules:
    - Ideal class size is ideal_class_size
    - Maximum allowed class size is 34, but only if remainder equals number of sections at ideal_class_size
    - If remainder > number of sections at ideal_class_size, add more sections to balance
    - Minimize number of sections while avoiding very small last sections

    Returns the maximum class size that will be used.
    """
    if total_students <= max_class_size:
        return ideal_class_size

    # Start with sections of ideal_class_size and see what remainder we get
    sections_at_ideal = total_students // ideal_class_size
    remainder = total_students % ideal_class_size

    # If remainder == 0, all sections are ideal_class_size
    if remainder == 0:
        return ideal_class_size

    # If remainder equals the number of sections, we can go to max_class_size
    if remainder == sections_at_ideal:
        return max_class_size

    # If remainder < number of sections, we can distribute evenly at ideal_class_size and max_class_size
    if remainder < sections_at_ideal:
        return max_class_size

    # If remainder > number of sections, we need more sections to balance
    # Find the minimum number of sections where all are reasonably balanced
    min_sections = sections_at_ideal + 1

    while True:
        base_size = total_students // min_sections
        section_remainder = total_students % min_sections

        # If base_size > max_class_size, we need even more sections
        if base_size > max_class_size:
            min_sections += 1
            continue

        # Check if this gives us a reasonable distribution
        if section_remainder == 0:
            return base_size
        else:
            return base_size + 1


def remove_lab_ineligible(row):
    course = row["CourseCode"]
    LabEligible = row["LabEligible?"]
    if course[0] == "S" and LabEligible == False:
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

    if scribe:
        return 89
    if Technology:
        return 87

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
