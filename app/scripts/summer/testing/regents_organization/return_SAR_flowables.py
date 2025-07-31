import pandas as pd
import numpy as np
import os
import datetime as dt
from io import BytesIO
from flask import current_app, session

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch, cm
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.flowables import BalancedColumns

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df
from app.scripts.summer import utils as summer_utils

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_small",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=7,
        leading=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=9,
        leading=9,
    )
)


def main(students_df):

    flowables = []
    cols = ["StudentID", "LastName", "FirstName", "photo_filename", "Type"]
    cols_header = ["StudentID", "Last Name", "First Name", "Photo", "Type"]
    colwidths = [1 * inch, 1.5 * inch, 1.5 * inch, 0.75 * inch, 2.25 * inch]

    B = return_balanced_grid_of_class_list(students_df)
    flowables.append(B)
    

    return flowables


def return_balanced_grid_of_class_list(class_list_df):

    flowables = []
    for index, student in class_list_df.iterrows():
        photo_path = student["photo_filename"]
        section_Type = student["Type"]
        FirstName = student["FirstName"]
        LastName = student["LastName"]
        StudentID = student["StudentID"]
        sending_school = student['Sending school']

        try:
            I = Image(photo_path)
            I.drawHeight = 1 * inch
            I.drawWidth = 1 * inch
            I.hAlign = "CENTER"

        except:
            I = ""

        chart_style = TableStyle(
            [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
        )
        flowables.append(
            Table(
                [
                    [
                        I,
                        [
                            Paragraph(
                                f"{FirstName} {LastName}", styles["Normal_medium"]
                            ),
                            Paragraph(f"{StudentID}", styles["Normal_small"]),
                            Paragraph(f"{sending_school}", styles["Normal_small"]),
                            Paragraph(str(section_Type), styles["Normal_small"]),
                        ],
                    ]
                ],
                colWidths=[1 * inch, 1 * inch],
                rowHeights=[1 * inch],
                style=chart_style,
            )
        )

    B = BalancedColumns(
        flowables,  # the flowables we are balancing
        nCols=3,  # the number of columns
        # needed=72,  # the minimum space needed by the flowable
    )
    return B
