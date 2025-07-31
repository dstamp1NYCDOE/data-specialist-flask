from io import BytesIO

import app.scripts.utils.utils as utils
from app.scripts import files_df

from flask import session

from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Table, TableStyle
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import SimpleDocTemplate

from reportlab_qrcode import QRCodeImage

import pandas as pd


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

letter_head = [
    Paragraph("High School of Fashion Industries", styles["Normal"]),
    Paragraph("225 W 24th St", styles["Normal"]),
    Paragraph("New York, NY 10011", styles["Normal"]),
    Paragraph("Principal, Daryl Blank", styles["Normal"]),
]

closing = [
    Spacer(width=0, height=0.25 * inch),
    Paragraph("Warmly,", styles["Normal_RIGHT"]),
    Paragraph("Derek Stampone", styles["Normal_RIGHT"]),
    Paragraph("Assistant Principal, Programming", styles["Normal_RIGHT"]),
]


def main(form, request):
    school_year = session["school_year"]
    school_year = int(school_year) + 1

    filename = utils.return_most_recent_report(files_df, "3_07")
    students_df = utils.return_file_as_df(filename)
    students_df["year_in_hs"] = students_df["GEC"].apply(return_year_in_hs)

    students_on_register = students_df["StudentID"].to_list()

    filename = utils.return_most_recent_report(files_df, "4_01")
    student_requests_df = utils.return_file_as_df(filename)

    student_session_dict = {}
    for StudentID, student_requests in student_requests_df.groupby('StudentID'):
        student_courses = student_requests['Course'].to_list()
        if 'ZM18' in student_courses:
            student_session_dict[StudentID] = '1-8 Schedule'
        elif 'ZM29' in student_courses:
            student_session_dict[StudentID] = '2-9 Schedule'
        else:
            student_session_dict[StudentID] = '1-9 Schedule'

    filename = utils.return_most_recent_report(files_df, "code_deck")
    code_deck_df = utils.return_file_as_df(filename)

    date_of_letter = form.date_of_letter.data.strftime("%e %b %Y")
    due_date = form.due_date.data.strftime("%B %e, %Y")

    ap_vetting_file = request.files[form.ap_vetting_file.name]
    ap_vetting_df = pd.read_csv(ap_vetting_file)
    ap_vetting_df = ap_vetting_df[["StudentID", "Course", "decision"]]

    ap_vetting_df = ap_vetting_df[ap_vetting_df["StudentID"].isin(students_on_register)]

    students_to_receive_letters = ap_vetting_df["StudentID"].unique()

    student_requests_df = student_requests_df[
        student_requests_df["Course"].str[0:2] != "ZL"
    ]

    student_requests_df = student_requests_df.merge(
        code_deck_df[["CourseCode", "CourseName", "Credits"]],
        left_on=["Course"],
        right_on=["CourseCode"],
        how="left",
    )

    student_requests_df = student_requests_df[
        student_requests_df["StudentID"].isin(students_to_receive_letters)
    ]

    student_requests_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "CourseName",
    ]
    student_requests_df = student_requests_df[student_requests_cols]

    ap_course_lst = [
        "AHS21X",
        "SBS21X",
        "MCS21X",
        "MKS21X",
        "HGS43X",
        "HFS21X",
        "MPS21X",
        "APS21X",
        "HUS21X",
        "EES87X",
    ]

    student_requests_df["AP_course?"] = student_requests_df["Course"].apply(
        lambda x: x in ap_course_lst
    )

    flowables = []
    for StudentID, student_vetting_df in ap_vetting_df.groupby("StudentID"):
        year_in_hs = students_df[students_df["StudentID"] == StudentID][
            "year_in_hs"
        ].to_list()[0]
        LastName = students_df[students_df["StudentID"] == StudentID][
            "LastName"
        ].to_list()[0]
        FirstName = students_df[students_df["StudentID"] == StudentID][
            "FirstName"
        ].to_list()[0]
        student_name = f"{FirstName.title()} {LastName.title()}"

        APs_accepted = (
            student_vetting_df[student_vetting_df["decision"] == "Yes"]["Course"]
            .sort_values()
            .to_list()
        )

        student_requests_dff = student_requests_df[
            student_requests_df["StudentID"] == StudentID
        ]

        ap_courses_df = student_requests_dff[student_requests_dff["AP_course?"]]
        APs_enrolled = ap_courses_df["Course"].sort_values().to_list()
        num_of_ap_courses = len(ap_courses_df)

        ## determine if a course was a yes but not in the final list
        if APs_enrolled:
            yes_but_not_enrolled = [course for course in APs_accepted if course not in APs_enrolled]
        else:
            yes_but_not_enrolled = []

        # Start Flowables
        flowables.append(Spacer(width=0, height=0.5 * inch))
        paragraph = Paragraph(f"{date_of_letter}", styles["Normal"])
        flowables.append(paragraph)
        flowables.append(Spacer(width=0, height=0.2 * inch))
        flowables.extend(letter_head)
        flowables.append(Spacer(width=0, height=0.2 * inch))

        paragraph = Paragraph(f"Dear {student_name} ({StudentID}),", styles["BodyText"])
        flowables.append(paragraph)

        paragraph = Paragraph(
            f"Thank you for applying to challenge yourself with Advanced Placement courses for the Fall {school_year} semester. Below are your admissions results by AP course:",
            styles["Body_Justify"],
        )

        flowables.append(paragraph)

        flowables.append(Spacer(width=0, height=0.25 * inch))
        cols = ["Course", "decision"]
        flowables.append(return_courses_as_table(student_vetting_df, cols=cols))

        if num_of_ap_courses == 0:
            paragraph = Paragraph(
                f"I regret to inform you have not been enrolled in any AP courses for the Fall semester. Over 400 students applied for the AP courses and there was only 1 class section of seats available per AP course.",
                styles["Body_Justify"],
            )
            flowables.append(paragraph)
            if year_in_hs < 4:
                paragraph = Paragraph(
                    f"Although you were not selected, we applaud your effort to challenge yourself and encourage you to continue reaching for advanced goals! Please remember that opportunities to apply for AP courses are available every year. We encourage you to become a more competitive candidate for next year by improving your attendance (being present and on time to all classes), applying yourself further in your courses, and scoring highly on your Regents exams this June.",
                    styles["Body_Justify"],
                )
                flowables.append(paragraph)
            else:
                paragraph = Paragraph(
                    f"Although you were not selected, we applaud your effort to challenge yourself and encourage you to continue reaching for advanced goals! Please remember there are a number of ways you can still strengthen your resume for college applications aside from AP classes. As a senior, we encourage you to take advantage of the multitude of extracurricular opportunities available at HSFI such as joining a club, trying out for a sports team or volunteering in a leadership role.",
                    styles["Body_Justify"],
                )
                flowables.append(paragraph)                
        else:
            student_session = student_session_dict.get(StudentID,'1-8 schedule')
            paragraph = Paragraph(
                f"Congratulations on being accepted to an AP course! To fit these AP course(s) in your program, you are on a {student_session}. Taking an AP course is a big time committment inside and outside of school. You are expected to be an active participant and diligently prepare for the AP exam in May. You have been enrolled in the following AP courses:",
                styles["Body_Justify"],
            )
            flowables.append(paragraph)

            flowables.append(Spacer(width=0, height=0.25 * inch))
            cols = ["CourseName"]
            flowables.append(return_courses_as_table(ap_courses_df, cols=cols))
            flowables.append(Spacer(width=0, height=0.25 * inch))

            if len(yes_but_not_enrolled) > 0:
                paragraph = Paragraph(
                    f"Due to schedule constraints, you may not have been enrolled in all of the AP courses you were accepted into. If you would like to make any changes to the AP classes you are enrolled in please bring this letter to see your guidance counselor by <b>{due_date}</b>. Your counselor will submit an updated request to the programming office.",
                    styles["Body_Justify"],
                )
                flowables.append(paragraph)

            if num_of_ap_courses > 2:
                paragraph = Paragraph(
                    f"HSFI typically recommends students take no more than 2 AP Courses in a school year. Taking on 3 or more APs is a big time committment but one that can be worth it especially for your college application resume. If you do not want to take all {num_of_ap_courses} AP courses currently on your schedule, bring this letter to bring this letter to your counselor to discuss your options by <b>{due_date}</b>. Your counselor will submit an updated request to the programming office.",
                    styles["Body_Justify"],
                )
                flowables.append(paragraph)                

            paragraph = Paragraph(
                f"If you have any questions about your AP courses, your other courses, and if you want to remove an accepted AP or swap for a different accepted AP, bring this letter to your counselor to discuss your options by <b>{due_date}</b>. Your counselor will submit an updated request to the programming office.",
                styles["Body_Justify"],
            )
            flowables.append(paragraph)

        flowables.extend(closing)
        flowables.append(PageBreak())

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
        bottomMargin=0.25 * inch,
    )

    my_doc.build(flowables)
    f.seek(0)
    return f


def return_courses_as_table(registered_courses_df, cols):
    table_data = registered_courses_df[cols].values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                # ('FONTSIZE', (0, 0), (100, 100), 11),
                ("LEFTPADDING", (0, 0), (100, 100), 1),
                ("RIGHTPADDING", (0, 0), (100, 100), 1),
                ("BOTTOMPADDING", (0, 0), (100, 100), 1),
                ("TOPPADDING", (0, 0), (100, 100), 1),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
            ]
        )
    )
    return t


def return_year_in_hs(gec):
    school_year = session["school_year"]
    return utils.return_year_in_hs(gec, school_year) + 1
