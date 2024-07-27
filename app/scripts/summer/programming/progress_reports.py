import pandas as pd
import os
import numpy as np
import datetime as dt
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors

from zipfile import ZipFile
from io import BytesIO
from flask import current_app, session
from dotenv import load_dotenv
import app.scripts.utils as utils
import pygsheets
from app.scripts import scripts, files_df, photos_df, gsheets_df

load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    sending_school = form.data["sending_school"]

    summer_school_gradebooks_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_gradebooks_hub", year_and_semester
    )

    gradebook_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url, sheet="AllStudentsBySchool"
    )
    gradebook_df = gradebook_df.dropna(subset="FinalMark")

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    gradebook_df = gradebook_df.merge(dbn_df, on="school_name", how="left").fillna(
        "NoSendingSchool"
    )

    if sending_school != "ALL":
        gradebook_df = gradebook_df[gradebook_df["Sending school"] == sending_school]

    attendance_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url, sheet="AllStudentsAttendance"
    )

    student_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Teacher1",
        "Period",
        "school_name",
        "dbn",
    ]

    gradebook_df = gradebook_df.sort_values(by=["Period"], ascending=True)

    gradebook_df["Teacher1"] = gradebook_df["Teacher1"].apply(lambda x: str(x)[0:10])
    gradebook_df["Course Name"] = gradebook_df["Course Name"].apply(
        lambda x: str(x)[0:16]
    )

    gradebook_df["distribute_by_this_period"] = gradebook_df.apply(
        distribute_by_this_period, args=(gradebook_df,), axis=1
    )
    students_df = gradebook_df[gradebook_df["distribute_by_this_period"]]

    days_of_school = attendance_df["total_absences"].max()
    no_show_student_IDS = attendance_df[
        attendance_df["total_absences"] == days_of_school
    ]["StudentID"]

    dates_lst = [
        "7/10",
        "7/11",
        "7/15",
        "7/16",
        "7/17",
        "7/18",
        "7/22",
        "7/23",
        "7/24",
    ]

    attendance_output_cols = [
        "total_absences",
    ] + dates_lst

    gradebook_output_cols = [
        "Teacher1",
        "Course Name",
        "Period",
        "FinalMark",
    ] + dates_lst

    flowables = []

    students_who_have_attended_df = students_df[
        ~students_df["StudentID"].isin(no_show_student_IDS)
    ]

    if sending_school == "ALL":

        for (
            teacher,
            period,
        ), students_temp_df in students_who_have_attended_df.groupby(
            ["Teacher1", "Period"]
        ):
            for index, student in students_temp_df.sort_values(
                by=["LastName", "FirstName"]
            ).iterrows():
                StudentID = student["StudentID"]
                student_grades_df = gradebook_df[
                    gradebook_df["StudentID"] == StudentID
                ][gradebook_output_cols]
                student_attendance_df = attendance_df[
                    attendance_df["StudentID"] == StudentID
                ].drop_duplicates(subset=["StudentID"])[attendance_output_cols]
                student_flowables = return_student_progress_report(
                    student, student_grades_df, student_attendance_df
                )
                flowables.extend(student_flowables)
    else:
        for index, student in students_who_have_attended_df.sort_values(
            by=["LastName", "FirstName"]
        ).iterrows():
            StudentID = student["StudentID"]
            student_grades_df = gradebook_df[gradebook_df["StudentID"] == StudentID][
                gradebook_output_cols
            ]
            student_attendance_df = attendance_df[
                attendance_df["StudentID"] == StudentID
            ].drop_duplicates(subset=["StudentID"])[attendance_output_cols]
            student_flowables = return_student_progress_report(
                student, student_grades_df, student_attendance_df
            )
            flowables.extend(student_flowables)

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    # list_of_files.append(f)

    # stream = BytesIO()
    # with ZipFile(stream, "w") as zf:
    #     for file in list_of_files:
    #         zf.write(file)
    # stream.seek(0)
    return f


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
styles.add(
    ParagraphStyle(
        name="TITLE", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=150
    )
)

current_date = dt.datetime.today().strftime("%m/%d/%Y")


TEACHER_COL = 1.00
COURSE_COL = 1.25
PERIOD_COL = 0.5
FINAL_MARK_COL = 0.75
TOTAL_DAYS_ABSENT_COL = TEACHER_COL + COURSE_COL + PERIOD_COL + FINAL_MARK_COL

DATE_COL = 0.29

attendance_col_widths = [(TOTAL_DAYS_ABSENT_COL) * inch] + 25 * [DATE_COL * inch]
grades_col_widths = [
    TEACHER_COL * inch,
    COURSE_COL * inch,
    PERIOD_COL * inch,
    FINAL_MARK_COL * inch,
] + 25 * [DATE_COL * inch]

rubric_table_data = [
    ["Daily Grade", "Criteria"],
    [
        "5 - A",
        "Full period participation and attendance. No phone use. Short bathroom break. Excellent work products.",
    ],
    [
        "4 - B",
        "One of the following: Less than full period participation and attendance. Late or longer bathroom break. Minimal phone use. Very good work products.",
    ],
    [
        "3 - C",
        "One of the following: Less than full period participation and attendance. Very late or long bathroom break. Extensive phone use. Medium work products.",
    ],
    [
        "2 - D",
        "One of the following: Less than full period participation and attendance. Very late or long bathroom break. Extensive phone use. Poor work products.",
    ],
    [
        "1 - F",
        "Two of the following: Less than full period participation and attendance. Very late or long bathroom break. Extensive phone use. Poor work products.",
    ],
    ["0 - F", "Absent"],
]
rubric_table = Table(
    rubric_table_data,
    repeatRows=1,
)
rubric_table.setStyle(
    TableStyle(
        [
            ("ALIGN", (0, 0), (100, 100), "CENTER"),
            ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (100, 100), 1),
            ("RIGHTPADDING", (0, 0), (100, 100), 1),
            ("BOTTOMPADDING", (0, 0), (100, 100), 1),
            ("TOPPADDING", (0, 0), (100, 100), 1),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
        ]
    )
)


def return_student_progress_report(student, student_grades_df, student_attendance_df):
    FirstName = student["FirstName"]
    LastName = student["LastName"]
    StudentID = student["StudentID"]
    TeacherName = student["Teacher1"]
    Period = student["Period"]
    school_name = student["school_name"]

    student_flowables = []

    student_name = f"{FirstName} {LastName} ({StudentID})"
    teacher_sortby = f"{TeacherName} - Period{Period}"

    paragraph = Paragraph(teacher_sortby, styles["Heading3"])
    student_flowables.append(paragraph)

    paragraph = Paragraph(student_name, styles["Heading1"])
    student_flowables.append(paragraph)

    paragraph = Paragraph(school_name, styles["Heading2"])
    student_flowables.append(paragraph)

    paragraph_text = f"""
    Below is your current grades in your courses and your overall attendance as of {current_date}.
    """

    paragraph = Paragraph(paragraph_text, styles["BodyText"])
    student_flowables.append(paragraph)

    paragraph_text = f"""
    There is still plenty of time to improve your grades and it starts coming on time every day.
    """

    paragraph = Paragraph(paragraph_text, styles["BodyText"])
    student_flowables.append(paragraph)

    colWidths = None

    paragraph = Paragraph("Grades", styles["Heading4"])
    student_flowables.append(paragraph)

    student_flowables.append(rubric_table)
    student_flowables.append(Spacer(width=0, height=0.25 * inch))

    grade_tbl = return_schedule_df_as_table(
        student_grades_df, student_grades_df.columns, grades_col_widths
    )
    student_flowables.append(grade_tbl)

    paragraph = Paragraph("Daily Attendance", styles["Heading4"])
    student_flowables.append(paragraph)

    paragraph_text = f"""
    Attendance is taken in every class at the beginning and the end of the period. A student is considered present for the day if they are marked present or late in at least one class of the day. As a reminder, students have a 25 minute grace period to get to class before they are not admitted.
    """

    paragraph = Paragraph(paragraph_text, styles["BodyText"])
    student_flowables.append(paragraph)
    student_flowables.append(Spacer(width=0, height=0.25 * inch))

    attd_tbl = return_schedule_df_as_table(
        student_attendance_df, student_attendance_df.columns, attendance_col_widths
    )
    student_flowables.append(attd_tbl)

    student_flowables.append(PageBreak())

    return student_flowables


def distribute_by_this_period(student_row, cr_1_01_df):
    StudentID = student_row["StudentID"]
    Period = student_row["Period"]
    student_courses_df = cr_1_01_df[cr_1_01_df["StudentID"] == StudentID]
    non_pe_classes_df = student_courses_df[
        student_courses_df["Course"].str[0:2] != "PP"
    ]
    if len(non_pe_classes_df) == 0:
        return True
    else:
        last_period = non_pe_classes_df["Period"].max()
        return Period == last_period


def return_schedule_df_as_table(df, cols, colWidths):
    table_data = df[cols].values.tolist()
    table_data.insert(0, cols)
    rowHeights = (len(df) + 1) * [20]
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (100, 100), 1),
                ("RIGHTPADDING", (0, 0), (100, 100), 1),
                ("BOTTOMPADDING", (0, 0), (100, 100), 1),
                ("TOPPADDING", (0, 0), (100, 100), 1),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t
