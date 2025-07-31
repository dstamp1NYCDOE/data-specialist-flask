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

from app.scripts import scripts, files_df
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
    exam_date = df.iloc[0, :]["ExamDate"]
    exam_date = exam_date.strftime("%B %e")
    flowables = []
    paragraph = Paragraph(
        f"{exam_date} - {exam_title} - Room {room} - Session {session}",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{return_computer_login_info(room)}",
        styles["Normal"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"This roster is meant to help with checking in students but the roster of record is what appears in Test Day Toolkit.",
        styles["Normal"],
    )
    flowables.append(paragraph)

    table_cols = ["StudentName", "StudentUsername", "StudentPassword"]
    students_tbl = utils.return_df_as_table(df, table_cols, fontsize=10)
    flowables.append(students_tbl)

    flowables.append(PageBreak())
    return flowables


def return_computer_login_info(room_number):
    return "Log in with your DOE email and password"
    if room_number in ["919", "901", "603", "221"]:
        return f"Username: .\{room_number}s# (Type period + backslash +room number + s + computer number ex. .\{room_number}s24"
    if room_number in ["704", "519", "319"]:
        return f"Username: \{room_number}s# (Type backslash +room number + s + computer number ex. \{room_number}s24"
    if room_number in ["201"]:
        return f"Username: .\student (Sign-in options -> Key icon Type period + backslash + student ex. \student"


def generate_student_exam_ticket(student_row):
    flowables = []

    StudentID = int(student_row["StudentID"])
    student_name = student_row["StudentName"]
    StudentUsername = student_row["StudentUsername"]
    StudentPassword = student_row["StudentPassword"]

    email_address = student_row["Student DOE Email"]
    date_of_birth = student_row["DOB"]
    date_of_birth = date_of_birth.strftime("%m/%d/%Y")

    apt_num = student_row["AptNum"]
    street = student_row["Street"]
    city = student_row["City"]
    state = student_row["State"]
    zipcode = int(student_row["Zip"])
    street_address = f"{street} {apt_num} {city}, {state} {zipcode}"

    room_num = student_row["Room#"]
    testing_session = student_row["Session"]
    exam_title = student_row["Test Name"]
    exam_date = student_row["ExamDate"]
    exam_date = exam_date.strftime("%B %e")

    paragraph = Paragraph(
        f"{exam_date} {exam_title} Exam Ticket",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{student_name}",
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

    ## Student to Do List
    student_to_dos = ListFlowable(
        [
            Paragraph(
                f"Log into the computer with your DOE email ({email_address}) and password",
                styles["Normal"],
            ),
            Paragraph(
                "Open Blue Book app on desktop. If BlueBook does not appear, restart computer",
                styles["Normal"],
            ),
            Paragraph(
                f"Log into Bluebook with your test day username ({StudentUsername}) and registration number ({StudentPassword})",
                styles["Normal"],
            ),
            Paragraph("Complete the digital readiness section", styles["Normal"]),
            Paragraph(
                "Wait for the proctor to provide the room code and start code",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="squarelrs",
    )

    flowables.append(student_to_dos)

    paragraph = Paragraph(
        f"Student Info",
        styles["Heading3"],
    )
    flowables.append(paragraph)

    student_info = ListFlowable(
        [
            Paragraph(
                f"<b>Date of Birth:</b> {date_of_birth}",
                styles["Normal"],
            ),
            Paragraph(
                f"{street} {apt_num}",
                styles["Normal"],
            ),
            Paragraph(
                f"{city}, {state} {zipcode}",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="squarelrs",
    )
    flowables.append(student_info)

    paragraph = Paragraph(
        f"THIS PAPER WILL BE COLLECTED AT THE END OF THE EXAM",
        styles["Heading3"],
    )
    flowables.append(paragraph)

    flowables.append(PageBreak())
    return flowables


def process_exam_tickets(form, request):
    student_testing_assignments = request.files[form.student_testing_assignments.name]
    df = pd.read_csv(student_testing_assignments)
    df = df.dropna(subset=["StudentID"])

    exam_date = form.exam_date.data
    exam_date = pd.to_datetime(exam_date)

    df["Room#"] = df["Room"].str.extract(r"(\d{3})")

    df["Session"] = df["Room"].str.extract(r"([AaPp][Mm])")
    df["ExamDate"] = df["Room"].apply(lambda x: exam_date)
    df["StudentName"] = df["Student Name"].apply(swap_name)

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
    students_registered_for_exam_df = student_exam_tickets_df

    cols = [
        "StudentID",
        "StudentName",
        "DateOfBirth",
        "StudentUsername",
        "StudentPassword",
        "Test Name",
        "Room#",
        "Session",
        "ExamDate",
    ]
    student_exam_tickets_df = student_exam_tickets_df[cols]
    student_exam_tickets_df = student_exam_tickets_df.dropna(subset=["StudentID"])

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    student_exam_tickets_df = student_exam_tickets_df.merge(
        cr_3_07_df, on="StudentID", how="inner"
    )
    students_on_register_testing = student_exam_tickets_df["StudentID"]

    print(
        students_registered_for_exam_df[
            ~students_registered_for_exam_df["StudentID"].isin(
                students_on_register_testing
            )
        ]
    )

    return student_exam_tickets_df


def swap_name(student_name):
    last_name, first_name = student_name.split(", ")
    return f"{first_name} {last_name}".strip()


def iterate_through_n_lines_at_a_time(input_lst, n):
    for i in range(0, len(input_lst), n):
        yield input_lst[i : i + n]
