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

def main(form, request):
    filename = request.files[form.kiosk_file.name]
    kiosk_df = pd.read_csv(filename)

    labels_to_make = kiosk_df.to_dict('records')

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    filename = 'SmartPassKioskLabels.pdf'
    return f, filename


def draw_label(label, width, height, obj):
    if obj:
        username = obj['Kiosk Username']
        password = obj['Kiosk Password']
        label.add(
            shapes.String(5, 55, f"Username:", fontName="Courier", fontSize=14)
        )
        label.add(
            shapes.String(5, 40, f"{username}", fontName="Courier", fontSize=14)
        )

        label.add(
            shapes.String(5, 25, f"Password:", fontName="Courier", fontSize=14)
        )
        label.add(
            shapes.String(5, 10, f"{password}", fontName="Courier", fontSize=14)
        )

