import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

def main():
    school_year = session["school_year"]
    term = session["term"]
    
    if term == 1:
        month = "January"
    if term == 2:
        month = "June"

    filename = utils.return_most_recent_report(files_df, "1_08")
    registrations_df =  utils.return_file_as_df(filename)
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


    
    registrations_df["senior?"] = registrations_df["Grade"].apply(lambda x: x == "12")

    ## drop inactivies
    registrations_df = registrations_df[registrations_df["Status"] == True]
    registrations_df = registrations_df[cols]

    # ## exam_info


    ## attach exam info to registrations
    registrations_df = registrations_df.merge(regents_calendar_df, left_on=["Course"], right_on=['CourseCode'], how="left")

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    # rosters_df = rosters_df[rosters_df['Term']==f"S{term}"]
    rosters_df = rosters_df[["StudentID", "Course", "Teacher1"]].drop_duplicates()    
    rosters_df["CulminatingCourse"] = rosters_df["Course"].apply(lambda x: x[0:5])
    rosters_df = rosters_df[['StudentID','CulminatingCourse','Teacher1']]
    

    registrations_df = registrations_df.merge(
        rosters_df, on=["StudentID", "CulminatingCourse"], how="left"
    ).fillna("")
    return registrations_df

    ## attach testing accommodations info
    testing_accommodations_filename = f"data/{year_term}/testing_accommodations.csv"
    testing_accommodations_df = pd.read_csv(testing_accommodations_filename)
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
    print(num_of_exams_by_student_by_day)

    registrations_df = registrations_df.merge(
        num_of_exams_by_student_by_day, on=["StudentID", "Day"], how="left"
    ).fillna(0)

    ## flag double time students with multiple exams on a day
    double_time_multiple_exams = registrations_df[
        registrations_df["double_time?"]
        & (registrations_df["Total_#_of_exams_on_day"] > 1)
    ]
    if len(double_time_multiple_exams):
        double_time_multiple_exams_filename = (
            f"output/double_time_multiple_exams.xlsx"
        )
        double_time_multiple_exams.to_excel(
            double_time_multiple_exams_filename, index=False
        )

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
    sections_df.to_excel("output/sections.xlsx")

    ## attach default_section_number
    registrations_df = registrations_df.merge(sections_df, on=flags_cols)

    ## number_of_students_per_section
    registrations_df["running_total"] = (
        registrations_df.sort_values(by=["Teacher", "LastName", "FirstName"])
        .groupby(["Course", "Section"])["StudentID"]
        .cumcount()
        + 1
    )

    ## adjust sections based on enrollment



    registrations = []
    for (exam, section), exam_section_df in registrations_df.groupby(
        ["Course", "Section"]
    ):
        if section < 18 or section in [20, 25,30,35]:
            max_capacity = return_gen_ed_section_capacity(exam, window)
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

            for teacher, teacher_df in exam_section_df.groupby("Teacher"):
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

    registrations_pvt_tbl = pd.pivot_table(
        registrations_df,
        index=["Course", "NewSection", "Teacher"],
        values="StudentID",
        aggfunc="count",
    )

    output_filename = "output/registrations.xlsx"
    writer = pd.ExcelWriter(output_filename)
    registrations_df = registrations_df.sort_values(
        by=['Day','Time',"Course", "NewSection"]
    )
    registrations_df.to_excel(writer, sheet_name="registrations")
    registrations_pvt_tbl.to_excel(writer, sheet_name="pivot")

    registrations_df['Action'] = 'Replace'
    registrations_df['GradeLevel'] = ''
    registrations_df['OfficialClass'] = ''
    stars_upload_cols = [
        'StudentID',
        'LastName',
        'FirstName',
        'GradeLevel',
        'OfficialClass',
        'Course',
        'NewSection',
        'Action',
    ]
    registrations_df[stars_upload_cols].to_excel(writer, sheet_name="STARS")
    students_taking_exams_lst = registrations_df['StudentID'].unique()
    
    accommodations_to_check = testing_accommodations_df[testing_accommodations_df['StudentID'].isin(students_taking_exams_lst)]
    accommodations_to_check.to_excel(writer, sheet_name="AccommodationsToCheck")

    writer.close()

    return True


def return_gen_ed_section_capacity(exam_code, window):

    if window == 'January':
        if exam_code[0] == 'E':
            return 34
        else:
            return 40
    if window == 'June':
        if exam_code[0] == 'E':
            return 40
        else:
            return 34

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
    
    temp_str = ''
    for attribute in [senior,conflict,ENL,QR, time_and_a_half,double_time]:
        if attribute:
            temp_str+='1'
        else:
            temp_str+='0'
    

    section_dict = {
        '000010':24,
        '100010':31,
        '001010':32,
        '101010':33,
        '001000':34,
        '101000':35,
        '000001':36,
        '100001':37,
        '001001':38,
        '101001':39,
        '000110':40,
        '100110':43,
        '001110':44,
        '101110':45,
        '000101':46,
        '100101':47,
        '001101':48,
        '101101':49,
        '010010':50,
        '110010':51,
        '011010':52,
        '111010':53,
        '011000':54,
        '111000':55,
        '010001':56,
        '110001':57,
        '011001':58,
        '111001':59,
        '010110':62,
        '110110':63,
        '011110':64,
        '111110':65,
        '010101':66,
        '110101':67,
        '011101':68,
        '111101':69,
    }

    return section_dict.get(temp_str,20)



    if conflict and double_time and ENL and senior and QR:
        return 86
    if conflict and double_time and ENL and QR:
        return 87
    if conflict and double_time and senior and QR:
        return 85
    if conflict and double_time and QR:
        return 88

    if conflict and double_time and ENL and senior:
        return 82
    if conflict and double_time and ENL:
        return 83
    if conflict and double_time and senior:
        return 81
    if conflict and double_time:
        return 84

    if double_time and ENL and senior and QR:
        return 66
    if double_time and ENL and QR:
        return 67
    if double_time and senior and QR:
        return 65
    if double_time and QR:
        return 68

    if double_time and ENL and senior:
        return 62
    if double_time and ENL:
        return 63
    if double_time and senior:
        return 61
    if double_time:
        return 64

    if conflict and QR and ENL and senior:
        return 51
    if conflict and QR and time_and_a_half and senior:
        return 55
    if conflict and QR and ENL:
        return 52
    if conflict and QR and time_and_a_half:
        return 56

    if conflict and time_and_a_half and senior and ENL:
        return 35
    if conflict and time_and_a_half and senior:
        return 35
    if conflict and time_and_a_half and senior:
        return 35

    if QR and ENL and senior:
        return 41
    if QR and time_and_a_half and senior:
        return 45
    if QR and time_and_a_half:
        return 46



    
    if time_and_a_half and senior:
        return 25
    if time_and_a_half:
        return 26
    
    ## Checkvalve for Sped
    return 19