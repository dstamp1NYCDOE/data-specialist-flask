import pandas as pd
import numpy as np
from io import BytesIO
from flask import current_app, session

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

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
            name="TITLE75", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=75
        )
    )
    styles.add(
        ParagraphStyle(
            name="TITLE100",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=110,
        )
    )

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
        bottomMargin=0.25 * inch,
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    master_schedule_df = master_schedule_df[master_schedule_df["PD"].isin([1, 2, 3])]
    master_schedule_df = master_schedule_df[
        master_schedule_df["Course Code"].str[0] != "Z"
    ]

    master_schedule_df["Room"] = master_schedule_df["Room"].astype(int)

    if form.teacher.data == "ALL":
        pass
    else:
        master_schedule_df = master_schedule_df[
            master_schedule_df["Teacher Name"] == form.teacher.data
        ]

    flowables = []
    teacher_courses_col = ["Course Name", "PD", "Room"]
    for teacher, courses_df in master_schedule_df.groupby("Teacher Name"):

        courses_df = courses_df.drop_duplicates(subset=["PD"]).sort_values(by=["PD"])

        paragraph = Paragraph(
            f"Summer School {int(school_year)+1} at HSFI", styles["Heading1"]
        )
        flowables.append(paragraph)

        flowables.append(Spacer(width=0, height=1 * inch))
        paragraph = Paragraph(f"HALL PASS", styles["TITLE100"])
        flowables.append(paragraph)
        flowables.append(Spacer(width=0, height=1.5 * inch))

        paragraph = Paragraph(f"{teacher}", styles["TITLE75"])
        flowables.append(paragraph)
        flowables.append(Spacer(width=0, height=1.25 * inch))

        flowables.append(Spacer(width=0, height=1 * inch))
        paragraph = Paragraph(f"Courses", styles["Heading1"])
        flowables.append(paragraph)

        teacher_courses_table = return_df_as_table(
            courses_df, teacher_courses_col, None
        )
        flowables.append(teacher_courses_table)

        flowables.append(PageBreak())

    my_doc.build(flowables)

    f.seek(0)
    return f


def return_df_as_table(df, cols, colWidths):
    table_data = df[cols].values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=colWidths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (100, 100), 15),
                ("RIGHTPADDING", (0, 0), (100, 100), 15),
                ("BOTTOMPADDING", (0, 0), (100, 100), 2),
                ("TOPPADDING", (0, 0), (100, 100), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
            ]
        )
    )
    return t
