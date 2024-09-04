import pandas as pd

from werkzeug.utils import secure_filename

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re

from app.scripts import scripts, files_df, photos_df


def main(form, request):

    PDF = request.files[form.student_records_pdf.name]
    orientation_flag = form.student_records_pdf_orientation.data

    StudentID_Regex = r"\d{9}"
    StudentIDRegex = re.compile(StudentID_Regex)

    pdfReader = PyPDF2.PdfReader(PDF)
    num_of_pages = pdfReader.pages

    StudentID_dict = {}

    for page_num, page in enumerate(num_of_pages):
        page_text = page.extract_text()
        page_text = page_text.replace(" ", "")

        mo = StudentIDRegex.search(page_text)

        if mo:
            StudentID = mo.group()
            # StudentID = int(StudentID)

            if StudentID_dict.get(StudentID):
                StudentID_dict[StudentID].append(page_num)
            else:
                StudentID_dict[StudentID] = [page_num]

    filename = form.student_list.data

    sort_by_data = request.files[form.student_list.name]

    sort_by_df = pd.read_excel(sort_by_data)

    sort_by_df["___________"] = ""

    if form.student_list_source.data == "STARS_Classlist_Report":
        sort_by_df = sort_by_df.rename(columns={"PeriodId || '/'": "Period"})
        sort_by_df = sort_by_df.astype(str)
        sort_by_df = sort_by_df.merge(photos_df, on=["Student Id"])
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

        student_sort_by_cols = ["StudentName"]
        student_roster_table_cols = ["StudentName", "___________"]

    if form.student_list_source.data == "teacher_and_room_list":
        sort_by_df = sort_by_df.merge(photos_df, on=["StudentID"])

        sort_by_df = sort_by_df.astype(str)
        group_by = ["TeacherName", "Room"]
        sort_by_df["sort_by_col"] = (
            sort_by_df["TeacherName"] + " - Room" + sort_by_df["Room"]
        )

        student_sort_by_cols = ["LastName", "FirstName"]
        student_roster_table_cols = ["LastName", "FirstName", "___________"]

    sort_by_list = sort_by_df["sort_by_col"].to_list()

    sort_by_landscape_dict = generate_sortby_dict_landscape(sort_by_list)
    sort_by_potrait_dict = generate_sortby_dict_portrait(sort_by_list)

    pdfWriter = PyPDF2.PdfWriter()

    include_classlist_flag = form.include_classlist_boolean.data

    for sort_by, students_df in sort_by_df.groupby("sort_by_col"):

        students_df = students_df.sort_values(by=student_sort_by_cols)

        if include_classlist_flag:
            roster_pdf = return_class_list_roster_pdf(
                sort_by, students_df, student_roster_table_cols
            )
            pdfWriter.add_page(roster_pdf)

            photo_roster_pdf = return_photo_roster_pdf(
                sort_by, students_df, student_roster_table_cols
            )
            pdfWriter.add_page(photo_roster_pdf)

        for StudentID in students_df["StudentID"]:
            page_nums = StudentID_dict.get(StudentID)
            if page_nums:
                for pageNum in page_nums:
                    pageObj = pdfReader.pages[pageNum]
                    if orientation_flag == "portrait":
                        pdfWaterMarkPage = sort_by_potrait_dict.get(sort_by)
                        pageObj.merge_page(pdfWaterMarkPage)
                    if orientation_flag == "landscape":
                        pdfWaterMarkPage = sort_by_landscape_dict.get(sort_by)
                        pageObj.merge_page(pdfWaterMarkPage)
                    pdfWriter.add_page(pageObj)

        # pdfWriter.add_blank_page()

    f = BytesIO()
    pdfWriter.write(f)
    f.seek(0)

    return f


def generate_sortby_dict_landscape(sort_by_list):
    pdf_dict = {}
    for sort_by in sort_by_list:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        c.setFont("Times-Roman", 12)
        c.drawString(8 * inch, 0.5 * inch, sort_by)
        c.save()

        pdfWatermarkReader = PyPDF2.PdfReader(buffer)
        pdfWaterMarkPage = pdfWatermarkReader.pages[0]

        pdf_dict[sort_by] = pdfWaterMarkPage
    return pdf_dict


def generate_sortby_dict_portrait(sort_by_list):
    pdf_dict = {}
    for sort_by in sort_by_list:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Times-Roman", 12)
        c.drawString(1 * inch, 1 * inch, sort_by)
        c.save()

        pdfWatermarkReader = PyPDF2.PdfReader(buffer)
        pdfWaterMarkPage = pdfWatermarkReader.pages[0]

        pdf_dict[sort_by] = pdfWaterMarkPage
    return pdf_dict


from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.enums import TA_JUSTIFY


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=9,
        leading=9,
    )
)


def return_class_list_roster_pdf(sort_by, students_df, student_roster_table_cols):
    flowables = []

    paragraph = Paragraph(
        f"{sort_by}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    T = return_df_as_table(students_df, cols=student_roster_table_cols)

    flowables.append(T)

    f = BytesIO()

    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.50 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    pdfReader = PyPDF2.PdfReader(f)
    pdfPage = pdfReader.pages[0]
    return pdfPage


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


from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Image


def return_photo_roster_pdf(sort_by, students_df, student_roster_table_cols):
    flowables = []

    paragraph = Paragraph(
        f"{sort_by}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    temp_flowables = []
    if len(students_df) <= (9 * 2):
        image_dim = 1.5
        nCols = 2
    elif len(students_df) <= (9 * 3):
        image_dim = 1
        nCols = 3
    else:
        image_dim = 0.75
        nCols = 4
    for index, student in students_df.iterrows():
        photo_path = student["photo_filename"]
        FirstName = student["FirstName"]
        LastName = student["LastName"]

        try:
            I = Image(photo_path)
            I.drawHeight = image_dim * inch
            I.drawWidth = image_dim * inch
            I.hAlign = "CENTER"

        except:
            I = ""

        chart_style = TableStyle(
            [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
        )
        temp_flowables.append(
            Table(
                [
                    [
                        I,
                        [
                            Paragraph(f"{FirstName}", styles["Normal_medium"]),
                            Paragraph(f"{LastName}", styles["Normal_medium"]),
                        ],
                    ]
                ],
                colWidths=[image_dim * inch, image_dim * inch],
                rowHeights=[image_dim * inch],
                style=chart_style,
            )
        )

    B = BalancedColumns(
        temp_flowables,  # the flowables we are balancing
        nCols=nCols,  # the number of columns
        # needed=72,  # the minimum space needed by the flowable
    )
    flowables.append(B)

    f = BytesIO()

    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    pdfReader = PyPDF2.PdfReader(f)
    pdfPage = pdfReader.pages[0]
    return pdfPage
