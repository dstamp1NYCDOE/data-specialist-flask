from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

import labels
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


def main(form, request):
    filename = "ProctorRosters.pdf"
    proctor_assignments_csv = request.files[form.proctor_assignments_csv.name]
    proctor_assignments_df = pd.read_csv(proctor_assignments_csv)
    proctor_assignments_df["File#"] = proctor_assignments_df["File#"].astype(str)
    proctor_assignments_df["HubLocation"] = proctor_assignments_df[
        "HubLocation"
    ].astype(int)
    proctor_assignments_df = proctor_assignments_df.drop_duplicates(
        subset=["Name", "File#", "Day"]
    )

    flowables = []
    checkin_flowables = return_checkin_flowables(proctor_assignments_df)
    flowables.extend(checkin_flowables)

    hub_flowables = return_hub_flowables(proctor_assignments_df)
    flowables.extend(hub_flowables)

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f, filename


def return_hub_flowables(proctor_assignments_df):
    flowables = []
    for (day, hub_location, time), proctors_df in proctor_assignments_df.groupby(
        ["Day", "HubLocation", "Time"]
    ):
        paragraph = Paragraph(
            f"{day} - {time} Proctor Assignments - Room {hub_location}",
            styles["Heading2"],
        )
        flowables.append(paragraph)
        proctors_by_hub_table = return_proctors_by_hub(proctors_df)
        flowables.append(proctors_by_hub_table)
        flowables.append(PageBreak())

    return flowables


def return_proctors_by_hub(proctors_df):
    proctors_df = proctors_df.sort_values(by=["Name"])
    proctors_df["✓"] = "     "
    cols = ["✓", "Name", "File#", "Hours", "Room", "ExamTitle", "Type"]
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


def return_checkin_flowables(proctor_assignments_df):
    flowables = []
    for (day, time), proctors_df in proctor_assignments_df.groupby(["Day", "Time"]):
        paragraph = Paragraph(
            f"{day} - {time} Proctor Checkin Roster",
            styles["Heading2"],
        )
        flowables.append(paragraph)
        proctor_checkin_table = return_proctor_checkin_table(proctors_df)
        flowables.append(proctor_checkin_table)
        flowables.append(PageBreak())

    return flowables


def return_proctor_checkin_table(proctors_df):
    proctors_df = proctors_df.sort_values(by=["Name"])
    proctors_df["✓"] = "     "
    cols = [
        "✓",
        "Name",
        "File#",
        "Hours",
        "Category",
        "HubLocation",
    ]
    table_data = proctors_df[cols].values.tolist()

    table_data.insert(0, cols)
    t = Table(table_data, colWidths=None, repeatRows=1, rowHeights=None)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t
