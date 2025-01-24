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
    
    MATERIAL = 'Direction_Labels'
    if course != 'All':
        exam_book_df = exam_book_df[exam_book_df["Course Code"] == course]
    download_name = f"{administration}_{course}_{MATERIAL}.pdf"

    labels_to_make = []
    for (day, time, exam_title), exam_sections_by_exam_df in exam_book_df.groupby(
        ["Day", "Time", "ExamTitle"]
    ):
    
        for room, sections_in_room_df in exam_sections_by_exam_df.groupby('Room'):
            room_label = {
                'ExamTitle':exam_title,
                'Day':sections_in_room_df.iloc[0]['Day'],
                'Type':sections_in_room_df.iloc[0]['Type'],
                'Time':sections_in_room_df.iloc[0]['Time'],
                'Course':sections_in_room_df.iloc[0]['Course Code'],
                'Sections':sections_in_room_df['Section'].to_list(),
                'Room':sections_in_room_df.iloc[0]['Room'],
                'ExamAdministration':administration,
            }
            labels_to_make.append(room_label)

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)    
    f = BytesIO()
    sheet.save(f)
    f.seek(0)
    return f, download_name


def draw_label(label, width, height, obj):
    exam_title = obj.get('ExamTitle')
    type = obj.get("Type")
    room = obj.get("Room")
    Day = obj.get("Day")
    Time = obj.get("Time")
    Part = obj.get('Part')

    

    label.add(
        shapes.String(4, 52, f"{exam_title}", fontName="Helvetica", fontSize=18)
    )    
    label.add(
        shapes.String(125, 55, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
    )



    label.add(
        shapes.String(4, 4, f"{room}", fontName="Helvetica", fontSize=40)
    )
    label.add(
        shapes.String(125, 4, f"{type}", fontName="Helvetica", fontSize=7)
    )

    label.add(
            shapes.String(
                4, 38, f"Section: {obj['Sections']}", fontName="Helvetica", fontSize=11
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
