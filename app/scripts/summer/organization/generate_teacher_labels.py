from app.scripts import scripts, files_df, photos_df

from flask import current_app, session
from io import BytesIO

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm

from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate

from pypdf import PdfWriter

import app.scripts.utils as utils
import labels
import numpy as np
import pandas as pd

PADDING = 0
specs = labels.Specification(
    215.9,
    279.4,
    3,
    10,
    66.6,
    25.2,
    corner_radius=2,
    left_margin=5,
    right_margin=5,
    top_margin=12.25,
    # bottom_margin=13,
    left_padding=PADDING,
    right_padding=PADDING,
    top_padding=PADDING,
    bottom_padding=PADDING,
    row_gap=0,
)


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

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
            name="TITLE75", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=75
        )
    )
    styles.add(
        ParagraphStyle(
            name="TITLE100",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=110,
        )
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    master_schedule_df = master_schedule_df[master_schedule_df["PD"].isin([1, 2, 3])]
    print(master_schedule_df)
    master_schedule_df = master_schedule_df[
        master_schedule_df["Course Code"].str[0] != "Z"
    ]

    master_schedule_df["Room"] = master_schedule_df["Room"].astype(int)

    # --- Sheet 1: one label per teacher ---
    teacher_labels_to_make = (
        master_schedule_df.drop_duplicates(subset=["Teacher Name"])
        .sort_values(by=["Teacher Name"])
        .to_dict("records")
    )

    teacher_buffer = BytesIO()
    teacher_sheet = labels.Sheet(specs, draw_teacher_label, border=True)
    teacher_sheet.add_labels(teacher_labels_to_make)
    teacher_sheet.save(teacher_buffer)
    teacher_buffer.seek(0)

    # --- Sheet 2: one label per class section ---
    section_labels_to_make = (
        master_schedule_df.drop_duplicates(
            subset=["Teacher Name", "Course Code", "PD"]
        )
        .sort_values(by=["Teacher Name", "Course Code", "PD"])
        .to_dict("records")
    )

    section_buffer = BytesIO()
    section_sheet = labels.Sheet(specs, draw_section_label, border=True)
    section_sheet.add_labels(section_labels_to_make)
    section_sheet.save(section_buffer)
    section_buffer.seek(0)

    # --- Merge both sheets into a single PDF ---
    f = BytesIO()
    merger = PdfWriter()
    merger.append(teacher_buffer)
    merger.append(section_buffer)
    merger.write(f)
    merger.close()

    f.seek(0)
    return f


def draw_teacher_label(label, width, height, obj):
    if obj:
        TeacherName = obj["Teacher Name"]
        Room = obj["Room"]
        label.add(
            shapes.String(5, 46, f"{TeacherName}", fontName="Helvetica", fontSize=16)
        )
        label.add(
            shapes.String(5, 10, f"{Room}", fontName="Helvetica", fontSize=18)
        )


def draw_section_label(label, width, height, obj):
    if obj:
        TeacherName = obj["Teacher Name"]
        CourseName = obj["Course Name"]
        CourseCode = obj["Course Code"]
        CourseSection = obj["Section"]
        PD = obj["PD"]
        Days = obj["Days"]
        if Days == "MTWR-":
            Days = ""
        else:
            Days = f" ({Days})"

        label.add(
            shapes.String(5, 46, f"{TeacherName}", fontName="Helvetica", fontSize=14)
        )
        label.add(
            shapes.String(5, 28, f"{CourseName}{Days}", fontName="Helvetica", fontSize=12)
        )
        label.add(
            shapes.String(
                5,
                10,
                f"{CourseCode}/{CourseSection} (P{PD})",
                fontName="Helvetica",
                fontSize=12,
            )
        )