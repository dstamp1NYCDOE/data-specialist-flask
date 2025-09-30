from flask import current_app, session
from dotenv import load_dotenv

import pygsheets
import pandas as pd

import os
import numpy as np
from io import BytesIO

import datetime as dt
from app.scripts import scripts, files_df, photos_df, gsheets_df
import app.scripts.utils as utils

from app.scripts.summer.programming import programming_utils

load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


from reportlab.graphics import shapes
from reportlab.lib import colors

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

styles = getSampleStyleSheet()


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

    flowables = []

    for day in ['Day1','Day2']:
        cols = ['LastName','FirstName','CellPhone',f"{day}-Hours",f'{day}-Room',f'{day}-Notes']
        proctors_dff = proctors_df[proctors_df[f'{day}-Room']!='']
        for hub, proctors_by_hub_df in proctors_dff.groupby(f'{day}-Hub'):
            paragraph = Paragraph(
                f"{month} {school_year+1}\nRegents\nHub {hub} Proctors - {day}",
                styles["Title"],
            )
            flowables.append(paragraph)          

            paragraph = Paragraph(
                """
Below is the list of proctors/scorers assigned to the hub for the particular regents testing day. To the extent possible, proctors assigned to the 8am to 4pm shift will cover both tests scheduled in the room (typically two GenEd assignments). Proctors have been pre-assigned to testing rooms to make day of assigning quicker, but there may be absences or late arrivals that will necessitate reassigning reserves or other proctors. Likewise a testing room may have no students show up so after the uniform admissions deadlines (9:15 AM / 1:15 PM), you can close out that room and redeploy the proctors.
                """,
                styles["Normal"],
            )
            flowables.append(paragraph)          

            paragraph = Paragraph(
                """
All proctors receive a 30 minute lunch break. For GenEd Proctors, the break will occur between the two exams (approximately 11:45 AM - 12:15 PM) and they report back to the testing hub at 12:15 PM. For extended time rooms, the lunch break occurs after the AM exam or before the PM exam. Once a testing room is complete, the proctors report back to the testing hub to be used as reserve/relief proctors to provide bathroom breaks. Also utilize them for organization purposes. Your hub may receive a phone call from another hub or test testing office to request a redeployment of proctors based on needs around the building.
                """,
                styles["Normal"],
            )
            flowables.append(paragraph)    

            dff = proctors_by_hub_df[cols].copy()
            dff = dff.sort_values(by=[f"{day}-Hours","LastName", "FirstName"],ascending=[False,True,True])
            flowables.append(return_proctors_by_hub(dff,cols))

            flowables.append(PageBreak())



    

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    filename = f"{year_and_semester}ProctorRostersByHub.pdf"
    return f, filename



def return_proctors_by_hub(proctors_df,cols):
    proctors_df["✓"] = "     "
    proctors_df["Record 30 min Break"] = "     "
    cols = ["✓"] + cols + ["Record 30 min Break"]
    table_data = proctors_df[cols].values.tolist()

    table_data.insert(0, cols)
    t = Table(table_data, colWidths=None, repeatRows=1, rowHeights=None)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t

