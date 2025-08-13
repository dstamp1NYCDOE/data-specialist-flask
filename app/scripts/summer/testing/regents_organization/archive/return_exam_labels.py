from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

from app.scripts.summer.testing.regents_organization import utils as regents_organization_utils

PADDING = 0
specs = labels.Specification(
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


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"


    cr_1_08_df = regents_organization_utils.return_processed_registrations()

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_Exam_Labels.pdf"
    else:
        exam_to_merge = form.exam_title.data
        filename = f"{month}_{school_year+1}_{exam_to_merge}_Labels.pdf"
        cr_1_08_df = cr_1_08_df[cr_1_08_df["ExamTitle"] == exam_to_merge]

    labels_to_make = []
    for (day, time, exam_title), students_df in cr_1_08_df.groupby(
        ["Day", "Time", "ExamTitle"]
    ):
        ## Part 1 Org Labels
        # for label_type in ["Part 1 Present", "Part 1 Absent"]:
        #     bag_label = {
        #         "Day": day,
        #         "Time": time,
        #         "Exam Title": exam_title,
        #         "Room": "",
        #         "Flag": label_type,
        #         "NumOfStudents": "",
        #         "ExamAdministration": f"{month} {school_year+1}",
        #         "Sections_lst": students_df[["Section", "Room"]]
        #         .drop_duplicates()
        #         .sort_values(by="Room")
        #         .to_dict("records"),
        #     }
        #     labels_to_make.append(bag_label)
        ## DBN storage Labels by scoring section
        # for dbn, students_from_dbn_df in students_df.groupby("Sending school"):
        #     dbn_label = {
        #         "Day": day,
        #         "Time": time,
        #         "Exam Title": exam_title,
        #         "Flag": "Storage Label",
        #         "Sending School": dbn,
        #         "NumOfStudents": len(students_from_dbn_df),
        #         "ExamAdministration": f"{month} {school_year+1}",
        #         "Sections_lst": students_from_dbn_df[["Section", "Room"]]
        #         .drop_duplicates()
        #         .sort_values(by="Section")
        #         .to_dict("records"),
        #     }
        #     labels_to_make.append(dbn_label)
        # labels_to_make.extend(
        #     return_blank_labels_needed_to_start_new_page(labels_to_make)
        # )

        # for i in range(1 * 30):
        #     temp_dict = {
        #         "Flag": "Student",
        #         "LastName": "_________________",
        #         "FirstName": "_____________",
        #         "Course": "_______",
        #         "Section": "____",
        #         "ExamAdministration": f"{month} {school_year+1}",
        #         "Exam Title": exam_title,
        #         "Sending school": "________",
        #         "StudentID": "________________",
        #         "Room": "_____",
        #     }
        #     labels_to_make.append(temp_dict)

        # for (hub_location,room), students_in_room_df in students_df.groupby(["hub_location","Room"]):
        for (room,hub_location), students_in_room_df in students_df.groupby(["Room","hub_location"]):
            ## Bag and Proctor Labels
            for label_type in ["Bag Label", "Folder Label", "Proctor Label"]:
                section_lst = students_in_room_df[["Section", "Type"]].drop_duplicates().sort_values(by="Section").to_dict("records")
                bag_label = {
                        "Day": day,
                        "Time": time,
                        "Exam Title": exam_title,
                        "Room": room,
                        "Flag": label_type,
                        "NumOfStudents": len(students_in_room_df),
                        "ExamAdministration": f"{month} {school_year+1}",
                        "Sections_lst": section_lst,
                    }
                if len(section_lst) <= 4:
                    labels_to_make.append(bag_label)
                else:
                    bag_label["Sections_lst"] = section_lst[:4]
                    labels_to_make.append(bag_label)    
                    bag_label["Sections_lst"] = section_lst[4:]
                    bag_label["NumOfStudents"] = ""
                    labels_to_make.append(bag_label)

            for section, students_in_section_df in students_in_room_df.groupby(
                "Section"
            ):
                ## Section Labels
                for label_type in ["Section Label"]:
                    bag_label = {
                        "Day": day,
                        "Time": time,
                        "Exam Title": exam_title,
                        "Room": room,
                        "Flag": label_type,
                        "Section": section,
                        "NumOfStudents": len(students_in_section_df),
                        "ExamAdministration": f"{month} {school_year+1}",
                        "Sections_lst": students_in_section_df[["Section", "Type"]]
                        .drop_duplicates()
                        .sort_values(by="Section")
                        .to_dict("records"),
                    }
                    labels_to_make.append(bag_label)

            previous_remainder = len(labels_to_make) % 30
            exam_code = students_in_room_df.iloc[0]["Course"]
            if exam_code[0] in ["M"]:
                labels_to_make.extend(students_in_room_df.to_dict("records"))
            elif exam_code[0] in ["E"]:
                labels_to_make.extend(students_in_room_df.to_dict("records"))                
            elif exam_code[0:4] in ["SXRK","SXR2","SXR3"]:
                labels_to_make.extend(students_in_room_df.to_dict("records"))
            else:
                for student in students_in_room_df.to_dict("records"):
                    for i in range(2):
                        labels_to_make.append(student)

            remainder = len(labels_to_make) % 30
            temp_lst = []

            for i in range(30 - remainder):
                temp_dict = {
                    "Flag": "Student",
                    "LastName": "_________________",
                    "FirstName": "_____________",
                    "Course": exam_code,
                    "Section": "____",
                    "ExamAdministration": f"{month} {school_year+1}",
                    "Exam Title": exam_title,
                    "Sending school": "________",
                    "StudentID": "________________",
                    "Room": room,
                    "DOB": "____/_____/_______",
                    "HomeLang": "_____________",
                }
                labels_to_make.append(temp_dict)

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    return f, filename


def return_blank_labels_needed_to_start_new_page(labels_to_make):
    remainder = len(labels_to_make) % 30
    temp_lst = []
    for i in range(30 - remainder):
        temp_lst.append({})
    return temp_lst


def return_full_exam_title(ExamTitle):

    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trigonometry",
        "LE": "Living Environment",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics", 
        "ESS": "Earth & Space Science",
        "Bio": "Biology"
    }
    return exam_title_dict.get(ExamTitle)


def draw_label(label, width, height, obj):

    if obj.get("Flag") == "Student":
        draw_student_label(label, width, height, obj)
    if obj.get("Flag") in ["Bag Label", "Proctor Label", "Folder Label"]:
        draw_bag_label(label, width, height, obj)
    if obj.get("Flag") in ["Storage Label"]:
        draw_storage_label(label, width, height, obj)
    if obj.get("Flag") in ["Part 1 Present", "Part 1 Absent"]:
        draw_part_1_labels(label, width, height, obj)
    if obj.get("Flag") in ["Section Label"]:
        draw_section_label(label, width, height, obj)


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


def draw_storage_label(label, width, height, obj):
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

    label.add(
        shapes.String(
            150, 45, f"{obj['NumOfStudents']} ", fontName="Helvetica", fontSize=22
        )
    )
    label.add(
        shapes.String(
            4, 11, f"{obj['Sending School']} ", fontName="Helvetica", fontSize=24
        )
    )

    l = obj["Sections_lst"]
    n = 4
    section_lst_of_lst = [l[i : i + n] for i in range(0, len(l), n)]
    for j, section_lst in enumerate(section_lst_of_lst):
        for i, section_dict in enumerate(section_lst):
            section_num = section_dict["Section"]

            label.add(
                shapes.String(
                    110 + 12 * j,
                    11 + 9 * i,
                    f"/{section_num}",
                    fontName="Helvetica",
                    fontSize=8,
                )
            )


def draw_section_label(label, width, height, obj):
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

    label.add(
        shapes.String(
            150, 45, f"{obj['NumOfStudents']} ", fontName="Helvetica", fontSize=22
        )
    )

    label.add(
        shapes.String(4, 11, f"\{obj['Section']} ", fontName="Helvetica", fontSize=36)
    )

    for i, section_dict in enumerate(obj["Sections_lst"]):
        section_num = section_dict["Section"]
        section_type = section_dict["Type"]
        label.add(
            shapes.String(
                75, 11 + 7 * i, f"{section_type} ", fontName="Helvetica", fontSize=8
            )
        )


def draw_bag_label(label, width, height, obj):
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
