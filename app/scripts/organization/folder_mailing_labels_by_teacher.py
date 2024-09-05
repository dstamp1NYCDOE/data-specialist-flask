import pandas as pd

from werkzeug.utils import secure_filename

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.graphics import shapes

from io import BytesIO
import re

from app.scripts import scripts, files_df, photos_df


def main(form, request):

    filename = form.student_list.data

    sort_by_data = request.files[form.student_list.name]

    try:
        sort_by_df = pd.read_excel(sort_by_data)
    except ValueError:
        sort_by_df = pd.read_csv(sort_by_data)


    if form.student_list_source.data == "STARS_Classlist_Report":
        sort_by_df = sort_by_df.rename(columns={"PeriodId || '/'": "Period"})
        sort_by_df = sort_by_df.astype(str)
        
        group_by = ["TeacherName", "Period", "CourseCode", "SectionId"]
        sort_by_df["sort_by_col"] = (
            sort_by_df["TeacherName"]
            + " - P"
            + sort_by_df["Period"]
            + " "
            + sort_by_df["CourseCode"]
            + "/"
            + sort_by_df["SectionId"]
        )


    if form.student_list_source.data == "teacher_and_room_list":
        

        sort_by_df = sort_by_df.astype(str)
        group_by = ["TeacherName", "Room"]
        sort_by_df["sort_by_col"] = (
            sort_by_df["TeacherName"] + " - Room" + sort_by_df["Room"]
        )

    sort_by_df = sort_by_df.drop_duplicates(subset=['sort_by_col']).sort_values(by=['sort_by_col'])
    sort_by_list = sort_by_df.to_dict('records')

    

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(sort_by_list)
    sheet.save(f)
    f.seek(0)

    return f


import labels

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


def draw_label(label, width, height, obj):

    label.add(
        shapes.String(
            5,
            40,
            obj['TeacherName'],
            fontName="Helvetica",
            fontSize=20,
        )
    )

    label.add(
        shapes.String(
            5,
            10,
            obj['Room'],
            fontName="Helvetica",
            fontSize=24,
        )
    )
