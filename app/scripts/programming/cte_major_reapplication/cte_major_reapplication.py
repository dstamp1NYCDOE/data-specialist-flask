import pandas as pd
import numpy as np
from io import BytesIO

from matching.games import HospitalResident

import app.scripts.programming.vetting.main as vetting


def main(form, request):
    student_survey_file = request.files[form.student_survey_file.name]
    df = pd.read_csv(student_survey_file)
    preferences_df = df.drop_duplicates(subset=["StudentID"], keep="last")

    

    career_pathways_question_text = "Are you interested in HSFI Career Pathways course?  This class will make you eligible for the Apprenticeship program."
    career_pathways_interest_df = preferences_df[preferences_df[career_pathways_question_text]=='Yes']
    

    num_of_photography_seats = form.num_of_photography_seats.data
    num_of_vp_seats = form.num_of_vp_seats.data
    num_of_software_design_seats = form.num_of_software_design_seats.data
    num_of_business_seats = form.num_of_business_seats.data
    num_of_fashion_seats = form.num_of_fashion_seats.data
    num_of_art_and_design_seats = form.num_of_art_and_design_seats.data

    major_capacities = {
        "photo": num_of_photography_seats,
        "web": num_of_software_design_seats,
        "fd": num_of_fashion_seats,
        "a_n_d": num_of_art_and_design_seats,
        "vp": num_of_vp_seats,
        "fmm": num_of_business_seats,
    }

    student_requests_file = request.files[form.student_requests_file.name]
    student_requests_df = pd.read_excel(student_requests_file)

    sophomore_classes = [
        "AFS61TF",
        "TUS21TA",
        "AUS11TA",
        "APS11T",
    ]
    rising_sophomore_students_df = student_requests_df[
        student_requests_df["Course"].isin(sophomore_classes)
    ]



    current_enrollment = pd.pivot_table(
        rising_sophomore_students_df,
        index="Course",
        values="StudentID",
        aggfunc="count",
    )
    print(current_enrollment)

    rising_sophomores_studentIDs = rising_sophomore_students_df["StudentID"].tolist()
    print(f"Num of rising sophomores {len(rising_sophomores_studentIDs)}")

    ### student vetting numbers
    student_vetting_df = vetting.main()

    rising_sophomore_students_df = rising_sophomore_students_df.merge(
        student_vetting_df[["StudentID", "AttdTier", "Art GPA"]],
        on=["StudentID"],
        how="left",
    ).sort_values(by=["AttdTier", "Art GPA"], ascending=[True, False])

    print(rising_sophomore_students_df)

    ## drop students that are not rising sophomores
    preferences_df = preferences_df[
        preferences_df["StudentID"].isin(rising_sophomores_studentIDs)
    ]

    preferences_df["StudentRanking"] = preferences_df.apply(
        put_choices_into_list, axis=1
    )

    student_preferences = {}
    for index, student in preferences_df.iterrows():
        StudentID = student["StudentID"]
        StudentRanking = student["StudentRanking"]
        student_preferences[StudentID] = StudentRanking

    for index, student in rising_sophomore_students_df.iterrows():
        StudentID = student["StudentID"]
        if student_preferences.get(StudentID):
            pass
        else:
            default_course = student["Course"]
            default_major_dict = {
                "AFS61TF": ["fd","fmm","web","vp","photo","a_n_d"],
                "TUS21TA": ["fmm", "vp", "web", "a_n_d", "fd"],
                "AUS11TA": ["a_n_d", "web", "vp","photo","fd"],
                "APS11T": ["a_n_d", "web", "vp","photo","fd"],
            }
            student_preferences[StudentID] = default_major_dict.get(default_course)

    students_preferences_df = pd.DataFrame.from_dict(
        student_preferences, orient="index"
    ).fillna("")
    students_preferences_df["rankings"] = students_preferences_df.values.tolist()
    students_preferences_df = students_preferences_df.reset_index(names=["StudentID"])
    students_preferences_df = students_preferences_df[["StudentID", "rankings"]]

    rising_sophomore_students_df = rising_sophomore_students_df.merge(
        students_preferences_df, on=["StudentID"], how="left"
    ).sort_values(by=["AttdTier", "Art GPA"], ascending=[True, False])

    major_preferences = {}
    majors = ["photo", "web", "fd", "a_n_d", "vp", "fmm"]
    for major in majors:
        students_interested = [
            StudentID
            for StudentID, rankings in student_preferences.items()
            if major in rankings
        ]
        major_preferences[major] = rising_sophomore_students_df[
            rising_sophomore_students_df["StudentID"].isin(students_interested)
        ]["StudentID"]

    total_seats = sum(major_capacities.values())
    print(f"Num of seats {total_seats}")

    game = HospitalResident.create_from_dictionaries(
        student_preferences, major_preferences, major_capacities
    )

    matching = game.solve(optimal="hospital")

    rising_sophomore_students_df = rising_sophomore_students_df.drop(
        columns=[
            "Course",
            "Section",
            "OffClass",
            "Grade",
            "Counselor",
        ]
    )

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    output = []
    for major, students in matching.items():
        students = [student.name for student in students]
        df = rising_sophomore_students_df[
            rising_sophomore_students_df["StudentID"].isin(students)
        ]
        df["FirstChoice"] = df["rankings"].apply(lambda x: x[0])
        df["Major"] = major.name
        df.to_excel(writer, sheet_name=major.name, index=False)

        output.extend(df.to_dict("records"))

    output_df = pd.DataFrame(output)
    output_df.to_excel(writer, sheet_name="combined", index=False)

    numbers_pivot_tbl = pd.pivot_table(
        output_df, index=["Major"], values=["StudentID"], aggfunc="count"
    ).reset_index()

    numbers_pivot_tbl.to_excel(writer, sheet_name="counts", index=False)

    first_choice_df = pd.pivot_table(
        output_df,
        index=["Major"],
        columns=["FirstChoice"],
        values=["StudentID"],
        aggfunc="count",
    ).fillna(0)
    print(first_choice_df)

    first_choice_df.to_excel(
        writer,
        sheet_name="first_choice",
    )

    career_pathways_interest_df = career_pathways_interest_df.merge(
        student_vetting_df[["StudentID", "AttdTier", "Art GPA"]],
        on=["StudentID"],
        how="left",
    ).sort_values(by=["AttdTier", "Art GPA"], ascending=[True, False])

    career_pathways_interest_df.head(68).to_excel(writer, sheet_name="CareerClass", index=False)

    writer.close()
    f.seek(0)
    return f


def put_choices_into_list(student_row):
    photo_text = "Indicate your order of preference [Photography]"
    photo = student_row[photo_text]

    web_text = "Indicate your order of preference [Software Development]"
    web = student_row[web_text]

    fd_text = "Indicate your order of preference [Fashion Design]"
    fd = student_row[fd_text]

    a_n_d_text = "Indicate your order of preference [Art & Design]"
    a_n_d = student_row[a_n_d_text]

    vp_text = "Indicate your order of preference [Visual Presentation]"
    vp = student_row[vp_text]

    fmm_text = "Indicate your order of preference [Business]"
    fmm = student_row[fmm_text]

    dict = {photo: "photo", web: "web", fd: "fd", a_n_d: "a_n_d", vp: "vp", fmm: "fmm"}
    output_list = [
        "First Choice",
        "Second Choice",
        "Third Choice",
        "Fourth Choice",
        "Fifth Choice",
        "Sixth Choice",
    ]
    student_output = []
    for order in output_list:
        student_output.append(dict[order])

    return student_output
