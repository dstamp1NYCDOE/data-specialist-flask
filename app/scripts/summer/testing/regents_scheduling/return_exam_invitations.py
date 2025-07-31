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

import datetime as dt
import pandas as pd  #
import os

from io import BytesIO
from flask import session, current_app

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df

styles = getSampleStyleSheet()


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

    filename = utils.return_most_recent_report_by_semester(files_df, "1_08",year_and_semester=year_and_semester)
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df.fillna({"Room": 202})
    cr_1_08_df["Room"] = cr_1_08_df["Room"].astype(str)

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(
        path, sheet_name="SummerSectionProperties"
    ).fillna("")

    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )
    cr_1_08_df = cr_1_08_df.merge(section_properties_df, on=["Section"], how="left")
    cr_1_08_df = cr_1_08_df.merge(photos_df, on=["StudentID"], how="left")

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left")

    sending_school = form.data["sending_school"]
    if sending_school != "ALL":
        cr_1_08_df = cr_1_08_df[cr_1_08_df["Sending school"] == sending_school]

    cr_1_08_df["Report Time"] = cr_1_08_df["Time"].apply(return_exam_report_time)

    # reformat_date
    cr_1_08_df["Day"] = pd.to_datetime(cr_1_08_df["Day"])
    cr_1_08_df = cr_1_08_df.sort_values(by=["Day"])

    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(return_full_exam_title)
    cr_1_08_df = cr_1_08_df.drop_duplicates(subset=["StudentID", "Course"])

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "photo_filename",
        "Sending school",
        "Day",
        "Report Time",
        "Exam Title",
        "Room",
        "Section",
        "Type",
    ]

    cr_1_08_df = cr_1_08_df[cols]

    return generate_letters(cr_1_08_df)


def generate_letters_by_dbn(cr_1_08_df):
    output = []

    flowables = []
    for (
        sending_school,
        LastName,
        FirstName,
        StudentID,
    ), exams_df in cr_1_08_df.groupby(
        ["Sending school", "LastName", "FirstName", "StudentID"]
    ):
        student_flowables = generate_student_letter(exams_df)
        flowables.extend(student_flowables)
        flowables.append(PageBreak())

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def generate_letters(cr_1_08_df):
    output = []

    flowables = []
    for (LastName, FirstName, StudentID), exams_df in cr_1_08_df.groupby(
        ["LastName", "FirstName", "StudentID"]
    ):
        student_flowables = generate_student_letter(exams_df)
        flowables.extend(student_flowables)
        flowables.append(PageBreak())

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def return_exam_report_time(Time):
    if Time == "AM":
        return "7:45 AM"
    if Time == "PM":
        return "11:45 AM"


exam_cols = ["Exam Title", "Day", "Report Time", "Room", "Section", "Type"]


def generate_student_letter(exams_df):
    flowables = []

    school_year = session["school_year"]
    term = session["term"]
    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    StudentID = exams_df.iloc[0, :]["StudentID"]
    LastName = exams_df.iloc[0, :]["LastName"]
    FirstName = exams_df.iloc[0, :]["FirstName"]
    sending_school = exams_df.iloc[0, :]["Sending school"]

    paragraph = Paragraph(
        f"{month} {school_year+1} Regents Exam Invitations",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{LastName}, {FirstName} ({StudentID}) ----- {sending_school}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    try:

        photo_path = exams_df.iloc[0, :]["photo_filename"]
        I = Image(photo_path)
        I.drawHeight = 2.75 * inch
        I.drawWidth = 2.75 * inch
        I.hAlign = "CENTER"
        # flowables.append(I)
    except:
        I = ""
        pass

    T = return_df_as_table(exams_df, cols=exam_cols)
    # flowables.append(T)

    chart_style = TableStyle(
        [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    )

    flowables.append(
        Table(
            [[I, T]],
            colWidths=[3 * inch, 6.75 * inch],
            rowHeights=[3 * inch],
            style=chart_style,
        )
    )

    paragraph = Paragraph(
        "Please report to HSFI on time for your exams with your exam invitation, Photo ID, and all materials you need to test including pencils, pens, etc..",
        styles["Heading2"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        "You cannot have any communications device, including a cell phone, with you during this examination or during any breaks (such as a restroom visit). Such devices include, but are not limited to:",
        styles["Normal"],
    )
    flowables.append(paragraph)

    banned_devices_lst = ListFlowable(
        [
            Paragraph("Cell phones", styles["Normal"]),
            Paragraph("iPods or other MP3 players", styles["Normal"]),
            Paragraph("iPads, tablets, and other eReaders", styles["Normal"]),
            Paragraph(
                "Personal laptops, notebooks, or any other computing devices",
                styles["Normal"],
            ),
            Paragraph(
                "Wearable devices/smart wearables, including smart watches and health wearables with a display",
                styles["Normal"],
            ),
            Paragraph(
                "Headphones headsets, or in-ear headphones such as earbuds, and",
                styles["Normal"],
            ),
            Paragraph(
                "Any other device capable of recording audio, photogrphic, or video content, or capable of viewing or playing back such content, or sending/receiving text, audio, or video messages",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="-",
    )
    flowables.append(banned_devices_lst)

    paragraph = Paragraph(
        "If you bring any of these items to the building you must store them in your locker or turn it over to the proctor in the classroom. You may not keep your cell phone or any of these items with you, or near you, including in your pockets, backpack, desk, etc. If you keep a cell phone or any of these items with you, your examination will be invalidated, and you will get no score.",
        styles["Normal"],
    )
    flowables.append(paragraph)

    return flowables


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
                ("FONTSIZE", (0, 0), (-1, -1), 11),
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


def return_full_exam_title(ExamTitle):

    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trigonometry",
        "LE": "Living Environment",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics",
    }
    return exam_title_dict.get(ExamTitle)
