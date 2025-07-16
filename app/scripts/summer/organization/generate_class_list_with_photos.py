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


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    timestamp = os.path.getctime(filename)
    cr_1_01_date = dt.date.fromtimestamp(timestamp)
    generated_string = f"Program generated: {cr_1_01_date}"
    


    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )


    student_programs_df = summer_utils.return_summer_class_lists()

    
    TEACHER_NAME = form.teacher.data
    if TEACHER_NAME == "ALL":
        download_name = f"Summer{school_year+1}_ClassList_With_Photos.pdf"
    else:
        download_name = f"Summer{school_year+1}_ClassList_With_Photos_{TEACHER_NAME}.pdf"
        student_programs_df = student_programs_df[
            student_programs_df["Teacher1"] == TEACHER_NAME
        ]

    flowables = []
    cols = ['StudentID','LastName','FirstName','photo_filename',"school_name"]
    cols_header = ['StudentID','Last Name', 'First Name', 'Photo', 'Sending School']
    colwidths = [1*inch,1.5*inch,1.5*inch,0.75*inch,2.25*inch]

    for (teacher,period,cycle), class_list_df in student_programs_df.groupby(["Teacher1","Period","Cycle"]):
        course = class_list_df.iloc[0]["Course Name"]
        paragraph = Paragraph(
            f"Summer School {int(school_year)+1} at HSFI --- {generated_string}", styles["Heading2"]
        )
        flowables.append(paragraph)
        paragraph = Paragraph(
            f"{teacher} - {cycle} - Period {period} - {course}", styles["Heading3"]
        )
        flowables.append(paragraph)
        
        B = return_balanced_grid_of_class_list(class_list_df)
        flowables.append(B)

        flowables.append(PageBreak())

    my_doc.build(flowables)

    f.seek(0)

    
    return f, download_name

def return_balanced_grid_of_class_list(class_list_df):
    
    flowables = []
    for index, student in class_list_df.iterrows():
        photo_path = student['photo_filename']
        home_school = student['school_name']
        FirstName = student['FirstName']
        LastName = student['LastName']
        StudentID = student['StudentID']
        
        try:
            I = Image(photo_path)
            I.drawHeight = 1.2 * inch
            I.drawWidth = 1.2 * inch
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
                            Paragraph(f"{FirstName} {LastName}", styles['Normal_medium']),
                            Paragraph(f"{StudentID}", styles['Normal_small']),
                            Paragraph(home_school, styles['Normal_small'])
                        ],
                    ]
                ],
                colWidths=[1.2 * inch,  0.9* inch],
                rowHeights=[1.2 * inch],
                style=chart_style,
            )
        )

    B = BalancedColumns(
        flowables,  # the flowables we are balancing
        nCols=3,  # the number of columns
        # needed=72,  # the minimum space needed by the flowable
    )
    return B   
