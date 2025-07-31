
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
   
    MATERIAL = 'Bathroom_Passes'
    if course != 'All':
        exam_book_df = exam_book_df[exam_book_df["Course Code"] == course]
    download_name = f"{administration}_{course}_{MATERIAL}.pdf"


    registered_students_df = cr_1_08_df[cr_1_08_df["Status"]]
    registered_students_df = registered_students_df[
        ["StudentID", "LastName", "FirstName", "Course", "Section"]
    ]
    
    students_per_section_df = pd.pivot_table(
        registered_students_df,
        index=["Course", "Section"],
        values="StudentID",
        aggfunc="count",
    ).reset_index()
    students_per_section_df.columns = ["Course Code", "Section", "#_of_students"]

    exam_book_df = exam_book_df.merge(
        students_per_section_df, on=["Course Code", "Section"], how="left"
    ).fillna(0)
    exam_book_df["#_of_students"] = exam_book_df["#_of_students"].apply(
        lambda x: int(x)
    )


    exam_flowables = []
    for (day, time, course), exam_rooms_df in exam_book_df.drop_duplicates(
        subset=["Course Code", "Room"]
    ).groupby(["Day", "Time", "Course Code"]):
        exam_title = exam_rooms_df.iloc[0, :]["ExamTitle"]
        day_as_str = pd.to_datetime(day).strftime("%Y-%m-%d")
        for index, row in exam_rooms_df.iterrows():
            Room = row["Room"]
            paragraph = Paragraph(
                f"Bathroom Pass - {exam_title} - Room {Room} - {day} - {time}",
                styles["Title"],
            )
            exam_flowables.append(paragraph)

            T = return_bathroom_grid()
            exam_flowables.append(T)
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