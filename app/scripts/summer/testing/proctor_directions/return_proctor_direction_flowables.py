import pandas as pd
import numpy as np
import os
import datetime as dt
from io import BytesIO
from flask import current_app, session

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch, cm
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle, ListFlowable
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.flowables import BalancedColumns

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df
from app.scripts.summer import utils as summer_utils

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


def main(section_row, exam_book_df):
    flowables = []

    exam_title = section_row['Exam Title']
    hub_location = section_row['hub_location']
    exam_room = section_row['Room']
    exam_day = section_row['Day']
    exam_time = section_row['Time']
    course_code = section_row['Course']

    paragraph = Paragraph(
            f"{exam_day} {exam_time} | {exam_title} | Room {exam_room}",
            styles["Heading1"],
    )
    flowables.append(paragraph)

    hub_phone_number = return_hub_phone_number(hub_location)
    

    directions_paragraph = Paragraph(f"Directions: Complete this checklist as you administer the Regents exam. Initial next to each step. Exam specific information is on the back of the checklist. If you have any questions, contact your room's testing hub, {hub_location}, {hub_phone_number} and then the testing office x2021", styles["Normal"])
    

    paragraph = Paragraph(f"<b>Prioritize starting the exam on time; collect cell phones and get students seated. You can hand out bubble sheets and complete check-in process while students have begun testing. You must start the exam on time</b>", styles["Normal"])
    

    sections_tbl = return_sections_tbl(course_code, exam_room, exam_book_df)

    chart_style = TableStyle(
        [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    )
    flowables.append(
        Table(
            [[ [directions_paragraph,paragraph], sections_tbl]],
            colWidths=[5 * inch, 2.5 * inch],
            # rowHeights=[3 * inch],
            style=chart_style,
        )
    )


    paragraph = Paragraph(f"Pre-Exam --- Hub Location {hub_location}", styles["Heading2"])
    flowables.append(paragraph)

    pre_exam_todos = ListFlowable(
        [
            Paragraph(
                f"Pickup materials from hub location (Room {hub_location}) at the scheduled time.",
                styles["Normal"],
            ),
            Paragraph(
                "Report to testing room, review materials, and reread directions before letting students into the room.",
                styles["Normal"],
            ),
            Paragraph(
                f"Call your room's testing hub, {hub_location}, {hub_phone_number} and then the testing office, x2021, if you are missing any materials or have questions.",
                styles["Normal"],
            ),
            Paragraph("Admit students to the testing room. Students were informed to arrive 45 minutes early", styles["Normal"]),
            Paragraph("Collect student cell phones (students turn off their phones and place facedown on teacher desk)", styles["Normal"]),
            Paragraph("Pass out non-secure materials (scrap paper, reference tables, glossaries)", styles["Normal"]),
        ],
        bulletType="bullet",
        start="squarelrs",
)

    flowables.append(pre_exam_todos)

    paragraph = Paragraph(f"Starting Exam", styles["Heading2"])
    flowables.append(paragraph)
    starting_exams_todos = ListFlowable(
    [
        Paragraph("Read the Cellphone Policy verbatim to students (on back of proctor directions)", styles["Normal"]),
        Paragraph("Hand out secure testing materials (exam booklet, answer booklet)", styles["Normal"]),
        Paragraph("Read the exam directions verbatim on the front of the exam booklet and start the exam", styles["Normal"]),
        Paragraph(
            "Record the actual exact start time (8:30AM / 12:30PM) on the board and record here <b>Start Time:__________</b>",
            styles["Normal"],
        ),
        Paragraph(
            "Standard testing rooms are 3 hours in length. Some extended time rooms may have a mix of 1.5x (4.5 hours) and 2x (6 hours). ENL students receive at least 1.5x (4.5 hours). This info by student is on your testing room photo roster", styles["Normal"]
        ),        
        Paragraph(
            "Record the end time on the board and record here <b>End Time:__________</b>", styles["Normal"]
        ),
        
    ],
    bulletType="bullet",
    start="squarelrs",
)    
    
    flowables.append(starting_exams_todos)


    paragraph = Paragraph(f"During Exam", styles["Heading2"])
    flowables.append(paragraph)

    during_exam_todos = ListFlowable(
        [
            Paragraph("Complete check in process with each student. (1) Verify student identify with PhotoID, Exam Invitation or Photo Roster, (2) give student Part 1 bubble sheet, (3) affix label to student exams (see back for picture) and (4) have student sign themselves in on the Section Attendance Roster (SAR)", styles["Normal"]),
            Paragraph(
                "Universal Admission Deadline: (AM - 9:15AM / PM - 1:15PM). Do not allow any student into the testing room after the admissions deadline", styles["Normal"]
            ),
            Paragraph(
                "Students cannot be dismissed until: (AM - 9:30AM / PM - 1:30PM)",
                styles["Normal"],
            ),
            Paragraph(
                "Checkout each student one at a time and review their testing materials. (1) Check for double/missing bubbles, (2) confirm student signature on Part 1 bubble sheet, (3) student signs themselves out on the Section Attendance Roster (SAR)",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="squarelrs",
    )    

    
    flowables.append(during_exam_todos)

    paragraph = Paragraph(f"Post-Exam", styles["Heading2"])
    flowables.append(paragraph)
    post_exam_todos = ListFlowable(
        [
            Paragraph(
                "Before leaving proctoring location, organize all testing materials alphabetically <b>BY SECTION NUMBER</b> according to test specifics",
                styles["Normal"],
            ),
            Paragraph(
                "Before leaving proctoring location, return pens, pencils, scrap paper, and other support materials in your testing bag. <b>Calculators remain in the room.</b>",
                styles["Normal"],
            ),
            Paragraph(
                f"Return testing materials and bag to Room {hub_location}. If no one is at the hub, return materials to room 202 (testing office).",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="squarelrs",
    )
    flowables.append(post_exam_todos)

    paragraph = Paragraph(f"Proctor Signatures", styles["Heading2"])
    flowables.append(paragraph)
    paragraph = Paragraph(f"Sign and date to attest you followed NYSED and HSFI specific procedures while completing this proctoring assignment.", styles["Normal"])
    flowables.append(paragraph)

    signature_grid_data = [
        ["Name (printed)", "Signature", "Date"],
        [],
        [],

    ]
    colWidths = [200, 200, 75]
    rowHeights = [15, 20, 20]
    signature_grid_table = Table(
        signature_grid_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights
    )
    signature_grid_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (100, 100), 1),
                ("RIGHTPADDING", (0, 0), (100, 100), 1),
                ("BOTTOMPADDING", (0, 0), (100, 100), 1),
                ("TOPPADDING", (0, 0), (100, 100), 1),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                # ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xD0D0FF, None)),
            ]
        )
    )    
    flowables.append(signature_grid_table)

    flowables.append(PageBreak())


### Page 2

#### Cell Phone Policy
    paragraph = Paragraph("Cell Phone Statement -- Read verbatim", styles["Heading2"])
    flowables.append(paragraph)


    paragraph = Paragraph("You cannot have any communications device, including a cell phone, with you during this examination or during any breaks (such as a restroom visit). Such devices include, but are not limited to:", styles["Normal"])
    flowables.append(paragraph)

    banned_devices_lst = ListFlowable(
    [
        Paragraph("Cell phones", styles["Normal"]),
        Paragraph("iPods or other MP3 players", styles["Normal"]),
        Paragraph("iPads, tablets, and other eReaders", styles["Normal"]),
        Paragraph(
            "Personal laptops, notebooks, or any other computing devices",
            styles["Normal"],
        ),
        Paragraph(
            "Wearable devices/smart wearables, including smart watches and health wearables with a display",
            styles["Normal"],
        ),
        Paragraph(
            "Headphones headsets, or in-ear headphones such as earbuds, and",
            styles["Normal"],
        ),
        Paragraph(
            "Any other device capable of recording audio, photographic, or video content, or capable of viewing or playing back such content, or sending/receiving text, audio, or video messages",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="-",
    )
    flowables.append(banned_devices_lst)

    paragraph = Paragraph("If you brought any of these items to the building today, and have not already stored it in your locker or turned it over to me, a test monitor, or school official, you must give it to me now. You may not keep your cell phone or any of these items with you, or near you, including in your pockets, backpack, desk, etc. If you keep a cell phone or any of these items with you, your examination will be invalidated and you will get no score. Is there anyone who needs to give me any of these items now?", styles['Normal'])
    flowables.append(paragraph)
    
    exam_specific_flowables = exam_specific_info_dict.get(exam_title,[])
    flowables.extend(exam_specific_flowables)
    flowables.append(PageBreak())

    return flowables


def return_hub_phone_number(hub_location):
    if hub_location > 899:
        return f"x1{hub_location}"
    if hub_location == 329:
        return f"x3295"
    return f"x{hub_location}1"

def return_sections_tbl(course_code, room, exam_book_df):
    section_df = exam_book_df[(exam_book_df['Course']==course_code) & (exam_book_df['Room']==room)]
    cols = ['Section','Type']
    
    table_data = section_df[cols].values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=None, repeatRows=1, rowHeights=None)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t    


liv_env_specific_info = [
    Paragraph(f"Living Environment Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Calculator", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/LE_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Part 2 Test Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

earth_science_specific_info = [
    Paragraph(f"Earth Science Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Earth Science Reference Tables", styles["Normal"]),
            Paragraph("Calculator", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the answer booklet and the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/ES_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Part 2 Answer Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
            Paragraph("Pile C: Used Question Booklets (does not need to be alphabetized)", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

chemistry_specific_info = [
    Paragraph(f"Chemistry Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Chemistry Reference Tables", styles["Normal"]),
            Paragraph("Calculator", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the answer booklet and the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Chemistry_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Part 2 Answer Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
            Paragraph("Pile C: Used Question Booklets (does not need to be alphabetized)", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

physics_specific_info = [
    Paragraph(f"Physics Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Physics Reference Tables", styles["Normal"]),
            Paragraph("Centimeter Ruler", styles["Normal"]),
            Paragraph("Protractor", styles["Normal"]),
            Paragraph("Calculator", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the answer booklet and the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Physics_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Part 2 Answer Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
            Paragraph("Pile C: Used Question Booklets (does not need to be alphabetized)", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]
Global_specific_info = [
    Paragraph(f"Global History Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Scrap Paper", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the answer booklet and to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Global_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Test Booklets with Essay Booklet Inside", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

USH_specific_info = [
    Paragraph(f"US History Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Scrap Paper", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the answer booklet and to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/USH_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Test Booklets with Essay Booklet Inside", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

ELA_specific_info = [
    Paragraph(f"ELA Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Scrap Paper", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the Essay booklet only", styles["Normal"]
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/ELA_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Essay Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
            Paragraph("Pile C: Used question booklets", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

alg1_specific_info = [
    Paragraph(f"Algebra 1 Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Calculator", styles["Normal"]),
            Paragraph(
                "Straight Edge (Students to use their Student ID Card)",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Algebra_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Test Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

geo_specific_info = [
    Paragraph(f"Geometry Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Calculator", styles["Normal"]),
            Paragraph("Compass", styles["Normal"]),
            Paragraph(
                "Straight Edge (Students to use their Student ID Card)",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Geometry_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Test Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]

trig_specific_info = [
    Paragraph(f"AlgebraII/Trig Specific Info", styles["Heading1"]),
    Paragraph(f"Materials", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Calculator", styles["Normal"]),
            Paragraph(
                "Straight Edge (Students to use their Student ID Card)",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="-",
    ),
    Paragraph(f"Labels", styles["Heading2"]),
    Paragraph(
        f"Affix a label to the upper left corner of the test booklet",
        styles["Normal"],
    ),
    Image(
        "app/scripts/summer/testing/proctor_directions/sticker_schematics/Trigonometry_Sticker.png",
        width=3 * inch,
        height=3 * inch,
        kind="proportional",
    ),
    Paragraph(f"End of Exam Organization", styles["Heading2"]),
    ListFlowable(
        [
            Paragraph("Section Folder: Alphabetized Part 1 Bubble Sheets", styles["Normal"]),
            Paragraph("Section Folder: Alphabetized Absent Student Part 1 Bubble Sheets -- Bubbled Absent by Proctor.", styles["Normal"]),
            Paragraph("Pile A: Alphabetized Test Booklets", styles["Normal"]),
            Paragraph("Pile B: Unused testing materials", styles["Normal"]),
        ],
        bulletType="bullet",
        start="-",
    ),
]


exam_specific_info_dict = {
    "Living Environment": liv_env_specific_info,
    "Earth Science": earth_science_specific_info,
    "Chemistry": chemistry_specific_info,
    "Physics": physics_specific_info,
    "Global History": Global_specific_info,
    "US History": USH_specific_info,
    "ELA": ELA_specific_info,
    "Algebra I": alg1_specific_info,
    "Geometry": geo_specific_info,
    "Algebra II/Trigonometry": trig_specific_info,
    "Biology": liv_env_specific_info,
    "Earth and Space Science": earth_science_specific_info,    
}