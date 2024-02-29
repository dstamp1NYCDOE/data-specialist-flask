import pandas as pd

from werkzeug.utils import secure_filename

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re


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
    
    if form.student_list_source.data == 'STARS_Classlist_Report':
        sort_by_df = sort_by_df.rename(columns={"PeriodId || '/'":'Period'})
        sort_by_df = sort_by_df.astype(str)
        group_by = ['TeacherName',"Period",'CourseCode','SectionId']
        sort_by_df['sort_by_col'] = sort_by_df['TeacherName'] + ' - P' + sort_by_df['Period'] + ' ' + sort_by_df['CourseCode']+'/'+sort_by_df['SectionId']
        
        student_sort_by_col = 'StudentName'



    sort_by_list = sort_by_df['sort_by_col'].to_list()

    sort_by_landscape_dict = generate_sortby_dict_landscape(sort_by_list)
    sort_by_potrait_dict = generate_sortby_dict_portrait(sort_by_list)


    pdfWriter = PyPDF2.PdfWriter()

    for sort_by, students_df in sort_by_df.groupby('sort_by_col'):

        students_df = students_df.sort_values(by=[student_sort_by_col])

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

        pdfWriter.add_blank_page()


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