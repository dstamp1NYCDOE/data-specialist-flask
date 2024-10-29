import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for
from werkzeug.utils import secure_filename

from reportlab.platypus import (
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    SimpleDocTemplate,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    df_lst = []
    files_lst = request.files.getlist("rdsc_files")

    for file in files_lst:
        
        df = pd.read_excel(file, skiprows=3)

        df = df.rename(columns={"Student ID": "StudentID", "Attd. Date": "Date"})

        dff = df[["StudentID", "Student Name", "Teacher", "Date"]]
        dfff = df[["StudentID", "Student Name", "Teacher.1", "Date"]]
        dfff = dfff.rename(columns={"Teacher.1": "Teacher"})

        df_lst.append(dff)
        df_lst.append(dfff)

    df = pd.concat(df_lst)
    df = df.dropna()
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%y")

    week_of_date = min(df["Date"])
    week_of_date = week_of_date.strftime("%Y_%m_%d")

    ## process attendance
    filename = request.files[form.jupiter_attendance_file.name]
    attendance_df = pd.read_csv(filename)
    attendance_df["Date"] = pd.to_datetime(attendance_df["Date"])
    attendance_df['Pd'] = attendance_df['Period'].str.extract(r"(\d{1,2})")

    rdsc_students = df["StudentID"].unique()
    attendance_df = attendance_df[attendance_df["StudentID"].isin(rdsc_students)]

    temp_lst = []
    for (student, date), attendance_df in attendance_df.groupby(["StudentID", "Date"]):

        attendance_dict = (
            attendance_df[["Pd", "Attendance"]].set_index("Pd").T.to_dict()
        )
        attendance_dict = {x: y["Attendance"] for (x, y) in attendance_dict.items()}

        attendance_dict["StudentID"] = student
        attendance_dict["Date"] = date

        temp_lst.append(attendance_dict)

    parsed_attd_df = pd.DataFrame(temp_lst).fillna("")
    parsed_cols = ["StudentID", "Date", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    missing_cols = [x for x in parsed_cols if x not in parsed_attd_df.columns]
    for missing_col in missing_cols:
        parsed_attd_df[missing_col] = ''
    parsed_attd_df = parsed_attd_df[parsed_cols]

    parsed_attd_df = df[["StudentID", "Date", "Student Name"]].merge(
        parsed_attd_df, on=["StudentID", "Date"], how="left"
    )

    ## build letters

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
            name="BodyJustify",
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
        Paragraph("Assistant Principal", styles["Normal_RIGHT"]),
    ]

    directions_txt = """Confirmation of Attendance scan sheets are used to change attendance of students marked absent on the daily attendance roster (Blue Sheets) but marked present for 1 or 2 periods on the SPAT sheets (White Sheets). This may happen because (1) a student arrived after period 3, (2) a student was not in class period 3, or (3) a student was marked present by mistake in 1 or 2 periods. Subject class teachers should confirm the attendance of each student on the sheet by entering absent, late or present. Teachers should sign each sheet."""
    directions_paragraph = Paragraph(directions_txt, styles["BodyText"])

    intro_txt = """Below you will find a list of students per date showing their Jupiter attendance across all periods. What was entered in Jupiter may be different than what was bubbled on the white sheet. This information may be useful for you as you are confirming student attendance."""
    intro_paragraph = Paragraph(intro_txt, styles["BodyText"])

    flowables = []
    for teacher, students_df in df.groupby("Teacher"):
        flowables.extend(letter_head)
        paragraph = Paragraph(f"Dear {teacher},", styles["BodyText"])
        flowables.append(paragraph)

        flowables.append(directions_paragraph)

        flowables.append(Spacer(width=0, height=0.25 * inch))

        flowables.append(intro_paragraph)
        flowables.append(Spacer(width=0, height=0.25 * inch))

        for date, students_dff in students_df.groupby("Date"):
            students_lst = students_dff["StudentID"]
            student_attd_df = parsed_attd_df[
                (parsed_attd_df["Date"] == date)
                & (parsed_attd_df["StudentID"].isin(students_lst))
            ]
            student_attd_df = student_attd_df.drop_duplicates()

            paragraph = Paragraph(f"{date.strftime('%d-%b-%Y')}", styles["BodyText"])
            flowables.append(paragraph)
            attd_grid_flowable = return_attd_grid_as_table(
                student_attd_df,
                ["Student Name", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            )
            flowables.append(attd_grid_flowable)
            flowables.append(Spacer(width=0, height=0.25 * inch))

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

    download_name = f"Confirmation_Cover_Sheets_{week_of_date}.pdf"

    return f, download_name


def return_attd_grid_as_table(df, cols):
    table_data = df[cols].values.tolist()
    table_data.insert(0, cols)
    attendance_col_widths = [2.5 * inch] + 9 * [0.25 * inch]
    t = Table(
        table_data, colWidths=attendance_col_widths, repeatRows=1, rowHeights=None
    )
    t.setStyle(
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
    return t
