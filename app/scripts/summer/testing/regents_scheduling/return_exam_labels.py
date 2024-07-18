from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors


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

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df.fillna({'Room':'202'})

    cr_1_08_df['ExamAdministration'] = f"{month} {school_year+1}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(return_full_exam_title)

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left") 

    
    if form.exam_title.data == 'ALL':
        filename = f"{month}_{school_year+1}_Exam_Labels.pdf"
    else:
        exam_to_merge = form.exam_title.data
        filename = f"{month}_{school_year+1}_{exam_to_merge}_Labels.pdf"
        cr_1_08_df = cr_1_08_df[cr_1_08_df['ExamTitle']==exam_to_merge]

    labels_to_make = []
    for (day, time, exam_title), students_df in cr_1_08_df.groupby(
        ["Day", "Time", "ExamTitle"]
    ):
        for room, students_in_room_df in students_df.groupby("Room"):
            previous_remainder = len(labels_to_make) % 30
            exam_code = students_in_room_df.iloc[0]["Course"]
            if exam_code[0] in ["M"]:
                labels_to_make.extend(students_in_room_df.to_dict("records"))
            elif exam_code[0:4] == "SXRK":
                labels_to_make.extend(students_in_room_df.to_dict("records"))
            else:
                for student in students_in_room_df.to_dict("records"):
                    for i in range(2):
                        labels_to_make.append(student)

            next_remainder = len(labels_to_make) % 30
            blanks_to_add = 0
            if next_remainder == 0:
                blanks_to_add += 0
            else:
                if len(labels_to_make) % 3 == 0:
                    blanks_to_add += 0
                elif len(labels_to_make) % 3 == 1:
                    blanks_to_add += 2
                elif len(labels_to_make) % 3 == 2:
                    blanks_to_add += 1
                if (len(labels_to_make) + blanks_to_add) % 30 != 0:
                    blanks_to_add += 3             
            for i in range(blanks_to_add):
                temp_dict = {
                'LastName': '_________________',
                'FirstName': '_____________',
                'Course': exam_code,
                'Section': '____',
                'ExamAdministration': f"{month} {school_year+1}",
                'Exam Title': exam_title,
                'Sending school': '________',
                'StudentID': '________________',
                'Room': '_____',
                'DOB': '____/_____/_______',
                'HomeLang': '_____________',}
                labels_to_make.append(temp_dict)

            next_remainder = len(labels_to_make) % 30

            blanks_to_add = 0
            if next_remainder == 0:
                blanks_to_add += 0
            else:
                if len(labels_to_make) % 3 == 0:
                    blanks_to_add += 0
                elif len(labels_to_make) % 3 == 1:
                    blanks_to_add += 2
                elif len(labels_to_make) % 3 == 2:
                    blanks_to_add += 1
                if (len(labels_to_make) + blanks_to_add) % 30 != 0:
                    blanks_to_add += 3


            for i in range(blanks_to_add):
                labels_to_make.append({})

        next_remainder = len(labels_to_make) % 30
        for i in range(next_remainder):
            labels_to_make.append({})    

        for i in range(3*30):
            temp_dict = {
            'LastName': '_________________',
            'FirstName': '_____________',
            'Course': '_______',
            'Section': '____',
            'ExamAdministration': f"{month} {school_year+1}",
            'Exam Title': '______________',
            'Sending school': '________',
            'StudentID': '________________',
            'Room': '_____',
            }
            labels_to_make.append(temp_dict)

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_student_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    return f, filename

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
    }
    return exam_title_dict.get(ExamTitle)


def draw_student_label(label, width, height, obj):
    if obj:
        student_name = f"{obj['LastName'].upper()}, {obj['FirstName'].upper()}"


        course_section = f"{obj['Course']}/{obj['Section']}"

        label.add(shapes.Line(0, 70, 0, 54,
                  strokeColor=colors.grey, strokeWidth=2))
        label.add(shapes.String(
            4, 57, f'{obj["ExamAdministration"]} {obj["Exam Title"]} Regents', fontName="Helvetica", fontSize=10))
        label.add(shapes.Line(0, 53, 300, 53,
                  strokeColor=colors.grey, strokeWidth=1))
        label.add(shapes.String(
            4, 42, f'School: {obj["Sending school"]}', fontName="Helvetica", fontSize=10))
        label.add(shapes.Line(85, 54, 85, 44,
                  strokeColor=colors.grey, strokeWidth=1))
        label.add(shapes.String(
            93, 42, f'Course: {course_section}', fontName="Helvetica", fontSize=10))

        label.add(shapes.String(4, 25, student_name, fontSize=12))

        label.add(shapes.String(
            4, 11, f"ID: {obj['StudentID']}", fontName="Helvetica", fontSize=9))

        label.add(shapes.String(
                    130, 11, f"Room: {obj['Room']} ", fontName="Helvetica", fontSize=9))
            
        # label.add(shapes.String(
        #     4, 6, f'DOB: {obj["DOB"]}', fontName="Helvetica", fontSize=7))
        # label.add(shapes.String(
        #     90, 6, f'Home Lang.: {obj["HomeLang"]}', fontName="Helvetica", fontSize=7))