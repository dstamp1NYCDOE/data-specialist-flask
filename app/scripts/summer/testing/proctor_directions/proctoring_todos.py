from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

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
from reportlab.lib.pagesizes import letter, landscape

styles = getSampleStyleSheet()

pre_exam_todos = ListFlowable(
    [
        Paragraph(
            "Pickup materials from testing office (Room 202) at the scheduled time.",
            styles["Normal"],
        ),
        Paragraph(
            "Report to testing room, review materials, and reread directions before letting students into the room",
            styles["Normal"],
        ),
        Paragraph(
            "Call the testing (x2021 / x2022) office if you are missing any materials.",
            styles["Normal"],
        ),
        Paragraph("Admit students to the testing room", styles["Normal"]),
        Paragraph("Collect student cell phones", styles["Normal"]),
        Paragraph("Pass out non-secure materials", styles["Normal"]),
        Paragraph(
            "Pass out pre-slugged answer document with the student name and StudentID number",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)

pre_exam_FAQs = ListFlowable(
    [
        Paragraph(
            "What do I do if a student doesn't appear on the roster? First, check their invitation and see if they are in the wrong place. Second, send to the main lobby to register as a walk-in. Walk-in students will have a slip of paper confirming their room location and their answer document will be delivered to the testing room.",
            styles["Normal"],
        ),
        Paragraph(
            "What do I do for a Walk-In Student? Walk-in students will sign at the bottom of the sign in sheet. They should begin testing as soon as possible. Answer documents will be delivered after the universal admissions deadline.",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="-",
)

pre_exam_dos_and_donts = ListFlowable(
    [
        Paragraph(
            "Do not lay out secure testing materials on student desks before they enter.",
            styles["Normal"],
        ),
        Paragraph(
            "Do not affix student labels to any testing materials before the exam begins; unused testing materials with student information must be destroyed and cannot be recycled into the classroom",
            styles["Normal"],
        ),
        Paragraph(
            "Do not let multiple students use the restroom at the same time",
            styles["Normal"],
        ),
        Paragraph(
            "Do not allow a student to use pen on the multiple-choice bubble sheet",
            styles["Normal"],
        ),
        Paragraph(
            "Do not use your cell phone while proctoring the exam. Test Monitors from NYSED and NYCDOE conduct walkthroughs to verify test security",
            styles["Normal"],
        ),
        Paragraph(
            "Do not allow any student to test beyond their allotted time (3 hours/4.5 hours/6 hours) as indicated by your room assignment",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="-",
)

starting_exams_todos = ListFlowable(
    [
        Paragraph("Read the Cellphone Policy to students (below)", styles["Normal"]),
        Paragraph("Hand out secure testing materials", styles["Normal"]),
        Paragraph("Read the exam directions", styles["Normal"]),
        Paragraph(
            "Begin the exam and record the start time (9AM / 1PM) on the board. Start Time:__________",
            styles["Normal"],
        ),
        Paragraph(
            "Record the end time on the board. End Time:__________", styles["Normal"]
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)

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


checkin_process_lst = ListFlowable(
    [
        Paragraph("Circulate to students one at a time", styles["Normal"]),
        Paragraph(
            "Verify identity with exam invitation or photo ID (such as Student ID Card)",
            styles["Normal"],
        ),
        Paragraph(
            "Student signs their name on the section attendance roster (SAR)",
            styles["Normal"],
        ),
        Paragraph(
            "Mark student P for present on the section attendance roster (SAR)",
            styles["Normal"],
        ),
        Paragraph(
            "Affix label(s) to student test booklets and/or answer booklets if student work is graded in that document. Labels go in the upper left corner.",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)


checkout_process_lst = ListFlowable(
    [
        Paragraph(
            "Check out students one at a time, even after the exam has ended.",
            styles["Normal"],
        ),
        Paragraph(
            "Verify the student has completed the exam. If not, ask the student to go back and at least attempt the question (time permitting)",
            styles["Normal"],
        ),
        Paragraph(
            "Verify the student has not double bubbled or omitted a bubble. If so, ask the student to go back and make corrections (time permitting)",
            styles["Normal"],
        ),
        Paragraph(
            "Verify the student has signed the declaration in pen", styles["Normal"]
        ),
        Paragraph(
            "Student signs their name on the section attendance roster (SAR)",
            styles["Normal"],
        ),
        Paragraph(
            "Begin alphabetizing student documents (bubble sheets in Pile A and other question/answer/essay booklets in test specific additional piles)",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)

during_exam_todos = ListFlowable(
    [
        Paragraph("Complete check in process with each student", styles["Normal"]),
        Paragraph(
            "Universal Admission Deadline: (AM - 10AM / PM - 2PM)", styles["Normal"]
        ),
        Paragraph(
            "Students cannot be dismissed until: (AM - 10:15AM / PM - 2:15PM)",
            styles["Normal"],
        ),
        Paragraph(
            "Checkout each student one at a time and review their testing materials",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)

post_exam_todos = ListFlowable(
    [
        Paragraph(
            "Before leaving proctoring location, organize all testing materials alphabetically <b>BY SECTION NUMBER</b> according to test specifics",
            styles["Normal"],
        ),
        Paragraph(
            "Before leaving proctoring location, return pens, pencils, scrap paper, and other support materials to the supplies box in the room",
            styles["Normal"],
        ),
        Paragraph(
            "Return testing bag and testing materials to the designated drop off location: ________",
            styles["Normal"],
        ),
    ],
    bulletType="bullet",
    start="squarelrs",
)


signature_grid_data = [
    ["Name (printed)", "Signature", "Date"],
    [],
    [],
    [],
    [],
    [],
]
colWidths = [200, 200, 75]
rowHeights = [15, 20, 20, 20, 20, 20]
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
