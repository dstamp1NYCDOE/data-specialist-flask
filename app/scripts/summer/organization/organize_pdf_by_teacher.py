
from app.scripts import scripts, files_df, photos_df, gsheets_df
from dotenv import load_dotenv
from flask import current_app, session
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle, SimpleDocTemplate

from werkzeug.utils import secure_filename
from zipfile import ZipFile


import app.scripts.utils as utils
import datetime as dt
import numpy as np
import os

import pandas as pd
import pygsheets
import PyPDF2
import re

gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")
load_dotenv()


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

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
            StudentID = int(StudentID)

            if StudentID_dict.get(StudentID):
                StudentID_dict[StudentID].append(page_num)
            else:
                StudentID_dict[StudentID] = [page_num]

    
    summer_school_gradebooks_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_gradebooks_hub", year_and_semester
    )

    gradebook_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url, sheet="AllStudentsBySchool"
    )
    gradebook_df = gradebook_df.dropna(subset="FinalMark")
    gradebook_df = gradebook_df.dropna(subset="StudentID")

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    gradebook_df = gradebook_df.merge(dbn_df, on="school_name", how="left").fillna(
        "NoSendingSchool"
    )
    
    gradebook_df = gradebook_df.sort_values(by=["Period"], ascending=True)


    gradebook_df["sort_by_col"] = gradebook_df.apply(
        distribute_by_this_period, args=(gradebook_df,), axis=1
    )
    sort_by_df = gradebook_df[gradebook_df["sort_by_col"]]
    sort_by_df['sort_by_col'] = sort_by_df['Teacher1'] + ' - Period' + sort_by_df['Period'].astype(str)
    sort_by_list = sort_by_df['sort_by_col'].unique().tolist()
    

    sort_by_landscape_dict = generate_sortby_dict_landscape(sort_by_list)
    sort_by_potrait_dict = generate_sortby_dict_portrait(sort_by_list)


    pdfWriter = PyPDF2.PdfWriter()

    for sort_by, students_df in sort_by_df.groupby('sort_by_col'):

        students_df = students_df.sort_values(by=['LastName'])

        for StudentID in students_df["StudentID"]:
            page_nums = StudentID_dict.get(StudentID)
            
            if page_nums:
                for pageNum in page_nums:
                    pageObj = pdfReader.pages[pageNum]
                    if orientation_flag == 'portrait':
                        pdfWaterMarkPage = sort_by_potrait_dict.get(sort_by)
                        pageObj.merge_page(pdfWaterMarkPage)
                    if orientation_flag == 'landscape':
                        pdfWaterMarkPage = sort_by_landscape_dict.get(sort_by)
                        pageObj.merge_page(pdfWaterMarkPage)
                    pdfWriter.add_page(pageObj)

        # pdfWriter.add_blank_page()


    f = BytesIO()
    pdfWriter.write(f)
    f.seek(0)
    
    return f

def distribute_by_this_period(student_row, cr_1_01_df):
    StudentID = student_row["StudentID"]
    Period = student_row["Period"]
    student_courses_df = cr_1_01_df[cr_1_01_df["StudentID"] == StudentID]
    non_pe_classes_df = student_courses_df[
        student_courses_df["Course"].str[0:2] != "PP"
    ]
    if len(non_pe_classes_df) == 0:
        return True
    else:
        last_period = non_pe_classes_df["Period"].max()
        return Period == last_period


def generate_sortby_dict_landscape(sort_by_list):
    pdf_dict = {}
    for sort_by in sort_by_list:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        c.setFont("Times-Roman", 12)
        c.drawString(8*inch, 0.5*inch, sort_by)
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
        c.drawString(1*inch, 1*inch, sort_by)
        c.save()

        pdfWatermarkReader = PyPDF2.PdfReader(buffer)
        pdfWaterMarkPage = pdfWatermarkReader.pages[0]

        pdf_dict[sort_by] = pdfWaterMarkPage
    return pdf_dict