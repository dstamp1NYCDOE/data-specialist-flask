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
import pandas as pd  #
import os

from io import BytesIO
from flask import session, current_app

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
from app.scripts import scripts, files_df, photos_df
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


def main(form, request):

    file = request.files[form.student_testing_assignments.name]
    df = pd.read_csv(file)
    df = df.dropna(subset=["StudentID"])

    exam_date = form.exam_date.data
    exam_date = pd.to_datetime(exam_date)

    df["Room#"] = df["Room"].str.extract(r"(\d{3})")
    df = df.fillna({"Room#": "202"})
    df["Session"] = df["Room"].str.extract(r"([AaPp][Mm])")
    df["ExamDate"] = df["Room"].apply(lambda x: exam_date)
    df = df.merge(photos_df, on=["StudentID"], how="left")

    return generate_letters(df)


def generate_letters(df):
    output = []

    df["student_flowbles"] = df.apply(generate_student_letter, axis=1)
    flowables = df["student_flowbles"].explode().to_list()

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


def generate_student_letter(student_row):
    flowables = []

    StudentID = int(student_row["StudentID"])
    student_name = student_row["Student Name"]
    exam_date = student_row["ExamDate"]

    room_num = student_row["Room#"]
    testing_session = student_row["Session"]
    exam_title = student_row["Test Name"]

    paragraph = Paragraph(
        f"{exam_title} Exam Invitation",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{student_name} ({StudentID})",
        styles["Title"],
    )
    flowables.append(paragraph)

    try:
        photo_str = student_row["photo_filename"]
        I = Image(photo_str)
        I.drawHeight = 3.0 * inch
        I.drawWidth = 3.0 * inch
        I.hAlign = "CENTER"
        flowables.append(I)
    except:
        I = ""
        pass

    if testing_session == "PM":
        report_time = "12:00 PM"
    else:
        report_time = "8:15 AM"

    paragraph = Paragraph(
        f"Exam Date: {exam_date.strftime('%A, %B %e, %Y')}",
        styles["Heading1"],
    )
    flowables.append(paragraph)
    paragraph = Paragraph(
        f"Report Time: {report_time}",
        styles["Heading1"],
    )
    flowables.append(paragraph)
    paragraph = Paragraph(
        f"Testing Room: {room_num}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"On test day, being prepared will help you perform your best on the Digital {exam_title}. Here's what you need to bring: (1) Your photo ID (driver's license, school ID, or passport), (2) Snacks and water for breaks and (3) Extra pencils and scratch paper (which will be provided, but having extras doesn't hurt). ",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Before the exam, complete the Bluebook app's practice test to familiarize yourself with the digital format. Get a good night's sleep, eat a nutritious breakfast, and arrive at least 30 minutes early.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Remember, the Digital {exam_title} is adaptive, so pace yourself carefully and answer each question thoughtfully before moving on.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Good luck! You've got this. ",
        styles["BodyText"],
    )
    flowables.append(paragraph)


    flowables.append(PageBreak())
    return flowables
