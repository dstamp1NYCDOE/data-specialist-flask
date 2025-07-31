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
from reportlab_qrcode import QRCodeImage

import datetime as dt
from io import BytesIO
import pandas as pd
import math
import json

from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df
from app.scripts.date_to_marking_period import return_mp_from_date

from app.scripts.privileges.attendance_benchmark import attendance_benchmark

from app.api_1_0.students import return_student_info

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

letter_head = [
    Paragraph("High School of Fashion Industries", styles["Normal"]),
    Paragraph("225 W 24th St", styles["Normal"]),
    Paragraph("New York, NY 10011", styles["Normal"]),
    Paragraph("Principal, Daryl Blank", styles["Normal"]),
]

closing = [
    Spacer(width=0, height=0.25 * inch),
    Paragraph("Warmly,", styles["Normal_RIGHT"]),
    Paragraph("Derek Stampone", styles["Normal_RIGHT"]),
    Paragraph("Assistant Principal, Attendance", styles["Normal_RIGHT"]),
]


def return_student_letter(form, request):
    school_year = session["school_year"]

    StudentID = int(form.StudentID.data)

    PRESENT_STANDARD = form.in_class_percentage.data
    ON_TIME_STANDARD = form.on_time_percentage.data

    student_info = json.loads(return_student_info(StudentID).data)[0]

    first_name = student_info["FirstName"]
    last_name = student_info["LastName"]

    df = attendance_benchmark.main(PRESENT_STANDARD, ON_TIME_STANDARD)
    df = df[df["StudentID"] == StudentID]

    student_pd_df_cols = [
        "Term",
        "Pd",
        "excused",
        "present",
        "tardy",
        "unexcused",
        "total",
        "%_present",
        "%_on_time",
        "meet_attd_standard",
    ]

    student_pd_df = df[student_pd_df_cols]
    student_pd_table = utils.return_df_as_table(student_pd_df)

    # table_style = TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")])
    # for (
    #     row,
    #     values,
    # ) in enumerate(student_pd_df.values.tolist()):
    #     for column, value in enumerate(values):
    #         if value == False:
    #             table_style.add("TEXTCOLOR", (column, row), (column, row), colors.red)
    # student_pd_table.setStyle(table_style)

    student_eligibility_df_cols = ["Term", "overall_meet_attd_standard"]
    student_eligibility_df = df[student_eligibility_df_cols]
    student_eligibility_df = student_eligibility_df.drop_duplicates(subset=["Term"])
    student_eligibility_df_table = utils.return_df_as_table(student_eligibility_df)

    flowables = []

    paragraph = Paragraph(
        f"{first_name.title()} {last_name.title()} ({StudentID})",
        styles["Heading1"],
    )
    flowables.append(paragraph)
    paragraph = Paragraph(
        f"Attendance Benchmark Data - Present {PRESENT_STANDARD}% & On Time {ON_TIME_STANDARD}%",
        styles["Heading2"],
    )
    flowables.append(paragraph)

    flowables.append(student_eligibility_df_table)
    flowables.append(student_pd_table)

    flowables.append(PageBreak())
    attd_grid_df = attendance_benchmark.return_attd_grid(StudentID)
    student_attd_grid_table = utils.return_df_as_table(attd_grid_df)
    table_style = TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")])
    student_attd_grid_table.setStyle(table_style)

    # flowables.append(student_attd_grid_table)

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    return f, f"{first_name.title()}_{last_name.title()}"
