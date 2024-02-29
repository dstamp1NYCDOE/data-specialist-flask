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

import datetime as dt

from io import BytesIO
from flask import session

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
import app.scripts.utils as utils

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

signup_url = "https://cbaccount.collegeboard.org/iamweb/smartRegister"
signup_url_qr_code = QRCodeImage(
    signup_url,
    size=2 * inch,
)

def generate_letters(cr_3_07_df):
    output = []
    cr_3_07_df = process_3_07_df(cr_3_07_df)
    cr_3_07_df["student_flowbles"] = cr_3_07_df.apply(generate_student_letter, axis=1)
    flowables = cr_3_07_df["student_flowbles"].explode().to_list()

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

def generate_student_letter(student_row):
    flowables = []
    flowables.extend(reportlab_letter_head)

    exam = student_row['exam']
    first_name = student_row['FirstName']
    last_name = student_row["LastName"]
    StudentID = student_row["StudentID"]

    password = f"{first_name[0].upper()}{last_name[0].lower()}{StudentID}!"

    paragraphs = [
        f"Dear {first_name.title()} {last_name.title()} ({StudentID})",
        f"The next step in your post-HSFI journey is to take the {exam} this spring. In order to take the exam, you need to have a College Board Account.",
        "First, see if you have already created a College Board account, go to https://www.collegeboard.org and login. If you have an account but don't remember the password, you will need to go through the password reset process",
        "If you don't have a College Board account, you'll sign up using information that appears in your NYCPS official records. Scan the QR code below to get to the signup page.",
    ]

    flowables.extend(
        [
            Paragraph(
                x,
                styles["BodyText"],
            ) for x in paragraphs
        ]
    )

    flowables.append(signup_url_qr_code)

    email_address = student_row["Student DOE Email"]
    date_of_birth = student_row["DOB"].strftime("%m/%d/%Y")
    anticipated_graduation = student_row["anticipated_graduation"]
    apt_num = student_row['AptNum']
    street = student_row["Street"]
    city = student_row["City"]
    state = student_row["State"]
    zipcode = student_row['Zip']

    street_address = f"{street} {apt_num} {city}, {state} {zipcode}"
    steps_lst = [
        f"<b>First Name</b> - {first_name}",
        f"<b>Last Name</b> - {last_name}",
        f"<b>Email Address</b> - {email_address}",
        f"<b>Date of Birth</b> - {date_of_birth}",
        f"<b>HS Graduation</b> - {anticipated_graduation}",
        f"<b>Zip/Postal Code</b> - {zipcode}",
        f"<b>Where do you go to school?</b> - High School of Fashion Industries",
        f"<b>Home Address</b> - {street_address}",
    ]

    steps_lst = [
        Paragraph(
            x,
            styles["Normal"],
        )
        for x in steps_lst
    ]

    steps_lst = ListFlowable(
        steps_lst,
        bulletType="bullet",
        start="-",
    )
    flowables.append(steps_lst)

    flowables.append( 
        Paragraph(
            f"Parent information is optional, but consider filling it out if you know it. For your password, use the following: {password} so we can assist you if you forget. Write down the security phrase and save it in your phone. Add a phone number. And verify your account",
            styles["BodyText"]
            )
    )

    flowables.append( 
        Paragraph(
            f"You will not sign in with your College Board account on the day of the {exam}, a separate access code will be given to you in the testing room. You can log into Bluebook with your College Board account before the exam for practice materials",
            styles["BodyText"]
            )
    )

    flowables.extend(reportlab_closing)
    flowables.append(PageBreak())
    return flowables

def process_3_07_df(cr_3_07_df):
    school_year = session['school_year']
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(utils.return_year_in_hs, args=(school_year,))
    cr_3_07_df["exam"] = cr_3_07_df["year_in_hs"].apply(return_exam)

    cr_3_07_df = cr_3_07_df[cr_3_07_df['exam'].isin(['SAT','PSAT'])]
    cr_3_07_df["anticipated_graduation"] = cr_3_07_df["GEC"].apply(utils.return_hs_graduation_month)
    return cr_3_07_df

def return_exam(year_in_hs):
    if year_in_hs == 3:
        return 'SAT'
    if year_in_hs == 2:
        return 'PSAT'
