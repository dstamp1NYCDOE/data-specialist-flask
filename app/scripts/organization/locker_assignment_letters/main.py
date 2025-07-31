import pandas as pd
import numpy as np
import os
from io import BytesIO
from io import StringIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.units import mm, inch
from reportlab.lib.pagesizes import letter

def return_locker_assignment_letters(form, request):
    school_year = session["school_year"]
    term = session["term"]

    locker_assignment_csv = request.files[
        form.locker_assignment_csv.name
    ]
    lockers_assignment_df = pd.read_csv(
        locker_assignment_csv
    )

    lockers_assignment_df = lockers_assignment_df.dropna(subset=['StudentID'])

    lockers_assignment_df['flowables'] = lockers_assignment_df.apply(return_student_letter_flowables,axis=1)


    flowables = lockers_assignment_df["flowables"].explode().to_list()

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

    filename = "LockerAssignmentLetters.pdf"

    return f, filename

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
    ListItem
)

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

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
def return_student_letter_flowables(student_row):
    flowables = []

    StudentID = int(student_row["StudentID"])
    FirstName = student_row["FirstName"]
    LastName = student_row["LastName"]
    LockerNumber = student_row['LockerNumber']
    combo = student_row['combo']

    StudentName = f"{FirstName.title()} {LastName.title()}"
    
    flowables.extend(reportlab_letter_head)

    paragraph = Paragraph(
        f"Dear {StudentName} ({StudentID}),",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"You have been assigned to the following locker",
        styles["BodyText"],
    )

    flowables.append(paragraph)


    flowables.append(Paragraph(f"Locker: {LockerNumber}",styles["BodyText"],))
    flowables.append(Paragraph(f"Combo: {combo}",styles["BodyText"],))

    flowables.append(Paragraph(f"By requesting a locker, you agreed to the Locker User Agreement.",styles["BodyText"],))

    list_flowable = ListFlowable(
    [
        ListItem(Paragraph("Lockers are the school's property, and the administrative staff has the authority to govern their proper use. Lockers are school property and can be searched at any time.",styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('Lockers and locks are assigned to individual students. Students may not swap or share lockers or locks.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('Locks may not be removed, substituted, or exchanged.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('If a lock is lost, a replacement lock will be supplied at the cost of $3.00. ',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('If a lock is broken, a replacement lock will be supplied at no charge.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('Lockers are to remain sticker and graffiti-free.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('Contraband (such as illegal drugs, weapons (real or otherwise), or alcoholic beverages) is not permitted in the school building and may not be stored in lockers.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('The student is responsible for safeguarding lockers and their contents.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('I understand the locker policy and will abide by the user agreement above.',styles['Body_Justify']), bulletColor='black', value='square'),
        ListItem(Paragraph('I understand that I will have my locker and other privileges revoked if I am found to be violating the user agreement.',styles['Body_Justify']), bulletColor='black', value='square'),
    ],bulletType='bullet')


    flowables.append(list_flowable)


    flowables.append(Paragraph(f"Students with any locker related issues should report them to the peace center (149) and Mr. Raschilla",styles["BodyText"],))










    flowables.append(PageBreak())
    return flowables