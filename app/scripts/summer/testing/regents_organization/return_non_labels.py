from flask import session, current_app
import app.scripts.utils as utils
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
        name="Title_LARGE",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=72,
        leading=int(72 * 1.2),
    )
)


import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils
import app.scripts.summer.testing.regents_organization.return_SAR_flowables as return_SAR_flowables


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

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Section"] > 1]

    cr_1_08_df = cr_1_08_df.merge(photos_df, on=["StudentID"], how="left")

    cr_1_08_df["ExamAdministration"] = f"{month} {school_year+1}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    regents_calendar_df["exam_num"] = (
        regents_calendar_df.groupby(["Day", "Time"])["CourseCode"].cumcount() + 1
    )
    section_properties_df = pd.read_excel(path, sheet_name="SummerSectionProperties")

    ## attach Exam Info
    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )
    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    ## attach section properties
    cr_1_08_df = cr_1_08_df.merge(
        section_properties_df[["Section", "Type"]], on=["Section"], how="left"
    )

    cr_1_08_df["HubLocation"] = cr_1_08_df.apply(
        regents_organization_utils.return_hub_location, axis=1
    )

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left")

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_Exam_NonLabels.pdf"
    else:
        exam_to_merge = form.exam_title.data
        filename = f"{month}_{school_year+1}_{exam_to_merge}_NonLabels.pdf"
        cr_1_08_df = cr_1_08_df[cr_1_08_df["ExamTitle"] == exam_to_merge]

    flowables = []

    cr_1_08_df = cr_1_08_df.drop_duplicates(subset=["StudentID", "Course"])
    for (hub, day), students_by_hub_df in cr_1_08_df.groupby(["HubLocation", "Day"]):

        paragraph = Paragraph(
            f"Testing Hub {int(hub)} - Documents - {day}",
            styles["Heading2"],
        )
        flowables.append(paragraph)
        hub_rooms_pvt = (
            pd.pivot_table(
                students_by_hub_df,
                index=["Day", "Time", "Room", "ExamTitle"],
                values=["StudentID", "Type", "Section"],
                aggfunc={
                    "Section": combine_lst_of_section_properties,
                    "Type": combine_lst_of_section_properties,
                    "StudentID": "count",
                },
            )
            .reset_index()
            .rename(columns={"StudentID": "#_of_students"})
        )
        hub_rooms_pvt["Assigned Proctor (write in name)"] = ""
        hub_rooms_pvt = hub_rooms_pvt[
            [
                "Time",
                "Room",
                "ExamTitle",
                "Section",
                "Type",
                "#_of_students",
                "Assigned Proctor (write in name)",
            ]
        ].sort_values(by=["Time", "ExamTitle", "Room"])
        for time in ["AM", "PM"]:
            paragraph = Paragraph(
                f"{time}",
                styles["Heading3"],
            )
            flowables.append(paragraph)
            T = return_testing_rooms_by_hub(
                hub_rooms_pvt[hub_rooms_pvt["Time"] == time]
            )
            flowables.append(T)
        flowables.append(PageBreak())
        for (time, room), students_in_room_df in students_by_hub_df.groupby(
            ["Time", "Room"]
        ):
            exam_title = students_in_room_df.iloc[0]["ExamTitle"]
            paragraph = Paragraph(
                f"{day} - {time} {int(room)} - {exam_title}",
                styles["Heading2"],
            )
            flowables.append(paragraph)
            flowables.extend(return_SAR_flowables.main(students_in_room_df))
            flowables.append(PageBreak())

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


def combine_lst_of_section_properties(x):
    x = x.unique()
    output = "\n".join(str(v) for v in x)
    return output


def return_testing_rooms_by_hub(hub_rooms_pvt):

    table_data = hub_rooms_pvt.values.tolist()
    cols = hub_rooms_pvt.columns
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=None, repeatRows=1, rowHeights=None)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t
