from reportlab.graphics import shapes
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
from reportlab_qrcode import QRCodeImage

import datetime as dt
from io import BytesIO

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
    Paragraph("Assistant Principal, Attendance", styles["Normal_RIGHT"]),
]


import pandas as pd

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from flask import session

def main(data):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    term = data["form"]["marking_period"]
    semester, marking_period = term.split("-")

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    grades_df = utils.return_file_as_df(filename)

    ## keep grades from current semester
    grades_df = grades_df[grades_df["Term"] == semester]
    ## drop courses with no grades
    grades_df = grades_df.dropna(subset=["Pct"])
    ## determine failing classes
    grades_df["failing?"] = grades_df["Pct"] < 65

    ## drop non-credit-bearing-classes
    grades_df = grades_df[~grades_df["Course"].str[0].isin(["G"])]

    # grades_pvt
    grades_pvt = (
        pd.pivot_table(
            grades_df,
            index=["StudentID"],
            columns="failing?",
            values="Pct",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )

    ## student's failing one class
    students_failing_one_class = grades_pvt[grades_pvt[True] == 1]["StudentID"]

    students_df = grades_df[
        (grades_df["StudentID"].isin(students_failing_one_class))
        & (grades_df["failing?"])
    ]

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df = cr_3_07_df[["StudentID", "LastName", "FirstName"]]

    students_df = students_df.merge(cr_3_07_df, on="StudentID", how="inner")

    ## process assignments
    filename = utils.return_most_recent_report_by_semester(files_df, "assignments", year_and_semester=year_and_semester)
    assignments_df = utils.return_file_as_df(filename)
    # Keep Assignments from Marking Period
    assignments_df = assignments_df[assignments_df["Term"] == term]
    # keep just assignments from relevant students
    assignments_df = assignments_df[
        assignments_df["StudentID"].isin(students_failing_one_class)
    ]
    # keep assignments less than passing
    assignments_df = assignments_df[assignments_df["Percent"] < 65]
    ## drop duplicates due to mutliple objectives
    assignments_df = assignments_df.drop_duplicates(
        subset=["StudentID", "Course", "Assignment", "DueDate"]
    )
    assignments_df = assignments_df.sort_values(
        by=["Category", "Missing", "WorthPoints"], ascending=[True, True, False]
    )

    students_df["flowables"] = students_df.apply(
        return_student_flowables, axis=1, args=(assignments_df,)
    )

    ## sort by teacher, course, section
    students_df = students_df.sort_values(
        by=["Teacher1", "Course", "Section", "FirstName"]
    )

    flowables = students_df["flowables"].explode().to_list()

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    return f


def return_student_flowables(student_row, assignments_df):
    flowables = []

    StudentID = student_row["StudentID"]
    first_name = student_row["FirstName"]
    last_name = student_row["LastName"]

    course = student_row["Course"]
    section = student_row["Section"]
    teacher = student_row["Teacher1"]

    student_assignments = assignments_df[
        (assignments_df["StudentID"] == StudentID)
        & (assignments_df["Course"] == course)
    ]
    table_cols = ["Assignment", "Category", "DueDate", "RawScore", "WorthPoints"]
    student_assignments = student_assignments[table_cols]

    paragraph = Paragraph(
        f"{teacher} - {course}/{section}",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    flowables.append(Spacer(width=0, height=0.25 * inch))

    flowables.extend(letter_head)
    paragraph = Paragraph(
        f"Dear {first_name.title()} {last_name.title()} ({StudentID})",
        styles["BodyText"],
    )
    flowables.append(paragraph)
    paragraph = Paragraph(
        f"According to your current assignments entered in JupiterGrades, you are not passing one of your classes. There is still time to finish out this marking period strong. Below is a list of assignments for you to review <b>with your teacher</b> to identify which assignments to focus on. Your teacher will let you know which missing assignments can still be turned in and which assignments can go through the revision processes.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    assignments_table = utils.return_df_as_table(
        student_assignments, table_cols, fontsize=9
    )
    flowables.append(Spacer(width=0, height=0.1 * inch))
    flowables.append(assignments_table)
    flowables.append(Spacer(width=0, height=0.1 * inch))

    paragraph = Paragraph(
        f"It can be overwhelming trying to make up your classwork, especially if you are missing many items. Here are two strategies that can be successful.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    strategies_lst = ListFlowable(
        [
            Paragraph(
                "<b>The Snowball Method</b> - Pick out 2-3 small assignments you can get through quickly. The momentum of knocking out a few assignments can snowball into more success. And these smaller assignments will help you with the larger ones.",
                styles["Normal"],
            ),
            Paragraph(
                "<b>The Avalanche Method</b> - Review your low scores and select the assignment with the most worth points in the performance category. This assignment will have the largest impact on changing your grade. Think about how to break it down into smaller chunks with a to-do list and snowball method your way to the finish line!",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="squarelrs",
    )
    flowables.append(strategies_lst)

    paragraph = Paragraph(
        f"Everyone here at HSFI is here to help! If you need more support or help making a plan, stop by your wellness center to chat with your guidance counselor",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    flowables.extend(closing)
    flowables.append(PageBreak())
    return flowables
