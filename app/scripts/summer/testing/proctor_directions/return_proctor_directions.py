from flask import session, current_app
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

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

from app.scripts.summer.testing.regents_organization import (
    utils as regents_organization_utils,
)
import app.scripts.summer.testing.proctor_directions.return_proctor_direction_flowables as return_proctor_direction_flowables


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = f"{month}_{school_year+1}_Proctor_Directions_By_Exam.pdf"

    cr_1_08_df = regents_organization_utils.return_processed_registrations()

    exam_book_df = cr_1_08_df.drop_duplicates(subset=["Course", "Section"])

    rooms_df = exam_book_df.drop_duplicates(subset=["Course", "Room"])

    rooms_df["flowables"] = rooms_df.apply(
        return_proctor_direction_flowables.main, args=(exam_book_df,), axis=1
    )

    flowables = []

    # for (hub_location, day, time), df in rooms_df.groupby(['hub_location','Day','Time']):
    for exam, df in rooms_df.groupby("ExamTitle"):
        df = df.sort_values(by=["Room"])
        temp_flowables = df["flowables"].explode()
        flowables.extend(temp_flowables)

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    # return '',''
    return f, filename
