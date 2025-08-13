from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

from reportlab.graphics import shapes
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

styles.add(
    ParagraphStyle(
        name="Title_LARGE",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=72,
        leading=int(72 * 1.2),
    )
)


import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils

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


    exam_book_df = regents_organization_utils.return_exam_book()
    rooms_df = exam_book_df.drop_duplicates(subset=['Course','Room'])
    flowables = []
    for (course,day,time), exam_rooms_df in rooms_df.groupby(["Course","Day","Time"]):
        exam_title = exam_rooms_df.iloc[0, :]["Exam Title"]
    
        for index, row in exam_rooms_df.sort_values(by=['Room']).iterrows():
            Room = row["Room"]
            paragraph = Paragraph(
                f"Bathroom Pass - {exam_title} - Room {Room} - {day} - {time}",
                styles["Title"],
            )
            flowables.append(paragraph)

            T = return_bathroom_grid()
            flowables.append(T)
            flowables.append(PageBreak())  


    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    
    filename = f"{month}_{school_year+1}_bathroom_logs.pdf"
    
    return f, filename


def return_bathroom_grid(cols=None, colWidths=None, rowHeights=None):

    table_data = [
        ["Student Name", "Time Out", "Time In"],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
        ["", "", ""],
    ]
    colWidths = [4 * inch, 1.5 * inch, 1.5 * inch]
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                # ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t