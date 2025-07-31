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

import app.scripts.utils.utils as utils
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


def return_attendance_benchmark_letters(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    
    PRESENT_STANDARD = form.in_class_percentage.data
    ON_TIME_STANDARD = form.on_time_percentage.data

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    rosters_df = utils.return_file_as_df(filename)
    

    filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule",year_and_semester=year_and_semester)
    schedule_df = utils.return_file_as_df(filename)
    schedule_df["Pd"] = schedule_df["Period"].apply(utils.return_pd)
    
    rosters_df = rosters_df[['StudentID','Course','Section']].drop_duplicates()

    rosters_df = rosters_df.merge(schedule_df[['Course','Section','Pd','CourseTitle']], on=['Course','Section'], how='left')


    attendance_df = attendance_benchmark.main(PRESENT_STANDARD, ON_TIME_STANDARD)
    print(attendance_df)
    
    attendance_df = attendance_df.merge(rosters_df, left_on=['StudentID','Pd'], right_on=['StudentID','Pd'], how='left')
    
    flowables = []
    for index, student_info in cr_3_07_df.iterrows():
        
        StudentID = student_info["StudentID"]
        df = attendance_df[attendance_df['StudentID']==StudentID]
        df = df.drop_duplicates(subset=['Term','Pd'])

        first_name = student_info["FirstName"]
        last_name = student_info["LastName"]

        student_pd_df_cols = [
            "Term",
            "Pd",
            "CourseTitle",
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

        student_eligibility_df_cols = ["Term", "overall_meet_attd_standard"]
        student_eligibility_df = df[student_eligibility_df_cols]
        student_eligibility_df = student_eligibility_df.drop_duplicates(subset=["Term"])
        student_eligibility_df_table = utils.return_df_as_table(student_eligibility_df)

        

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

    return f, f"Attendance Benchmark Letters"
