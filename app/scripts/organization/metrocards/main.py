import pandas as pd
import numpy as np
import os
from io import BytesIO
from io import StringIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def return_processed_data(form, request):
    school_year = session["school_year"]
    term = session["term"]

    metrocard_student_organization_file = request.files[
        form.metrocard_student_organization_file.name
    ]
    metrocard_student_organization_df = pd.read_csv(
        metrocard_student_organization_file
    ).fillna("")

    metrocard_tbl = form.metrocard_tbl.data
    string_data = StringIO(metrocard_tbl)
    metrocard_tbl_df = pd.read_csv(string_data, sep="\t")

    metrocard_tbl_df = metrocard_tbl_df.sort_values(by=["StartingSerialNumber"])

    metrocard_lst = []
    for index, serial_number_row in metrocard_tbl_df.iterrows():
        starting_serial_number = serial_number_row["StartingSerialNumber"]
        num_of_cards = serial_number_row["#_of_cards"]
        for i in range(num_of_cards):
            metrocard_lst.append({"MetroCard #": str(starting_serial_number + i)})

    metrocard_tbl_df = pd.DataFrame(metrocard_lst)

    metrocard_student_organization_df = metrocard_student_organization_df.sort_values(
        by=["TeacherName", "LastName", "FirstName"]
    )
    metrocard_student_organization_df["Nickname"] = (
        metrocard_student_organization_df.apply(convert_name, axis=1)
    )
    metrocard_student_organization_df = metrocard_student_organization_df.reset_index()

    metrocard_student_organization_df = pd.concat(
        [metrocard_student_organization_df, metrocard_tbl_df], axis=1
    )
    print(metrocard_student_organization_df)
    return metrocard_student_organization_df


def return_busing_students():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    filename = utils.return_most_recent_report_by_semester(
        files_df, "RDRS", year_and_semester
    )
    RDRS_df = utils.return_file_as_df(filename, skiprows=2)
    RDRS_df["StudentID"] = RDRS_df["Student Id"].apply(clean_StudentID_str)

    return RDRS_df["StudentID"]


def clean_StudentID_str(student_id_str):
    return int(student_id_str.replace("-", ""))


def return_eligible_students():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    filename = utils.return_most_recent_report_by_semester(
        files_df, "RTPL", year_and_semester
    )
    RTPL_df = utils.return_file_as_df(filename, skiprows=3)

    busing_students_lst = return_busing_students()

    eligible_students = RTPL_df[~RTPL_df["Student Id"].isin(busing_students_lst)]

    return eligible_students["Student Id"]


def return_metrocard_labels_file(form, request):
    metrocard_student_organization_df = return_processed_data(form, request)

    metrocard_student_organization_df["Signature (Sign your name)"] = ""
    signature_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Room",
        "MetroCard #",
        "Signature (Sign your name)",
    ]
    f = BytesIO()
    metro_card_labels_lst = []

    for (Teacher, Room), students_df in metrocard_student_organization_df.groupby(
        ["TeacherName", "Room"]
    ):
        teacher_row = return_teacher_row(Teacher, Room)
        metro_card_labels_lst.append(teacher_row)

        for index, student in students_df.iterrows():
            student_row = return_label_dict(student)
            metro_card_labels_lst.append(student_row)

        remainder = (1 + len(students_df)) % 3

        if remainder == 0:
            blanks = 3
        elif remainder == 1:
            blanks = 5
        elif remainder == 2:
            blanks = 4

    PADDING = 1
    specs = labels.Specification(
        215.9,
        279.4,
        3,
        10,
        66.675,
        25.2,
        corner_radius=2,
        left_margin=5,
        right_margin=5,
        top_margin=12.75,
        # bottom_margin=13,
        left_padding=PADDING,
        right_padding=PADDING,
        top_padding=PADDING,
        bottom_padding=PADDING,
        row_gap=0.05,
    )

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(metro_card_labels_lst)

    sheet.save(f)
    f.seek(0)

    school_year = session["school_year"]
    filename = f"Fall{school_year}MetroCardLabels.pdf"
    return f, filename


def return_metrocard_signature_sheet_file(form, request):
    metrocard_student_organization_df = return_processed_data(form, request)

    metrocard_student_organization_df["Signature (Sign your name)"] = ""
    signature_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Room",
        "MetroCard #",
        "Signature (Sign your name)",
    ]
    f = BytesIO()
    writer = pd.ExcelWriter(f)

    output_df = metrocard_student_organization_df[signature_cols]
    output_df.to_excel(
        writer,
        sheet_name="AllStudents",
        index=False,
    )

    for Teacher, students_df in metrocard_student_organization_df.groupby(
        "TeacherName"
    ):
        output_df = students_df[signature_cols]
        output_df.to_excel(
            writer,
            sheet_name=Teacher,
            index=False,
        )

    writer.book.formats[0].set_font_size(14)
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.autofit()

    writer.close()
    f.seek(0)

    school_year = session["school_year"]
    download_name = f"Fall{school_year}MetroCardSignatureSheets.xlsx"
    return f, download_name


def draw_label(label, width, height, obj):
    metrocard_num = obj["MetroCard #"]
    nickname = obj["Nickname"]
    op_room = obj["OP_room"]
    StudentID = obj["StudentID"]

    label.add(shapes.String(4, 40, f"{nickname}", fontName="Helvetica", fontSize=14))
    label.add(shapes.String(4, 30, f"{StudentID}", fontName="Helvetica", fontSize=10))
    label.add(
        shapes.String(4, 55, f"{metrocard_num}", fontName="Helvetica", fontSize=10)
    )
    label.add(shapes.String(150, 55, f"{op_room}", fontName="Helvetica", fontSize=10))


def return_label_dict(student):
    metrocard_num = student["MetroCard #"]
    nickname = student["Nickname"]
    OP_room = student["Room"]
    StudentID = str(student["StudentID"])

    temp_dict = {
        "MetroCard #": "X" * 10 + str(metrocard_num)[-4:],
        "StudentID": f"ID: XXXX{StudentID[-5:]}",
        "Nickname": nickname,
        "OP_room": OP_room,
    }
    return temp_dict


def return_teacher_row(Teacher, Room):
    temp_dict = {
        "MetroCard #": "MetroCards",
        "StudentID": "",
        "Nickname": Teacher,
        "OP_room": Room,
    }
    return temp_dict


def return_space_row():
    temp_dict = {
        "MetroCard #": "",
        "StudentID": "",
        "Nickname": "",
        "OP_room": "",
    }
    return temp_dict


def convert_name(student_row):
    if student_row["FirstName"]:
        first_name = student_row["FirstName"]
        last_name = student_row["LastName"]
    else:
        name_lst = student_row["Name"].split(" ")
        first_name = name_lst[1]
        last_name = name_lst[0]
    return f"{first_name[0]} {last_name}"
