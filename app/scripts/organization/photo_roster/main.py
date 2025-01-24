from app.scripts import scripts, files_df, photos_df
from flask import session

from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.enums import TA_JUSTIFY

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=8,
        leading=8,
    )
)

import app.scripts.utils as utils
import pandas as pd
import PyPDF2
import re

import datetime as dt


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    student_subset_title = form.subset_title.data
    today_str = dt.datetime.today().strftime("%Y-%m-%d")
    lst_title = f"{student_subset_title} {today_str}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    students_df = utils.return_file_as_df(filename)
    students_df = students_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]

    student_lst_str = form.subset_lst.data
    student_lst = []
    if student_lst_str != "":
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]

    students_df = students_df[students_df["StudentID"].isin(student_lst)]
    students_df = students_df.sort_values(by=["LastName", "FirstName"])

    students_df = students_df.merge(
        photos_df[["StudentID", "photo_filename"]], on=["StudentID"], how="left"
    )
    photo_roster_pdf = return_photo_roster_pdf(students_df, lst_title)

    filename = f"{lst_title}.pdf"
    return photo_roster_pdf, filename


from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Image


def return_photo_roster_pdf(students_df, lst_title):
    flowables = []

    paragraph = Paragraph(
        f"{lst_title}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    temp_flowables = []
    if len(students_df) <= (10 * 2):
        image_dim = 1.5
        nCols = 2
    elif len(students_df) <= (10 * 3):
        image_dim = 1
        nCols = 3
    else:
        image_dim = 0.75
        nCols = 4

    image_dim = 1
    nCols = 3

    for index, student in students_df.iterrows():
        photo_path = student["photo_filename"]
        try:
            FirstName = student["FirstName"]
            LastName = student["LastName"]
        except:
            FirstName, LastName = student["StudentName"].split(",")

        try:
            I = Image(photo_path)
            I.drawHeight = image_dim * inch
            I.drawWidth = image_dim * inch
            I.hAlign = "CENTER"

        except:
            I = ""

        chart_style = TableStyle(
            [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
        )
        temp_flowables.append(
            Table(
                [
                    [
                        I,
                        [
                            Paragraph(f"{FirstName}", styles["Normal_medium"]),
                            Paragraph(f"{LastName}", styles["Normal_medium"]),
                        ],
                    ]
                ],
                colWidths=[image_dim * inch, image_dim * inch],
                rowHeights=[image_dim * inch],
                style=chart_style,
            )
        )

    B = BalancedColumns(
        temp_flowables,  # the flowables we are balancing
        nCols=nCols,  # the number of columns
        # needed=72,  # the minimum space needed by the flowable
    )
    flowables.append(B)

    f = BytesIO()

    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.1 * inch,
        leftMargin=0.1 * inch,
        rightMargin=0.1 * inch,
        bottomMargin=0.1 * inch,
    )
    my_doc.build(flowables)
    f.seek(0)
    return f
