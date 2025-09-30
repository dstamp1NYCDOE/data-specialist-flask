from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO


from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import PageTemplate
from reportlab.platypus.frames import Frame

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab_qrcode import QRCodeImage

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_small",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=7,
        leading=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=9,
        leading=9,
    )
)



import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils



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


    exam_book_df = regents_organization_utils.return_exam_book()
    registrations_df = regents_organization_utils.return_processed_registrations()
    
    filename = f"{month}_{school_year+1}_hub_pages.pdf"


    flowables = []
    for hub_location, exam_book_by_hub_df in exam_book_df.groupby("hub_location"):
        paragraph = Paragraph(
            f"{month} {school_year+1}\nRegents\nHub {int(hub_location)} Materials",
            styles["Title"],
        )
        flowables.append(paragraph)
        hub_exam_summary_df = exam_book_by_hub_df.drop_duplicates(subset=['Exam Title'])
        hub_exam_summary_df = hub_exam_summary_df.sort_values(by=['Day','Time','Exam Title'])
        cols = ['Date','Time','Exam Title']
        T = return_df_as_table(hub_exam_summary_df, cols)
        flowables.append(T)
        flowables.append(hub_directions_paragraph)
        flowables.append(PageBreak())
        flowables.extend(return_QR_code_poster())

        for day, exam_book_by_day_time_df in exam_book_by_hub_df.groupby("Date"):
            hub_rooms_pvt = (
            pd.pivot_table(
                exam_book_by_day_time_df,
                index=["Day", "Time", "Room", "ExamTitle"],
                values=["NumOfStudents", "Type", "Section"],
                aggfunc={
                    "Section": combine_lst_of_section_properties,
                    "Type": combine_lst_of_section_properties,
                    "NumOfStudents": "sum",
                },
            )
            .reset_index()
            )
            hub_rooms_pvt["Assigned Proctor (write in name)"] = ""
            hub_rooms_pvt = hub_rooms_pvt[
                [
                    "Time",
                    "ExamTitle",
                    "Room",
                    "Section",
                    "Type",
                    "NumOfStudents",
                    "Assigned Proctor (write in name)",
                ]
            ].sort_values(by=["Time", "ExamTitle", "Room"])
            for time in ["AM", "PM"]:
                paragraph = Paragraph(
                f"Testing Hub {int(hub_location)} - Sections - {day}",
                styles["Heading1"],)
                flowables.append(paragraph) 

                paragraph = Paragraph(
                    f"{time}",
                    styles["Heading3"],
                )
                flowables.append(paragraph)
                if hub_location != 329:
                    T = return_testing_rooms_by_hub(
                        hub_rooms_pvt[hub_rooms_pvt["Time"] == time]
                    )
                    flowables.append(T)
                else:
                    paragraph = Paragraph(
                        f"The following students are assigned with the scribe accommodation.",
                        styles["Normal"],
                    )
                    flowables.append(paragraph)                    
                    scribe_students_df = registrations_df[registrations_df['Room']==329]
                    scribe_students_df = scribe_students_df[scribe_students_df['Date']==day]
                    scribe_students_df = scribe_students_df[scribe_students_df['Time']==time]
                    scribe_students_df = scribe_students_df.sort_values(by=['ExamTitle','LastName','FirstName'])
                    scribe_students_df["Assigned Proctor (write in name)"] = ""
                    scribe_students_df["Room (write in room)"] = ""
                    cols = ['LastName','FirstName',"ExamTitle","Room (write in room)","Assigned Proctor (write in name)"]
                    T = return_df_as_table(scribe_students_df, cols=cols)
                    flowables.append(T)
                    
                flowables.append(PageBreak())
    ### Testing Office Materials
    for (day,time), df in exam_book_df.groupby(["Day","Time"]):
        ## return testing numbers by room, by hub
        for hub_location in df["hub_location"].unique():
            hub_rooms_pvt = pd.pivot_table(
                df[df["hub_location"] == hub_location],
                index=["Day", "Time", "hub_location", "Room", "ExamTitle"],
                values=["NumOfStudents", "Type", "Section"],
                aggfunc={
                    "Section": combine_lst_of_section_properties,
                    "Type": combine_lst_of_section_properties,
                    "NumOfStudents": "sum",
                },
            )
            hub_rooms_pvt = hub_rooms_pvt.reset_index()

            paragraph = Paragraph(
                f"{month} {school_year+1}\nRegents\nHub {int(hub_location)} Materials",
                styles["Title"],
            )
            flowables.append(paragraph)

            for exam in hub_rooms_pvt["ExamTitle"].unique():
                exam_df = hub_rooms_pvt[hub_rooms_pvt["ExamTitle"] == exam]
                T = return_testing_rooms_by_hub(exam_df)
                flowables.append(T)

                total_students = exam_df["NumOfStudents"].sum()
                paragraph = Paragraph(
                    f"Total Students {exam}: {total_students}",
                    styles["Title"],
                )
                flowables.append(paragraph)

            
            flowables.append(PageBreak())


    for (course,day,time,exam_title), df in exam_book_df.groupby(["Course","Day","Time","Exam Title"]):
        ## exam book by room
        paragraph = Paragraph(
        f"{exam_title} - Exam Book by Room - {day} {time}",
        styles["Heading1"],)
        flowables.append(paragraph)
        cols = ['ExamTitle','Section','Room','hub_location','Type','NumOfStudents']
        dff = df.sort_values(by=['Room'])
        T = return_df_as_table(dff, cols=cols)
        flowables.append(T)
        flowables.append(PageBreak())

        ## test 2 accommodations bubbles
        paragraph = Paragraph(
        f"{exam_title} - Part 2 Testing Accommodations Bubbles",
        styles["Heading1"],)
        flowables.append(paragraph)
        flowables.append(part_2_documents_paragraph)
        cols = ['ExamTitle','Section','Room','Type','accommodations_bubbles']
        dff = df[df['accommodations_bubbles']!=""]
        T = return_df_as_table(dff, cols=cols)
        flowables.append(T)
        flowables.append(PageBreak())

    ## return 10 copies of the QR code
    for _ in range(10):
        flowables.extend(return_QR_code_poster())

    # return '',''

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f, filename

hub_directions_paragraph = Paragraph(
    """<b>Hub Directions:</b><br/>
    1. Facilitate distribution of testing materials and assignments of proctors. Part 1 answer documents are organized in folders inside of a room folder with proctor directions, rosters, etc. <br/>
    2. Check in with testing rooms associated with your hub<br/>
    3. Facilitate bathroom breaks during testing assignments<br/>
    4. Walk in students will be sent to your hub to be assigned to rooms based on space availability<br/>
    5. Proctors will return testing materials to the testing office and return to the testing hub after their materials have been reviewed. Assign them to take their 30 minute lunch break, provide breaks for other proctors, and other support as needed. <br/>
    """,
    styles["Normal"],
)

part_2_documents_paragraph = Paragraph(
    """<b>Part 2 Documents:</b><br/>
    1. Bubble the Part 2 accommodations by section order<br/>
    2. After accommodations have been bubbled, reorganize by the room<br/>
    3. When that room returns to the testing office, place the Part 2 document inside the student work<br/>
    4. For absent students, pull their Part 2 document and set aside<br/>"""
)

def combine_lst_of_section_properties(x):
    x = x.unique()
    output = "\n".join(str(v) for v in x)
    return output


def return_testing_rooms_by_hub(hub_rooms_pvt):

    table_data = hub_rooms_pvt.values.tolist()
    cols = hub_rooms_pvt.columns
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=None, repeatRows=1, rowHeights=None)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t


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
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t


def return_QR_code_poster():
    flowables = []
    qr_code_url = 'https://script.google.com/a/macros/schools.nyc.gov/s/AKfycbwdcoDHcLFioogVyRQQOWgfPgRqi7YBpm9Z9aAWSmfkAO_cBrCU3NVvQNukeG9wixDq/exec'
    qr = QRCodeImage(qr_code_url, size=5 * inch)
    qr.hAlign = 'CENTER'


    paragraph = Paragraph(
        f"August Regents Digital Exam Ticket Lookup",
        styles["Title"],
    )
    flowables.append(paragraph)
    flowables.append(qr)

    paragraph = Paragraph(
        f"Scan the QR code and enter your 9 Digit StudentID number to look up your room assignment",
        styles["Heading1"],
    )
    flowables.append(paragraph)
    flowables.append(PageBreak())    

    return flowables