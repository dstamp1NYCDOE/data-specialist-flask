from reportlab.graphics import shapes
from reportlab_qrcode import QRCodeImage

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

import datetime as dt
import pandas as pd  #
import os

from io import BytesIO
from flask import session, current_app

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from app.scripts.pbis.smartpass.main import process_smartpass_data, return_total_time_per_period_by_student

from app.scripts.pbis.smartpass.return_student_period_usage_graph import main as return_student_period_usage_graph

def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.smartpass_file.name]
    date_of_interest = form.date_of_interest.data

    smartpass_df = pd.read_csv(filename)
    smartpass_df = process_smartpass_data(smartpass_df)
    df = return_total_time_per_period_by_student(smartpass_df)
    df = df.iloc[1:,:]

    ## pull in parent code
    codes_df = return_parent_codes()
    df = df.merge(codes_df, on='StudentID', how='left').head(214)

    f = generate_letters(df)
    download_name = f"SmartPassParentLetters.pdf"

    return f, download_name

def return_parent_codes():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    filename = utils.return_most_recent_report_by_semester(files_df, "SmartPassParentInviteCodes",year_and_semester=year_and_semester)
    codes_df = utils.return_file_as_df(filename)
    filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    students_df = utils.return_file_as_df(filename)

    codes_df = codes_df[['Student Email/Username','Student Invite Code']].merge(students_df[['Student DOE Email','StudentID','FirstName','LastName']], left_on=['Student Email/Username'], right_on=['Student DOE Email'], how='right')
    codes_df = codes_df[['StudentID','Student Invite Code','FirstName','LastName']]
    
    return codes_df

from datetime import timedelta

def return_class_period_equivalence(sec):
    return f"{round(sec/(45*60))}"

def get_time_hh_mm_ss(sec):
    td_str = str(timedelta(seconds=sec))
    x = td_str.split(':')
    return f"{x[0]} hours and {x[1]} minutes"

def get_time_hh_mm_ss_short(sec):
    td_str = str(timedelta(seconds=sec))
    x = td_str.split(':')
    return f"{x[0]} hrs, {x[1]} min"

def generate_letter_flowables(row):
    flowables = []
    flowables.extend(reportlab_letter_head)

    parent_code = row['Student Invite Code']

    first_name = str(row['FirstName']).title()
    last_name = str(row["LastName"]).title()
    StudentID = row["StudentID"]



    total_time_str = get_time_hh_mm_ss(row['Total'])
    class_periods_equivalent_str = return_class_period_equivalence(row['Total'])

    table_data = [
        [1,2,3,4,5,6,7,8,9],
        [get_time_hh_mm_ss_short(row[1.0]),get_time_hh_mm_ss_short(row[2.0]),get_time_hh_mm_ss_short(row[3.0]),get_time_hh_mm_ss_short(row[4.0]),get_time_hh_mm_ss_short(row[5.0]),get_time_hh_mm_ss_short(row[6.0]),get_time_hh_mm_ss_short(row[7.0]),get_time_hh_mm_ss_short(row[8.0]),get_time_hh_mm_ss_short(row[9.0])]    
    ]

    

    paragraphs = [
        f"Dear Parent/Guardian of {first_name} {last_name} ({int(StudentID)})",
        "To provide a safe learning environment for our students, HSFI has partnered with SmartPass to be our hall pass system. Students have full ownership to writing passes from kiosks in the classrooms to go to the bathroom and visit adults when they need help. The system monitors pass usage at these locations to keep them under control. And the data helps us ensure students are maximizing these instructional time in class as they become college and career ready.",
        "Students can use up to 3 passes per day and each bathroom pass is for up to 8 minutes.",
        f"Since the beginning of the school year, {first_name} has missed {total_time_str} of classtime -- this is equivalent to {class_periods_equivalent_str} class periods",
        "The chart below shows the amount of time missed per class period.",
        
    ]

    flowables.extend(
        [
            Paragraph(
                x,
                styles["BodyText"],
            ) for x in paragraphs
        ]
    )

    t = Table(table_data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    # flowables.append(Spacer(width=0, height=0.25 * inch))
    # flowables.append(t)
    # flowables.append(Spacer(width=0, height=0.25 * inch))

    I = return_student_period_usage_graph(row)
    flowables.append(I)

    paragraphs = [
        "Our classes are best and our students learn the most when everyone is present and engaged for the entire class period.",
        f"To see {first_name}'s pass usage, go to http://smartpass.app/app/parent-sign-up and sign up for an account with your email and password. Once you’ve signed in, you’re redirected to the Parent Dashboard where you can add your child(ren) using an invite code -- <b><code>{parent_code}</code></b>. If you have multiple children at HSFI, add each of their invite codes to your account.",
    ]

    flowables.extend(
        [
            Paragraph(
                x,
                styles["BodyText"],
            ) for x in paragraphs
        ]
    )


    flowables.extend(reportlab_closing)
    flowables.append(PageBreak())
    return flowables


def generate_letters(df):
    output = []

    df["student_flowbles"] = df.apply(generate_letter_flowables, axis=1)
    flowables = df["student_flowbles"].explode().to_list()

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=1 * inch,
        leftMargin=1.5 * inch,
        rightMargin=1.5 * inch,
        bottomMargin=1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f