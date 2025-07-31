from app.scripts import scripts, files_df, gsheets_df
from flask import render_template, request, send_file, session, current_app
from io import BytesIO
from reportlab.graphics import shapes
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
import app.scripts.utils as utils
import datetime as dt

import labels

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


def main(course, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        administration = f"January {school_year+1}"
    elif term == 2:
        administration = f"June {school_year+1}"

    gsheet_url = utils.return_gsheet_url_by_title(
        gsheets_df, "regents_exam_book", year_and_semester
    )

    exam_book_df = utils.return_google_sheet_as_dataframe(gsheet_url, sheet="ExamBook")

    if course != "All":
        exam_book_df = exam_book_df[exam_book_df["Course Code"] == course]
        filename = f"{course}_Folder_Labels.pdf"
    else:
        filename = f"All_Folder_Labels.pdf"

    labels_to_make = []
    section_99_labels = []

    for (day, time, exam_title), sections_df in exam_book_df.groupby(
        ["Day", "Time", "ExamTitle"]
    ):
        for part in ["Part1", "Part2"]:
            sections_df["Part"] = part
            labels_to_make.extend(sections_df.to_dict("records"))
            section_99_dict = {
                "Part": part,
                "Section": "99",
                "ExamTitle": exam_title,
                "Room": "Walkins",
                "Day": day,
                "Time": time,
                "Type": "",
            }
            section_99_labels.append(section_99_dict)
        for i in range(30 - len(labels_to_make) % 30):
            labels_to_make.append({})

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)


    sheet.add_labels(section_99_labels)

    f = BytesIO()
    sheet.save(f)
    f.seek(0)
    return f, filename


def draw_label(label, width, height, obj):
    if obj:
        exam_title = obj.get("ExamTitle")
        type = obj.get("Type")
        room = obj.get("Room")
        Day = obj.get("Day")
        Time = obj.get("Time")
        Part = obj.get("Part")

        label.add(shapes.String(4, 52, f"{exam_title}", fontName="Helvetica", fontSize=18))
        label.add(
            shapes.String(125, 55, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
        )

        label.add(shapes.String(125, 30, f"{Part}", fontName="Helvetica", fontSize=18))

        label.add(shapes.String(4, 4, f"{room}", fontName="Helvetica", fontSize=40))
        label.add(shapes.String(125, 4, f"{type}", fontName="Helvetica", fontSize=7))

        label.add(
            shapes.String(
                4, 38, f"Section: {obj.get('Section')}", fontName="Helvetica", fontSize=11
            )
        )


def return_exam_name(course):
    exam_code = course[0:4]
    exam_dict = {
        "SXRP": "Physics",
        "EXRC": "ELA",
        "SXRK": "LivEnv",
        "HXRC": "Global Hist",
        "HXRK": "USH",
        "MXRC": "Algebra I",
        "MXRF": "Algebra I",
        "SXRX": "Chemistry",
        "SXRU": "Earth Sci",
        "MXRK": "Geometry",
        "MXRN": "AlgII Trig",
        "FXTS": "Spanish",
    }
    return exam_dict.get(exam_code)
