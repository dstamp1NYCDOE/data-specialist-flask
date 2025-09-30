
import pandas as pd
import numpy as np
import os
import re
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


from io import BytesIO


from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import PageTemplate
from reportlab.platypus.frames import Frame

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
styles = getSampleStyleSheet()

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]

    ## flags
    check_INC = form.check_INC.data
    parts_to_check = form.parts_to_check.data
    check_part1 = 'Part1' in parts_to_check
    check_part2 = 'Part2' in parts_to_check

    reds_file = request.files[form.reds_xlsx.name]
    REDS_df = pd.read_excel(reds_file,skiprows=[0,1,2,4])
    REDS_df=REDS_df.fillna('')

    ## exam_info
    exam_info =  pd.read_excel(reds_file,nrows=1).iloc[0].values[0]
    pattern = r'\b[A-Z]XR[A-Z0-9]\b'
    exam_code = re.search(pattern, exam_info).group()
    exam_name = return_exam_name(exam_code)
    

    ### Import Answerkey
    answerkey_df = pd.read_excel(reds_file,skiprows=[0,1,2],nrows=1)
    answerkey_df=answerkey_df.transpose()
    answerkey_df.columns = answerkey_df.iloc[0]
    answerkey_df=answerkey_df.dropna()
    answerkey_df=answerkey_df.drop('Questions:')
    answerkey_df = answerkey_df.reset_index()
    answerkey_df.columns = ['Question', 'Answer']
    answerkey_df=answerkey_df.dropna()
    

    ## MC Questions
    mc_questions = answerkey_df[answerkey_df['Answer']!='*']['Question'].tolist()
    ## Short Response Questions
    cr_questions = answerkey_df[answerkey_df['Answer']=='*']['Question'].tolist()

    ## possible errors
    if check_INC:
        errors_df = REDS_df[(REDS_df['Errors']!='') | (REDS_df['Final Score'] == 'INC')]
    else:
        errors_df = REDS_df[REDS_df['Errors']!='']

    ## process error resolution
    errors_df['Part1Resolution'] = errors_df.apply(
        lambda row: determine_error_Part1Resolution(row, mc_questions, cr_questions), axis=1
    )
    errors_df['Part2Resolution'] = errors_df.apply(
        lambda row: determine_error_Part2Resolution(row, mc_questions, cr_questions), axis=1
    )

    part1_cols = ['Student Id', 'Name','Section','Room Num','Errors','Scan Date','Scan Date 2','Multi Scan','Part1Resolution']
    part2_cols = ['Student Id', 'Name','Section','Room Num','Errors','Scan Date','Scan Date 2','Multi Scan','Part2Resolution']
    inc_cols = ['Student Id', 'Name','Section','Room Num','Errors','Scan Date','Scan Date 2','Multi Scan','Final Score']
    part_1_errors_flowables = []
    part_2_errors_flowables = []
    inc_error_flowables = []
    for section, errors_by_section in errors_df.groupby('Section'):

        part_1_errors = errors_by_section[errors_by_section['Part1Resolution'] != '' ][part1_cols]
        part_2_errors = errors_by_section[errors_by_section['Part2Resolution'] != '' ][part2_cols]
        

        if len(part_1_errors) > 0 and check_part1:
            paragraph = Paragraph(f"Part 1 Errors {exam_code}/{section} ({exam_name})",styles["Title"],)
            part_1_errors_flowables.append(paragraph) 
            part_1_errors_table = return_df_as_table(part_1_errors)
            part_1_errors_flowables.append(part_1_errors_table)
            part_1_errors_flowables.append(PageBreak())
        if len(part_2_errors) > 0 and check_part2:
            paragraph = Paragraph(f"Part 2 Errors {exam_code}/{section} ({exam_name})",styles["Title"],)
            part_2_errors_flowables.append(paragraph)            
            part_2_errors_table = return_df_as_table(part_2_errors)
            part_2_errors_flowables.append(part_2_errors_table)
            part_2_errors_flowables.append(PageBreak())

    inc_errors = errors_df[errors_df['Final Score'] == 'INC'][inc_cols]
    if len(inc_errors) > 0 and check_INC:
        paragraph = Paragraph(f"INC Errors ({exam_name})",styles["Title"],)
        inc_error_flowables.append(paragraph)            
        inc_errors_table = return_df_as_table(inc_errors)
        inc_error_flowables.append(inc_errors_table)
        inc_error_flowables.append(PageBreak())

    flowables = part_1_errors_flowables + part_2_errors_flowables + inc_error_flowables

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)
    f.seek(0)
    filename = f"{exam_code}_REDS_Error_Analysis_{school_year}_{term}.pdf"

    return f, filename

def determine_error_Part1Resolution(student_row,mc_questions,cr_questions):
    error_code = student_row['Errors']
    Final_Score = student_row['Final Score']
    num_omitted = student_row['Omitted']
    num_of_mc_questions = len(mc_questions)

    mc_questions = student_row[mc_questions]
    omits = mc_questions[mc_questions == 'X'].index.tolist()
    multiples = mc_questions[mc_questions == 'M'].index.tolist()

    resolution_text = ""
    if Final_Score == 'INC':
        resolution_text = "INC\n"

    if '042' in error_code and num_omitted == num_of_mc_questions:
        resolution_text += "Student likely absent, but not bubbled absent. \n Check bubble sheet, bubble absent if needed, and rescan."
    if '042' in error_code and num_omitted < num_of_mc_questions:
        resolution_text += f"Student omitted questions {omits}\nCheck bubble sheet to confirm omitts are valid. \n If not, communicate with Testing Office\n"
    if '041' in error_code:
        resolution_text += f"Student multiple response to questions {multiples}\nCheck bubble sheet to confirm multiples are valid. \n If not, communicate with Testing Office\n"
    if '040' in error_code:
        resolution_text += f"Student bubbles absent + MC answer entered. \n Check for errant absent bubble and if a second Part1 document was scanned.\n"



    return resolution_text


def determine_error_Part2Resolution(student_row,mc_questions,cr_questions):
    error_code = student_row['Errors']


    cr_questions = student_row[cr_questions]
    omits = cr_questions[cr_questions == ''].index.tolist()

    resolution_text = ""

    if '043' in error_code:
        resolution_text += "Multiples in Alt Langage designation\nCheck records and correct Bubbles on Part 2 document and Rescan"
    if '046' in error_code:
        resolution_text += "Multiples in Teacher Answers\nCorrect and rescan Part 2"
    if '047' in error_code:
        resolution_text += f"Omits {omits}in teacher responses\nCorrect and rescan Part 2"

    return resolution_text

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
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t

def return_exam_name(exam_code):
    exam_dict = {
        "MXRF": "Alg1",
        "MXRN": "Alg2",
        "MXRJ": "Geo",
        "SXR3": "Bio",
        "SXR2": "ESS",
        "SXRU":"ES",
        "SXRK":"LE",
        "SXRX":"Chem",
        "EXRC":"ELA",
        "HXRC":"Global History",
        "HXRK":"USH",
    }
    return exam_dict.get(exam_code, "")