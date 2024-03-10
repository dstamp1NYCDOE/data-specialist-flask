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

    df["Room#"] = df["Room"].str.extract(r"(\d{3})")
    df["Session"] = df["Room"].str.extract(r"([AaPp][Mm])")

    print(df)

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

    if testing_session == "AM":
        report_time = "8:15 AM"
    if testing_session == "PM":
        report_time = "12:15 AM"

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

    flowables.append(PageBreak())
    return flowables
