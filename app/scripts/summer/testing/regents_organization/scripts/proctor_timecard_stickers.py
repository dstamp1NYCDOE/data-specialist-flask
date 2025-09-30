from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

import pandas as pd
import os
from io import BytesIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

from app.scripts.summer.testing.regents_organization import (
    utils as regents_organization_utils,
)

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

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"


    proctors_google_sheet = utils.return_gsheet_url_by_title(gsheets_df,'regents_exam_book',year_and_semester=year_and_semester)

    proctors_df = utils.return_google_sheet_as_dataframe(proctors_google_sheet, sheet='Proctors')
    proctors_df = proctors_df.fillna('')

    proctors_df = proctors_df[proctors_df['FirstName']!='']



    proctors_df = proctors_df.sort_values(by=["LastName",'FirstName'])

    labels_to_make = []
    # for (day, time), proctors_dff in proctors_df.groupby(["Day", "Time"]):
    #     labels_to_make.extend(proctors_dff.to_dict("records"))
    #     remainder = len(labels_to_make) % 30
    #     for i in range(30 - remainder):
    #         labels_to_make.append({})

    labels_to_make.extend(proctors_df.to_dict("records"))
    labels_to_make = [record for record in labels_to_make for _ in range(2)]

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)

    filename = f"{year_and_semester}ProctorTimeCardLabels.pdf"
    return f, filename


def draw_label(label, width, height, obj):
    DAY_ONE = '8/19/2025'
    DAY_TWO = '8/20/2025'
    DAY_THREE = '8/21/2025'
    
    if obj:
        label.add(
            shapes.String(
                4,
                52,
                f'{obj["LastName"]}, {obj["FirstName"]}',
                fontName="Helvetica",
                fontSize=16,
            )
        )
        label.add(
            shapes.String(
                4,
                38,
                f'File#: {obj["File#"]}',
                fontName="Helvetica",
                fontSize=13,
            )
        )

    days = ['Day1','Day2','Day3']
    dates = [DAY_ONE, DAY_TWO, DAY_THREE]
    START = 4
    GAP = 56
    start_pos = [START, START+GAP, START+2*GAP]

    zipped_lst = zip(days, dates, start_pos)

    for (day,date,start_pos) in zipped_lst:
        if obj[f"{day}-Hub"]:
            label.add(
                shapes.String(
                    start_pos,
                    5,
                    f"Report to {obj[f'{day}-Hub']}",
                fontName="Helvetica",
                fontSize=7,
            )
            )

            label.add(
                shapes.String(
                    start_pos,
                    14,
                    f"{obj[f'{day}-Hours']}",
                fontName="Helvetica",
                fontSize=7,
            )
            )

            label.add(
                shapes.String(
                    start_pos,
                    24,
                    f"{date}",
                fontName="Helvetica",
                fontSize=9,
            )
            )