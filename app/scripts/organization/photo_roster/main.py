import pandas as pd

from werkzeug.utils import secure_filename

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re

from app.scripts import scripts, files_df, photos_df


def main(form, request):


from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Image


def return_photo_roster_pdf(sort_by, students_df, student_roster_table_cols):
    flowables = []

    paragraph = Paragraph(
        f"{sort_by}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    temp_flowables = []
    if len(students_df) <= (9 * 2):
        image_dim = 1.5
        nCols = 2
    elif len(students_df) <= (9 * 3):
        image_dim = 1
        nCols = 3
    else:
        image_dim = 0.75
        nCols = 4
    for index, student in students_df.iterrows():
        photo_path = student["photo_filename"]
        try:
            FirstName = student["FirstName"]
            LastName = student["LastName"]
        except:
            FirstName, LastName = student['StudentName'].split(',')

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
        topMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    pdfReader = PyPDF2.PdfReader(f)
    pdfPage = pdfReader.pages[0]
    return pdfPage
