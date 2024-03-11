import pandas as pd

from reportlab.graphics import shapes
from reportlab_qrcode import QRCodeImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    Paragraph,
    PageBreak,
    Spacer,
    Image,
    Table,
    TableStyle,
    ListFlowable,
)
from reportlab.platypus import SimpleDocTemplate

import datetime as dt

import os

from io import BytesIO
from flask import session, current_app
import app.scripts.utils as utils

styles = getSampleStyleSheet()

styles.add(
    ParagraphStyle(
        name="Normal_RIGHT",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )
)

styles.add(
    ParagraphStyle(
        name="Body_Justify",
        parent=styles["BodyText"],
        alignment=TA_JUSTIFY,
    )
)

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re


def main(form, request):
    student_exam_tickets_df = process_exam_tickets(form, request)
    student_exam_tickets_df["student_flowbles"] = student_exam_tickets_df.apply(
        generate_student_exam_ticket, axis=1
    )
    flowables = []
    for (session, room), df in student_exam_tickets_df.groupby(["Session", "Room#"]):
        room_roster = generate_room_roster(df, room, session)
        flowables.extend(room_roster)

        temp_flowables = df["student_flowbles"].explode().to_list()
        flowables.extend(temp_flowables)

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=1 * inch,
        leftMargin=1.5 * inch,
        rightMargin=1.5 * inch,
        bottomMargin=1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def generate_room_roster(df, room, session):
    exam_title = df.iloc[0, :]["Test Name"]
    flowables = []
    paragraph = Paragraph(
        f"{exam_title} - Room {room} - Session {session}",
        styles["Title"],
    )
    flowables.append(paragraph)

    table_cols = ["StudentName", "StudentUsername", "StudentPassword"]
    students_tbl = utils.return_df_as_table(df, table_cols, fontsize=10)
    flowables.append(students_tbl)

    flowables.append(PageBreak())
    return flowables


def generate_student_exam_ticket(student_row):
    flowables = []

    StudentID = int(student_row["StudentID"])
    student_name = student_row["StudentName"]
    StudentUsername = student_row["StudentUsername"]
    StudentPassword = student_row["StudentPassword"]

    room_num = student_row["Room#"]
    testing_session = student_row["Session"]
    exam_title = student_row["Test Name"]

    paragraph = Paragraph(
        f"{exam_title} Exam Ticket",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{student_name} ({StudentID})",
        styles["Title"],
    )
    flowables.append(paragraph)

    try:
        path = os.path.join(current_app.root_path, f"data/StudentPhotos")
        photo_str = os.path.join(path, f"{int(StudentID)}.jpg")
        I = Image(photo_str)
        I.drawHeight = 3.0 * inch
        I.drawWidth = 3.0 * inch
        I.hAlign = "CENTER"
        flowables.append(I)
    except:
        I = ""
        pass

    paragraph = Paragraph(
        f"Testing Room: {room_num} - {testing_session}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"StudentUsername: {StudentUsername}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"StudentPassword: {StudentPassword}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Room Code: ________________________",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    flowables.append(PageBreak())
    return flowables


def process_exam_tickets(form, request):
    student_testing_assignments = request.files[form.student_testing_assignments.name]
    df = pd.read_csv(student_testing_assignments)
    df = df.dropna(subset=["StudentID"])

    df["Room#"] = df["Room"].str.extract(r"(\d{3})")
    df["Session"] = df["Room"].str.extract(r"([AaPp][Mm])")
    df["StudentName"] = df["Student Name"].apply(swap_name)

    print(df)

    PDF = request.files[form.student_exam_tickets.name]

    pdfReader = PyPDF2.PdfReader(PDF)
    num_of_pages = pdfReader.pages

    combined_txt = ""
    for page_num, page in enumerate(num_of_pages):
        if page_num == 0:
            pass
        else:
            page_text = page.extract_text()
            combined_txt += page_text

    all_lines_of_text = combined_txt.splitlines()
    student_lst = []

    for sub_lst in iterate_through_n_lines_at_a_time(all_lines_of_text, 12):
        test_name = sub_lst[1]

        testing_room = sub_lst[2]
        student_name = sub_lst[3].removeprefix("Name: ").strip()
        date_of_birth = sub_lst[4].removeprefix("Date of Birth: ")

        student_username = sub_lst[10].removesuffix("User ID")
        student_password = sub_lst[11].removesuffix("Registration Number")

        temp_dict = {
            "StudentName": student_name,
            "DateOfBirth": date_of_birth,
            "StudentUsername": student_username,
            "StudentPassword": student_password,
        }
        student_lst.append(temp_dict)

    student_exam_tickets_df = pd.DataFrame(student_lst)

    student_exam_tickets_df = student_exam_tickets_df.merge(
        df, on=["StudentName"], how="left"
    )

    cols = [
        "StudentID",
        "StudentName",
        "DateOfBirth",
        "StudentUsername",
        "StudentPassword",
        "Test Name",
        "Room#",
        "Session",
    ]
    student_exam_tickets_df = student_exam_tickets_df[cols]
    student_exam_tickets_df = student_exam_tickets_df.dropna(subset=["StudentID"])
    return student_exam_tickets_df


def swap_name(student_name):
    last_name, first_name = student_name.split(", ")
    return f"{first_name} {last_name}".strip()


def iterate_through_n_lines_at_a_time(input_lst, n):
    for i in range(0, len(input_lst), n):
        yield input_lst[i : i + n]
