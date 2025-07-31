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


import app.scripts.utils.utils as utils
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

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
        bottomMargin=0.25 * inch,
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)

    master_schedule_df = master_schedule_df[master_schedule_df["PD"].isin([1, 2, 3])]
    master_schedule_df = master_schedule_df[
        master_schedule_df["Course Code"].str[0] != "Z"
    ]

    master_schedule_df["Room"] = master_schedule_df["Room"].astype(int)

    labels_to_make = master_schedule_df.drop_duplicates(subset=['Teacher Name']).sort_values(by=['Teacher Name']).to_dict('records')

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    return f


def draw_label(label, width, height, obj):
    if obj:
        TeacherName = obj['Teacher Name']
        Room = obj['Room']
        label.add(
            shapes.String(5, 46, f"{TeacherName}", fontName="Helvetica", fontSize=16)
        )
        label.add(
            shapes.String(5, 10, f"{Room}", fontName="Helvetica", fontSize=18)
        )
