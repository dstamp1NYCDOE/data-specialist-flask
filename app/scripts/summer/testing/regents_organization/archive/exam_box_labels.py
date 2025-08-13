import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate

import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]

    cr_1_08_df['ExamTitle'] = cr_1_08_df['Course'].apply(return_exam_title)
    exams_df = cr_1_08_df

    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name",'dbn']]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school",'dbn', "school_name"]]

    exams_df = exams_df.merge(
        cr_s_01_df,
        on='StudentID',
        how='left'
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Normal_RIGHT',
               parent=styles['Normal'], alignment=TA_RIGHT,))
    styles.add(ParagraphStyle(name='Body_Justify',
               parent=styles['BodyText'], alignment=TA_JUSTIFY,))
    styles.add(ParagraphStyle(name='TITLE',
                              parent=styles['BodyText'], alignment=TA_CENTER, fontSize=40, leading=42,))
    styles.add(ParagraphStyle(name='TITLE1',
                              parent=styles['BodyText'], alignment=TA_CENTER, fontSize=90, leading=92,))

    box_labels_lst = []
    table_labels_lst = []
    for (school_name,dbn), students_df in exams_df.groupby(['school_name','dbn']):
        
        exams_pvt_tbl = pd.pivot_table(
            students_df,
            index='ExamTitle',
            values='StudentID',
            aggfunc='count',
            margins=True,
        ).reset_index()
        exams_pvt_tbl.columns = ['Exam Title','# of Students']
        exams_pvt_tbl['✔'] = ''
        
        data = {
            'year':school_year+1,
            'school_name': school_name,
            'dbn':dbn,
            'exams_pvt_tbl': exams_pvt_tbl,
        }
        temp_box_label = return_box_label(data, styles)
        box_labels_lst.extend(temp_box_label)


    
    f = BytesIO()
    my_doc = SimpleDocTemplate(f, 
                               pagesize=landscape(letter), 
                               topMargin=0.75*inch, 
                               leftMargin=0.75*inch, 
                               rightMargin=0.75*inch, 
                               bottomMargin=0.75*inch)

    my_doc.build(box_labels_lst)
    f.seek(0)
    filename = "RegentsBoxLabels.pdf"
    return f, filename



def return_box_label(data, styles):
    temp_flowables = []


    year = data['year']
    exams_pvt_tbl = data['exams_pvt_tbl']
    dbn = data['dbn']
    school_name = data['school_name']
    

    administration_str = f"August{year} Regents Exams -- Discard After August {year+1}"
    paragraph = Paragraph(administration_str, styles["Heading2"])
    temp_flowables.append(paragraph)

    dbn_str = f"{dbn}"
    paragraph = Paragraph(dbn_str, styles["Heading1"])
    temp_flowables.append(paragraph)

    dbn_str = f"Answer Booklets/Essay Booklets and Part 2 sheets -- Part 1 Bubble Sheets at 02M600"
    paragraph = Paragraph(dbn_str, styles["Heading3"])
    temp_flowables.append(paragraph)

    school_name_str = f"{school_name}"
    paragraph = Paragraph(school_name_str, styles["TITLE"])
    temp_flowables.append(paragraph)

    col_widths = [1.75*inch, 1.75*inch, 1.75*inch]
    exams_tbl = return_df_as_table(exams_pvt_tbl,
                                   exams_pvt_tbl.columns,
                                   col_widths
                                   )
    temp_flowables.append(Spacer(width=0*inch, height=0.5*inch))
    temp_flowables.append(exams_tbl)

    temp_flowables.append(PageBreak())
    return temp_flowables


def return_exam_title(course_code):
    exam_title_dict = {
        'EXRCG': 'English',
        'HXRCG': 'Global History',
        'HXRKG': 'US History',
        'MXRCG': 'Algebra',
        'MXRKG': 'Geometry',
        'MXRNG': 'Algebra 2',
        'SXRKG': 'Living Environment',
        'SXRUG': 'Earth Science',
        'SXRXG': 'Chemistry',
    }
    return exam_title_dict.get(course_code,'None')


def return_df_as_table(df, cols, colWidths=None):
    table_data = df[cols].values.tolist()
    table_data.insert(0, cols)
    rowHeights = (len(df)+1) * [25]
    t = Table(table_data, colWidths=colWidths,
              repeatRows=1, rowHeights=rowHeights)
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (100, 100), 'CENTER'),
        ('VALIGN', (0, 0), (100, 100), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (100, 100), 1),
        ('RIGHTPADDING', (0, 0), (100, 100), 1),
        ('BOTTOMPADDING', (0, 0), (100, 100), 1),
        ('TOPPADDING', (0, 0), (100, 100), 1),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    return t

if __name__ == "__main__":
    data = {
        'year':'2023'
    }
    main(data)