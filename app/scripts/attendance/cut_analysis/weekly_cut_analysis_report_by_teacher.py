from PyPDF2 import PdfMerger

from io import BytesIO

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate
import PyPDF2

import pandas as pd

from app.scripts.attendance.jupiter.process import main as process_jupiter
def main(form, request):
    week_number = form.week_of.data
    
    student_period_attendance_df = process_jupiter(week_number) 
    
    

    start_date = min(student_period_attendance_df['Date'])
    end_date = max(student_period_attendance_df['Date'])
    dates_covered_by_report = student_period_attendance_df['Date'].unique()
    
    num_of_days = len(dates_covered_by_report)
    

    if start_date == end_date:
        date_of_report = start_date
    else:
        date_of_report = f"{start_date} to {end_date}"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Body_Justify',parent=styles['BodyText'],alignment=TA_JUSTIFY,))

    buffer = BytesIO()
    my_doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.50*inch,
        leftMargin=1.25*inch,
        rightMargin=1.25*inch,
        bottomMargin=0.25*inch
        )

    flowables = []

    students_absent_all_week_df = student_period_attendance_df[
        student_period_attendance_df['num_of_days_absent'] >= num_of_days]

    student_cuts_by_period = student_period_attendance_df[student_period_attendance_df['cutting?']].groupby(['StudentID','Pd','Course'])['Date'].apply(list)
    student_cuts_by_period = pd.DataFrame(student_cuts_by_period).rename(columns={"Date": "Dates Cut"}).reset_index()

    cuts_df = student_period_attendance_df[student_period_attendance_df['cutting?']].sort_values(by=['Teacher','Pd','LastName','FirstName'])
    cuts_df = cuts_df.merge(student_cuts_by_period, on=['StudentID','Pd','Course'], how='left')
    cuts_df["Dates Cut"] = cuts_df["Dates Cut"].apply(lambda x: ', '.join([y[5:] for y in x]))

    cuts_df = cuts_df.drop_duplicates(subset=['StudentID','Course','Section',])

    
    late_to_school_df = student_period_attendance_df[student_period_attendance_df['Type'].isin(['unexcused','tardy'])]
    student_late_to_school_by_period = late_to_school_df[late_to_school_df['late_to_school?']].groupby(['StudentID','Pd','Course'])['Date'].apply(list)
    student_late_to_school_by_period = pd.DataFrame(student_late_to_school_by_period).rename(columns={"Date": "Dates Late to school"}).reset_index()

    late_to_school_df = late_to_school_df[late_to_school_df['late_to_school?']].sort_values(by=['Teacher','Pd','LastName','FirstName'])
    late_to_school_df = late_to_school_df.merge(student_late_to_school_by_period, on=['StudentID','Pd','Course'], how='left')
    late_to_school_df["Dates Late to school"] = late_to_school_df["Dates Late to school"].apply(lambda x: ', '.join([y[5:] for y in x]))

    late_to_school_df = late_to_school_df.drop_duplicates(subset=['StudentID','Course','Section',])

    attd_errors_df = student_period_attendance_df[student_period_attendance_df['attd_error']]
    teachers = student_period_attendance_df['Teacher'].sort_values().unique().tolist()
    for teacher in teachers:

        students_present_in_one_period = attd_errors_df[attd_errors_df['Teacher']==teacher]
        students_with_cuts_df = cuts_df[cuts_df['Teacher']==teacher]
        students_absent_all_week = students_absent_all_week_df[students_absent_all_week_df['Teacher'] == teacher].drop_duplicates(subset=['StudentID'])

        
        students_with_lates_df = late_to_school_df[late_to_school_df['Teacher']==teacher]
        

    
        days_with_attendance_by_teacher = student_period_attendance_df[
            student_period_attendance_df['Teacher'] == teacher]['Date'].unique()
        

        teacher_flowables = return_flowables_by_teacher(
            students_with_cuts_df,students_with_lates_df, students_present_in_one_period, students_absent_all_week, teacher, styles, date_of_report, days_with_attendance_by_teacher, dates_covered_by_report)
        flowables.extend(teacher_flowables)


    lates_to_school_df = student_period_attendance_df[student_period_attendance_df['late_to_school?']]
    lates_to_school_df = lates_to_school_df.drop_duplicates(subset=['StudentID', 'Date'])
    lates_to_school_df = lates_to_school_df[lates_to_school_df['num_of_late_to_school'] >= num_of_days]

    student_days_late = lates_to_school_df.groupby(['StudentID'])['Date'].apply(list)
    student_days_late = pd.DataFrame(student_days_late).rename(columns={"Date": "Dates Late"}).reset_index()
    student_days_late["Dates Late"] = student_days_late["Dates Late"].apply(
        lambda x: ', '.join([y[5:] for y in x]))
    lates_to_school_df = lates_to_school_df.drop_duplicates(subset=['StudentID'])
    lates_to_school_df = lates_to_school_df.merge(student_days_late, on=['StudentID'], how='left')
    lates_to_school_df = lates_to_school_df.sort_values(by=["Dates Late",'LastName','FirstName'])

    group_by_cohort = lates_to_school_df.groupby(['year_in_hs'])

    for (cohort_year,), students_with_lates_df in group_by_cohort:
        flowables.extend(return_flowables_overall_late_to_school(
            cohort_year, students_with_lates_df, styles, date_of_report))
    
    overall_cuts_df = cuts_df[cuts_df['num_of_cuts'] >= num_of_days ].drop_duplicates(subset=['StudentID'])
    overall_cuts_df = overall_cuts_df.sort_values(by=['num_of_cuts','LastName','FirstName'],ascending = [False,True,True])
    group_by_cohort = overall_cuts_df.groupby(['year_in_hs'])

    for (cohort_year,), students_with_cuts in group_by_cohort:
        flowables.extend(return_flowables_overall_cuts_to_school(
            cohort_year, students_with_cuts, styles, date_of_report))

 
    overall_absent_all_week_df = students_absent_all_week_df.sort_values(
        by=['LastName', 'FirstName']).drop_duplicates(subset=['StudentID'])
    group_by_cohort = overall_absent_all_week_df.groupby(['year_in_hs'])

    for (cohort_year,), students_absent_all_week_by_cohort in group_by_cohort:
        flowables.extend(return_flowables_overall_absent_all_week_to_school(
            cohort_year, students_absent_all_week_by_cohort, styles, date_of_report))

    my_doc.build(flowables)
    buffer.seek(0)

    filename = f'JupiterCutReport-{date_of_report}.pdf'


    return buffer, filename


def return_flowables_by_teacher(students_with_cuts_df,students_with_lates_df, students_present_in_one_period, students_absent_all_week, teacher, styles, date_of_report, days_with_attendance_by_teacher, dates_covered_by_report):
    temp_list_of_flowables = []
    paragraph = Paragraph(
        f"{teacher}",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )

    # ## Check for Missing Attendance
    if len(days_with_attendance_by_teacher) < len(dates_covered_by_report):
       paragraph = Paragraph(
        f"You have not submitted all of your Jupiter attendance for {date_of_report}.",
        styles['Body_Justify']
               )
    else:
       paragraph = Paragraph(
        f"Thank you for submitting all of your Jupiter attendance for {date_of_report}.",
        styles['Body_Justify']
               )
       
    temp_list_of_flowables.append(paragraph)
    # temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )     
    ### Cutting
    paragraph = Paragraph(
        f"These students were marked present or tardy in at least two periods during the day {date_of_report}. It is possible they (1) were incorrectly marked present or tardy on this day or (2) cut class, arrived late, left early, or were in another location for the duration of the period. Please confirm your attendance records and speak with student about their location if they were not in class. As necessary, update their attendance from A to E for excused. Log any interactions in the dashboard. If you determine the student was cutting, take appropriate action --- update their attendance from A to C for cut --- and, if this is a repeat offense, submit a discipline referral",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )

    cols = ['LastName','FirstName','Course','Section','Pd','Dates Cut']
    table_data = students_with_cuts_df[cols].values.tolist()
    table_data.insert(0,cols)

    t=Table(table_data, repeatRows=1)
    t.setStyle (TableStyle ([
        ('FONTSIZE', (0, 0), (100, 100), 10),
        ('LEFTPADDING', (0, 0), (100, 100), 1),
        ('RIGHTPADDING', (0, 0), (100, 100), 1),
        ('BOTTOMPADDING', (0, 0), (100, 100), 1),
        ('TOPPADDING', (0, 0), (100, 100), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
        ]))

    temp_list_of_flowables.append(t)

    paragraph = Paragraph(
        f"These students were marked absent or tardy at the beginning of the day and in your class. It is most likely these students arrived to school late.",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )

    cols = ['LastName','FirstName','Course','Section','Pd','Dates Late to school']
    table_data = students_with_lates_df[cols].values.tolist()
    table_data.insert(0,cols)

    t=Table(table_data, repeatRows=1)
    t.setStyle (TableStyle ([
        ('FONTSIZE', (0, 0), (100, 100), 10),
        ('LEFTPADDING', (0, 0), (100, 100), 1),
        ('RIGHTPADDING', (0, 0), (100, 100), 1),
        ('BOTTOMPADDING', (0, 0), (100, 100), 1),
        ('TOPPADDING', (0, 0), (100, 100), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
        ]))

    temp_list_of_flowables.append(t)

    if len(students_present_in_one_period) > 0:
        temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )

        paragraph = Paragraph(
            f"These students were marked present or tardy in only one period on date shown. Please verify your attendance records that the student was in fact present",
            styles['Body_Justify']
        )
        temp_list_of_flowables.append(paragraph)
        temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch) )

        cols = ['LastName','FirstName','Course','Section','Pd','Type','Date']
        table_data = students_present_in_one_period[cols].values.tolist()
        table_data.insert(0,cols)

        t=Table(table_data, repeatRows=1)
        t.setStyle (TableStyle ([
            ('FONTSIZE', (0, 0), (100, 100), 10),
            ('LEFTPADDING', (0, 0), (100, 100), 1),
            ('RIGHTPADDING', (0, 0), (100, 100), 1),
            ('BOTTOMPADDING', (0, 0), (100, 100), 1),
            ('TOPPADDING', (0, 0), (100, 100), 1),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
            ]))

        temp_list_of_flowables.append(t)

    if len(students_absent_all_week) > 0:
        temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

        paragraph = Paragraph(
            f"These students were marked absent for the entire week. Please connect with the student and family",
            styles['Body_Justify']
        )
        temp_list_of_flowables.append(paragraph)
        temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

        cols = ['LastName', 'FirstName','Course', 'Section', 'Pd',]
        table_data = students_absent_all_week[cols].values.tolist()
        table_data.insert(0, cols)

        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (100, 100), 10),
            ('LEFTPADDING', (0, 0), (100, 100), 1),
            ('RIGHTPADDING', (0, 0), (100, 100), 1),
            ('BOTTOMPADDING', (0, 0), (100, 100), 1),
            ('TOPPADDING', (0, 0), (100, 100), 1),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
        ]))

        temp_list_of_flowables.append(t)

    temp_list_of_flowables.append(PageBreak())
    return temp_list_of_flowables


def return_flowables_overall_late_to_school(cohort_year, lates_to_school_df, styles, date_of_report):
    temp_list_of_flowables = []
    paragraph = Paragraph(
        f"{cohort_year}",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    paragraph = Paragraph(
        f"These students were late to school all days between {date_of_report} for {cohort_year}.",
        styles['Body_Justify']
    )

    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    cols = ['LastName', 'FirstName','Counselor']
    table_data = lates_to_school_df[cols].values.tolist()
    table_data.insert(0, cols)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (1000, 1000), 10),
        ('LEFTPADDING', (0, 0), (1000, 1000), 1),
        ('RIGHTPADDING', (0, 0), (1000, 1000), 1),
        ('BOTTOMPADDING', (0, 0), (1000, 1000), 1),
        ('TOPPADDING', (0, 0), (1000, 1000), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
    ]))

    temp_list_of_flowables.append(t)

    temp_list_of_flowables.append(PageBreak())
    
    return temp_list_of_flowables


def return_flowables_overall_absent_all_week_to_school(
        cohort_year, students_absent_all_week_by_cohort, styles, date_of_report):
    temp_list_of_flowables = []
    paragraph = Paragraph(
        f"{cohort_year}",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    paragraph = Paragraph(
        f"These students were absent from school all days between {date_of_report} for {cohort_year} year in High School.",
        styles['Body_Justify']
    )

    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    cols = ['LastName', 'FirstName','Counselor']
    table_data = students_absent_all_week_by_cohort[cols].values.tolist()
    table_data.insert(0, cols)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (1000, 1000), 10),
        ('LEFTPADDING', (0, 0), (1000, 1000), 1),
        ('RIGHTPADDING', (0, 0), (1000, 1000), 1),
        ('BOTTOMPADDING', (0, 0), (1000, 1000), 1),
        ('TOPPADDING', (0, 0), (1000, 1000), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
    ]))

    temp_list_of_flowables.append(t)

    temp_list_of_flowables.append(PageBreak())

    return temp_list_of_flowables

def return_flowables_overall_cuts_to_school(cohort_year, students_with_cuts, styles, date_of_report):
    temp_list_of_flowables = []
    paragraph = Paragraph(
        f"{cohort_year}",
        styles['Body_Justify']
    )
    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    paragraph = Paragraph(
        f"These students have potential cuts between {date_of_report} for {cohort_year} year in high school.",
        styles['Body_Justify']
    )

    temp_list_of_flowables.append(paragraph)
    temp_list_of_flowables.append(Spacer(width=0, height=0.25*inch))

    cols = ['LastName', 'FirstName', 'num_of_cuts','Counselor']
    table_data = students_with_cuts[cols].values.tolist()
    table_data.insert(0, cols)

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (1000, 1000), 10),
        ('LEFTPADDING', (0, 0), (1000, 1000), 1),
        ('RIGHTPADDING', (0, 0), (1000, 1000), 1),
        ('BOTTOMPADDING', (0, 0), (1000, 1000), 1),
        ('TOPPADDING', (0, 0), (1000, 1000), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
    ]))

    temp_list_of_flowables.append(t)

    temp_list_of_flowables.append(PageBreak())

    return temp_list_of_flowables
