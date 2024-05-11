import pandas as pd
import numpy as np
import datetime as dt
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from flask import current_app, session

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import SimpleDocTemplate

from reportlab_qrcode import QRCodeImage


def main(data):
    school_year = session["school_year"]
    school_year = int(school_year)+1

    date_of_letter = data['date_of_letter'].strftime('%e %b %Y')
    due_date = data['due_date'].strftime('%B %e, %Y')

    filename = utils.return_most_recent_report(files_df, "4_01")
    student_requests_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(files_df, "code_deck")
    code_deck_df = utils.return_file_as_df(filename)
    
    filename = utils.return_most_recent_report(files_df, "3_07")
    register_raw_df = utils.return_file_as_df(filename)

    
    register_raw_df['year_in_hs'] = register_raw_df['GEC'].apply(return_year_in_hs)

    student_requests_df = student_requests_df[student_requests_df['Course'].str[0:2]!='ZL']

    student_requests_df = student_requests_df.merge(
        code_deck_df[['CourseCode','CourseName','Credits']],
        left_on = ['Course'], right_on = ['CourseCode'],
        how='left'
    )

    student_requests_df = student_requests_df.merge(
        register_raw_df[['StudentID','year_in_hs']],
        on = ['StudentID'],
        how='left'
    )


    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='Normal_RIGHT',
                              parent=styles['Normal'],
                              alignment=TA_RIGHT,
                              ))

    styles.add(ParagraphStyle(name='Body_Justify',
               parent=styles['BodyText'], alignment=TA_JUSTIFY,))

    
    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50*inch,
        leftMargin=1.25*inch,
        rightMargin=1.25*inch,
        bottomMargin=0.25*inch
    )

    letter_head = [
        Paragraph('High School of Fashion Industries', styles['Normal']),
        Paragraph('225 W 24th St', styles['Normal']),
        Paragraph('New York, NY 10011', styles['Normal']),
        Paragraph('Principal, Daryl Blank', styles['Normal']),
    ]

    closing = [
        Spacer(width=0, height=0.25*inch),
        Paragraph('Warmly,', styles['Normal_RIGHT']),
        Paragraph('Derek Stampone', styles['Normal_RIGHT']),
        Paragraph('Assistant Principal, Programming', styles['Normal_RIGHT']),
    ]

    flowables = []

    students_df = student_requests_df[student_requests_df['year_in_hs'] <= 4].sort_values(by=['Counselor','LastName','FirstName'])
    students_df = students_df.groupby(['StudentID', 'LastName', 'FirstName', 'year_in_hs'])

    for group, registered_courses_df in students_df:
        
        StudentID = group[0]
        LastName = group[1]
        FirstName = group[2]
        year_in_hs = group[3]
        list_of_courses = registered_courses_df['Course'].to_list()

        student_name = f"{FirstName.title()} {LastName.title()}"
        student_major = return_CTE_major(list_of_courses)

    
        # Start Flowables
        flowables.append(Spacer(width=0, height=0.5*inch))
        paragraph = Paragraph(f"{date_of_letter}", styles['Normal'])
        flowables.append(paragraph)
        flowables.append(Spacer(width=0, height=0.2*inch))
        flowables.extend(letter_head)
        flowables.append(Spacer(width=0, height=0.2*inch))

        paragraph = Paragraph(f"Dear {student_name} ({StudentID}),",
                              styles['BodyText'])
        flowables.append(paragraph)

        
        paragraph = Paragraph(
            f"It's time to start thinking about your Fall semester coursework. Based on your transcript and enrollment, you have been pre-registered for the following classes you will be in if you take no action:",
                styles['Body_Justify']
        )
        
        flowables.append(paragraph)

        flowables.append(Spacer(width=0, height=0.25*inch))
        flowables.append(return_courses_as_table(registered_courses_df))
        flowables.append(Spacer(width=0, height=0.25*inch))

        paragraph = Paragraph(
            f"Your CTE major is: {student_major}",
            styles['Body_Justify']
        )
        flowables.append(paragraph)

        paragraph = Paragraph(
            "Scan the QR code below to access surveys to:",
            styles['Body_Justify']
        )
        flowables.append(paragraph)

        if year_in_hs > 2:
  
            list_flowable = ListFlowable(
            [
                ListItem(Paragraph('Apply to be on early schedule',
                         styles['Body_Justify']), bulletColor='black', value='square'),
                ListItem(Paragraph(
                    'Indicate interest for advanced coursework such as honors or Advanced Placement', styles['Body_Justify']), bulletColor='black', value='square')
            ],bulletType='bullet')

        else:
            list_flowable = ListFlowable(
                [
                    ListItem(Paragraph('Reapply for your CTE major or change your major',
                                       styles['Body_Justify']), bulletColor='black', value='square'),
                    ListItem(Paragraph(
                        'Indicate interest for advanced coursework such as honors or Advanced Placement', styles['Body_Justify']), bulletColor='black', value='square')
                ], bulletType='bullet')

        flowables.append(list_flowable)

        paragraph = Paragraph(
            f"Complete the surveys by {due_date} to receive priority consideration.",
            styles['Body_Justify']
        )
        flowables.append(paragraph)

        paragraph = Paragraph(
            "Your overall attendance and attending school on time will be a factor in selection.",
            styles['Body_Justify']
        )
        flowables.append(paragraph)

        paragraph = Paragraph(
            "If you have any questions, contact your counselor in the wellness center or attend a Programming Office student office hours.",
            styles['Body_Justify']
        )
        flowables.append(paragraph)

        qr_code_url = f"https://hsfi-data-dashboard.herokuapp.com/programming/fall/surveys?StudentID={StudentID}&year_in_hs={int(year_in_hs)}&year={school_year}&FirstName={FirstName}&LastName={LastName}"

        qr = QRCodeImage(qr_code_url, size=60 * mm)
        qr.hAlign = 'CENTER'
        flowables.append(qr)

        flowables.extend(closing)
        flowables.append(PageBreak())

    my_doc.build(flowables)
    return f


def return_courses_as_table(registered_courses_df):
    cols = ['CourseName']
    table_data = registered_courses_df[cols].values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        # ('FONTSIZE', (0, 0), (100, 100), 11),
        ('LEFTPADDING', (0, 0), (100, 100), 1),
        ('RIGHTPADDING', (0, 0), (100, 100), 1),
        ('BOTTOMPADDING', (0, 0), (100, 100), 1),
        ('TOPPADDING', (0, 0), (100, 100), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
    ]))
    return t


def return_year_in_hs(gec):
    school_year = session["school_year"]
    return utils.return_year_in_hs(gec, school_year) + 1

def return_CTE_major(list_of_courses):

    for fd_course in ['AFS61TF', 'AFS63TD', 'AFS63TDB', 'AFS63TDC',"AFS63TDA", 'AFS65TC', 'AFS65TCH','AFS65TCT']:
        if fd_course in list_of_courses:
            return 'Fashion Design'
    
    for vp_course in ['BMS61TV', 'BMS63TT', 'BMS65TW']:
        if vp_course in list_of_courses:
            return 'Visual Presentation'

    for fmm_course in ['TUS21TA', 'BRS11TF', 'BNS21TV']:
        if fmm_course in list_of_courses:
            return 'Fashion Marketing & Management'

    for wd_course in ['SKS21X', 'TQS21TQW', 'TQS21TQS']:
        if wd_course in list_of_courses:
            return 'Software Development'

    for photo_course in ['ACS21T', 'ACS22T', 'ALS21TP']:
        if photo_course in list_of_courses:
            return 'Photography'

    for a_and_d_course in ['AUS11TA', 'APS11T', 'ACS11TD', 'AES11TE', 'ALS21T']:
        if a_and_d_course in list_of_courses:
            return 'Art and Design'      


