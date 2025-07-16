import pandas as pd
from app.scripts import scripts, files_df, gsheets_df
from flask import render_template, request, send_file, session, current_app
from io import BytesIO
from reportlab.graphics import shapes
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
import app.scripts.utils as utils
import datetime as dt

import labels

import pandas as pd

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.fonts import tt2ps
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

import labels
from reportlab.graphics import shapes

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


def main(course, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        administration = f"January {school_year+1}"
    elif term == 2:
        administration = f"June {school_year+1}"

    gsheet_url = utils.return_gsheet_url_by_title(
        gsheets_df, "regents_exam_book", year_and_semester
    )

    exam_book_df = utils.return_google_sheet_as_dataframe(gsheet_url, sheet="ExamBook")

    cr_1_08_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_08", year_and_semester=year_and_semester
    )
    cr_1_08_df = pd.read_csv(cr_1_08_filename)
    
    MATERIAL = 'Checkout_Roster'
    if course != 'All':
        exam_book_df = exam_book_df[exam_book_df["Course Code"] == course]
    download_name = f"{administration}_{course}_{MATERIAL}.pdf"


    registered_students_df = cr_1_08_df[cr_1_08_df["Status"]]
    registered_students_df = registered_students_df[
        ["StudentID", "LastName", "FirstName", "Course", "Section"]
    ]
    
    
    registered_students_df = registered_students_df.merge(
        exam_book_df,
        left_on=["Course", "Section"],
        right_on=["Course Code", "Section"],
        how="left",
    )

    registered_students_df['No Double\nBubbles'] = registered_students_df['StudentID'].apply(
        lambda x: "[_]")
    registered_students_df['No Missing\nBubbles'] = registered_students_df['StudentID'].apply(
        lambda x: "[_]")   
    registered_students_df['Finish Time\n(HH:MM)'] = registered_students_df['StudentID'].apply(
        lambda x: "")
    registered_students_df['Proctor\nInitials'] = registered_students_df['StudentID'].apply(
        lambda x: "") 
    registered_students_df['Any Testing Irregularities     '] = registered_students_df['StudentID'].apply(
        lambda x: "")           

    roster_T_cols = ["StudentID", "LastName", "FirstName",'No Double\nBubbles','No Missing\nBubbles',"Finish Time\n(HH:MM)","Proctor\nInitials","Any Testing Irregularities     "]
    exam_flowables = []
    for (
        day,
        time,
        exam_title,
        course,
    ), exam_registrations_df in registered_students_df.groupby(
        ["Day", "Time", "ExamTitle","Course"]
    ):
        for section, exam_section_registrations_df in exam_registrations_df.groupby("Section"):
            if section < 80:
                paragraph = Paragraph(
                    f"{exam_title} - {course}/{section} - Student Checkout Roster",
                    styles["Title"],
                )
                exam_flowables.append(paragraph)

                paragraph = Paragraph(
                    f"Use this checklist when checking a student out and recording any irregularities.",
                    styles["Normal"],
                )
                exam_flowables.append(paragraph)

                
                roster_T = return_df_as_table(
                    exam_section_registrations_df, cols=roster_T_cols
                )
                exam_flowables.append(roster_T)
                exam_flowables.append(PageBreak())
            elif section in [87,89]:
                for student, df in exam_section_registrations_df.groupby("StudentID"):
                    paragraph = Paragraph(
                        f"{exam_title} - {section} - Student Checkout Roster for {df.iloc[0]['LastName']}, {df.iloc[0]['FirstName']}",
                        styles["Title"],
                    )
                    exam_flowables.append(paragraph)

                    paragraph = Paragraph(
                        f"Use this checklist when checking a student out and recording any irregularities.",
                        styles["Normal"],
                    )
                    exam_flowables.append(paragraph)

                    
                    roster_T = return_df_as_table(
                        df, cols=roster_T_cols
                    )
                    exam_flowables.append(roster_T)
                    exam_flowables.append(PageBreak())
            

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(exam_flowables)
    f.seek(0)

    return f, download_name


def return_df_as_table(df, cols=None, colWidths=None, rowHeights=None):
    if cols:
        table_data = df[cols].values.tolist()
    else:
        cols = df.columns
        table_data = df.values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ]
        )
    )
    return t
