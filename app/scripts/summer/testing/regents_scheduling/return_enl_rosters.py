import pandas as pd
import glob
from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df
import app.scripts.summer.testing.regents_scheduling.utils as regents_utils
import pandas as pd
import os
from io import BytesIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

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

import labels
from reportlab.graphics import shapes

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
    cr_1_08_df = cr_1_08_df.fillna({"Room": 202})
    cr_1_08_df["Room"] = cr_1_08_df["Room"].astype(int)

    filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df.merge(
        cr_3_07_df[["StudentID", "HomeLangCode"]], on="StudentID", how="left"
    )

    home_lang_codes_df = utils.return_home_lang_code_table(files_df)
    cr_1_08_df = cr_1_08_df.merge(home_lang_codes_df, on="HomeLangCode", how="left")
    cr_1_08_df["HomeLang"] = cr_1_08_df["HomeLang"].str[0:10]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(path, sheet_name="SummerSectionProperties")
    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    cr_1_08_df = cr_1_08_df.merge(
        section_properties_df, left_on=["Section"], right_on=["Section"], how="left"
    )

    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(
        regents_utils.return_full_exam_title
    )
    cr_1_08_df["ExamAdministration"] = f"{month} {school_year+1}"

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_ENL_Rosters.pdf"
    else:
        exam_to_merge = form.exam_title.data
        filename = f"{month}_{school_year+1}_{exam_to_merge}_ENL_Rosters.pdf"
        cr_1_08_df = cr_1_08_df[cr_1_08_df["ExamTitle"] == exam_to_merge]

    enl_exam_registrations_df = cr_1_08_df[cr_1_08_df["ENL?"] == 1]

    exam_flowables = []

    ## overall numbers by exam and then room
    enl_pvt_tbl = pd.pivot_table(
        enl_exam_registrations_df,
        index=["ExamTitle", "Room", "HomeLang"],
        # columns=["HomeLang"],
        values="StudentID",
        aggfunc="count",
    ).fillna("")
    enl_pvt_tbl = enl_pvt_tbl.reset_index()
    print(enl_pvt_tbl)
    T = return_df_as_table(enl_pvt_tbl)
    exam_flowables.append(T)
    exam_flowables.append(PageBreak())

    for (
        day,
        time,
        exam_title,
    ), exam_registrations_df in enl_exam_registrations_df.groupby(
        ["Day", "Time", "Exam Title"]
    ):

        for room, exam_room_registrations_df in exam_registrations_df.groupby("Room"):
            summary_pvt = pd.pivot_table(
                exam_room_registrations_df,
                index="HomeLang",
                values="StudentID",
                aggfunc="count",
            ).reset_index()
            summary_pvt.columns = ["HomeLang", "#"]

            paragraph = Paragraph(
                f"{day} - {time} - {exam_title} - Room{room} - ENL Info",
                styles["Heading2"],
            )
            exam_flowables.append(paragraph)

            paragraph = Paragraph(
                f"Each student shall receive access to a language glossery and home language exam when applicable. These materials are in the room or provided in the testing bag. For exams other than ELA, they may write their responses in their home language. Answers should all appear in one book. Students receive a minimum of 1.5x time accommodation - Their IEP may indicate other testing accommodations.",
                styles["Normal"],
            )
            exam_flowables.append(paragraph)

            pvt_T = return_df_as_table(summary_pvt)
            roster_T_cols = ["LastName", "FirstName", "HomeLang", "Type"]
            roster_T = return_df_as_table(
                exam_room_registrations_df, cols=roster_T_cols
            )

            chart_style = TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )

            exam_flowables.append(
                Table(
                    [[roster_T, pvt_T]],
                    colWidths=[5.75 * inch, 1.25 * inch],
                    style=chart_style,
                )
            )

            # exam_flowables.append(pvt_T)
            # exam_flowables.append(roster_T)

            exam_flowables.append(PageBreak())

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(exam_flowables)

    f.seek(0)
    return f, filename


def return_df_as_table(df, cols=None, colWidths=None, rowHeights=None):
    if cols:
        table_data = df[cols].values.tolist()
    else:
        cols = df.columns
        table_data = df.values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t
