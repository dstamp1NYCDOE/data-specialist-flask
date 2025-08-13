from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

def return_hub_location(section_row):
    Room = int(section_row["Room"])
    Time = section_row["Time"]
    exam_num = section_row["exam_num"]
    Section = section_row["Section"]

    if Room == 329:
        return 329
    if Room > 800:
        return {1: 919, 2: 823}.get(exam_num, 823)
    return {1: 727, 2: 519}.get(exam_num, 519)


def return_processed_registrations():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df.fillna({"Room": 202})
    cr_1_08_df["Room"] = cr_1_08_df["Room"].astype(int)

    cr_1_08_df["ExamAdministration"] = f"{month} {school_year+1}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(
        path, sheet_name="SummerSectionProperties"
    )

    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )
    cr_1_08_df = cr_1_08_df.merge(section_properties_df[['Section','Type']], on=["Section"], how="left")

    cr_1_08_df["Date"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%m/%d")
    
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(return_full_exam_title)
    cr_1_08_df['hub_location'] = cr_1_08_df.apply(return_hub_location, axis=1)
    cr_1_08_df["Flag"] = "Student"

    ## attach home lang from 3.07
    filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df.merge(cr_3_07_df[['StudentID','HomeLangCode']], on=["StudentID"], how="left")

    home_lang_codes_df = utils.return_home_lang_code_table(files_df)
    cr_1_08_df = cr_1_08_df.merge(home_lang_codes_df[['HomeLang','HomeLangCode']], on=["HomeLangCode"], how="left")
    print(cr_1_08_df)

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left").fillna({"Sending school":'X'})

    ## attach photos
    cr_1_08_df = cr_1_08_df.merge(photos_df[['StudentID','photo_filename']], on=["StudentID"], how="left")

    cr_1_08_df = cr_1_08_df.drop_duplicates(subset=['StudentID','Course'])
    return cr_1_08_df

def return_exam_book():
    cr_1_08_df = return_processed_registrations()
    cols = ['Course','Section','Day','Date','Time','Exam Title','ExamTitle','hub_location','Type','Room']
    exam_book_df = pd.pivot_table(
        cr_1_08_df,
        index=cols,
        values=['StudentID'],
        aggfunc='count'
    )
    exam_book_df.columns = ['NumOfStudents']
    exam_book_df = exam_book_df.reset_index()

    return exam_book_df

def return_full_exam_title(ExamTitle):

    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trig",
        "LE": "Liv Environ",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics",
        "Bio": "Biology",
        "ESS": "Earth & SS",
    }
    return exam_title_dict.get(ExamTitle)


PADDING = 0

import labels
label_specs = labels.Specification(
    215.9,
    279.4,
    3,
    10,
    66.6,
    25.2,
    corner_radius=2,
    left_margin=5,
    right_margin=5,
    top_margin=12.25,
    # bottom_margin=13,
    left_padding=PADDING,
    right_padding=PADDING,
    top_padding=PADDING,
    bottom_padding=PADDING,
    row_gap=0,
)

def return_blank_labels_needed_to_start_new_page(labels_to_make):
    remainder = len(labels_to_make) % 30
    temp_lst = []
    if remainder == 0:
        return temp_lst
    for i in range(30 - remainder):
        temp_lst.append({})
    return temp_lst


def return_blank_labels_needed_to_start_new_row(labels_to_make):
    remainder = len(labels_to_make) % 3
    temp_lst = []
    for i in range(3 - remainder):
        temp_lst.append({})
    return temp_lst


def draw_label(label, width, height, obj):

    if obj.get("Flag") == "Student":
        draw_student_label(label, width, height, obj)
    if obj.get("Flag") in ["Folder Label"]:
        draw_folder_label(label, width, height, obj)
    if obj.get("Flag") in ["Part 1", "Part 2"]:
        draw_section_label(label, width, height, obj)        
    if obj.get("Flag") in ["Section Label"]:
        draw_section_label(label, width, height, obj)
    if obj.get("Flag") in ["Scoring Certificate Label"]:
        draw_scoring_certificate_label(label, width, height, obj)        


from reportlab.graphics import shapes
from reportlab.lib import colors

 
def draw_section_label(label,width,height,obj):
    if obj:
        exam_title = obj.get("Exam Title")
        type = obj.get("Type")
        room = obj.get("Room")
        Day = obj.get("Day")
        Time = obj.get("Time")
        Part = obj.get("Flag")
        num_of_students = obj.get('NumOfStudents')

        label.add(shapes.String(4, 52, f"{exam_title}", fontName="Helvetica", fontSize=18))
        label.add(
            shapes.String(125, 38, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
        )

        label.add(shapes.String(125, 52, f"{Part}", fontName="Helvetica", fontSize=18))

        label.add(shapes.String(4, 4, f"{room}", fontName="Helvetica", fontSize=40))
        label.add(shapes.String(110, 10, f"{type}", fontName="Helvetica", fontSize=7))
        if num_of_students:
            label.add(shapes.String(125, 25, f"{num_of_students} Students", fontName="Helvetica", fontSize=7))



        label.add(
            shapes.String(
                4, 38, f"Section: {obj.get('Section')}", fontName="Helvetica", fontSize=11
            )
        )


def draw_part_1_labels(label, width, height, obj):
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["Exam Title"]} Regents - {obj["Flag"]}',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(
        shapes.String(
            4, 45, f'{obj["Day"]} - {obj["Time"]}', fontName="Helvetica", fontSize=10
        )
    )

    l = obj["Sections_lst"]
    n = 4
    section_lst_of_lst = [l[i : i + n] for i in range(0, len(l), n)]
    for j, section_lst in enumerate(section_lst_of_lst):
        for i, section_dict in enumerate(section_lst):
            section_num = section_dict["Section"]
            section_room = section_dict["Room"]
            label.add(
                shapes.String(
                    4 + 38 * j,
                    11 + 7 * i,
                    f"{section_room} ",
                    fontName="Helvetica",
                    fontSize=8,
                )
            )



def draw_folder_label(label, width, height, obj):
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["Exam Title"]}',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(
        shapes.String(
            4, 45, f'{obj["Day"]} - {obj["Time"]} | Hub: {obj["hub_location"]}', fontName="Helvetica", fontSize=10
        )
    )

    label.add(
        shapes.String(
            150, 45, f"{obj['NumOfStudents']} ", fontName="Helvetica", fontSize=22
        )
    )

    label.add(
        shapes.String(4, 11, f"{obj['Room']} ", fontName="Helvetica", fontSize=36)
    )

    for i, section_dict in enumerate(obj["Sections_lst"]):
        section_num = section_dict["Section"]
        section_type = section_dict["Type"]
        label.add(
            shapes.String(
                75,
                11 + 7 * i,
                f"/{section_num} - {section_type} ",
                fontName="Helvetica",
                fontSize=8,
            )
        )


def draw_student_label(label, width, height, obj):

    student_name = f"{obj['LastName'].upper()}, {obj['FirstName'].upper()}"

    course_section = f"{obj['Course']}/{obj['Section']}"

    label.add(shapes.Line(0, 70, 0, 54, strokeColor=colors.grey, strokeWidth=2))
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["ExamAdministration"]} {obj["Exam Title"]} Regents',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(shapes.Line(0, 53, 300, 53, strokeColor=colors.grey, strokeWidth=1))
    label.add(
        shapes.String(
            4, 42, f'School: {obj["Sending school"]}', fontName="Helvetica", fontSize=10
        )
    )
    label.add(shapes.Line(85, 54, 85, 44, strokeColor=colors.grey, strokeWidth=1))
    label.add(
        shapes.String(
            93, 42, f"Course: {course_section}", fontName="Helvetica", fontSize=10
        )
    )

    label.add(shapes.String(4, 25, student_name, fontSize=12))

    label.add(
        shapes.String(
            4, 11, f"ID: {obj['StudentID']}", fontName="Helvetica", fontSize=9
        )
    )

    label.add(
        shapes.String(
            130, 11, f"Room: {obj['Room']} ", fontName="Helvetica", fontSize=9
        )
    )


def draw_scoring_certificate_label(label, width, height, obj):

    label.add(
        shapes.String(
            4,
            50,
            f'{obj["Exam Title"]}',
            fontName="Helvetica",
            fontSize=17,
        )
    )

    label.add(
        shapes.String(
            4,
            30,
            f'{obj["Flag"]}',
            fontName="Helvetica",
            fontSize=13,
        )
    )

    label.add(
        shapes.String(
            4, 10, f'{obj["Day"]} - {obj["Time"]}', fontName="Helvetica", fontSize=13
        )
    )