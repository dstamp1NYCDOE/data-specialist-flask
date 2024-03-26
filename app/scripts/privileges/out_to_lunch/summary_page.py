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

from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df
from app.scripts.date_to_marking_period import return_mp_from_date

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

def return_student_letter(form,request):
    school_year = session["school_year"]
    
    StudentID = int(form.StudentID.data)

    first_name = ''
    last_name = ''

    

    jupiter_attd_filename = utils.return_most_recent_report(files_df, "jupiter_period_attendance")
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)    
    

    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(return_mp_from_date, args=(school_year,))

    
    
    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    ## exclude SAGA
    attendance_marks_df = attendance_marks_df[~attendance_marks_df['Course'].isin(['MQS22','MQS21'])]       


    student_attd_marks_df = attendance_marks_df[attendance_marks_df['StudentID']==StudentID]
    student_attd_pvt = pd.pivot_table(student_attd_marks_df,index=['Term','Pd'],columns='Type',values='Date',aggfunc='count').fillna(0)
    student_attd_pvt['total'] = student_attd_pvt.sum(axis=1)
    student_attd_pvt['%_present'] = 100*(1-student_attd_pvt['unexcused']/student_attd_pvt['total'])
    student_attd_pvt['%_on_time'] = 100*student_attd_pvt['present']/(student_attd_pvt['present'] + student_attd_pvt['tardy'])

    for standard in ['%_present','%_on_time']:
        student_attd_pvt[standard] = student_attd_pvt[standard].apply(lambda x: math.ceil(x))
    
    ## meets present + on time standard
    PRESENT_STANDARD = 90
    ON_TIME_STANDARD = 80

    student_attd_pvt['meeting_present_standard'] = student_attd_pvt['%_present'] >= PRESENT_STANDARD
    student_attd_pvt['meeting_on_time_standard'] = student_attd_pvt['%_on_time'] >= ON_TIME_STANDARD
    student_attd_pvt['meet_attd_standard'] = student_attd_pvt['meeting_present_standard'] & student_attd_pvt['meeting_on_time_standard']

    print(student_attd_pvt)

    flowables = []

    flowables.extend(letter_head)
    paragraph = Paragraph(
        f"Dear {first_name.title()} {last_name.title()} ({StudentID})",
        styles["BodyText"],
    )
    flowables.append(paragraph)


    flowables.extend(closing)


    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    return f
