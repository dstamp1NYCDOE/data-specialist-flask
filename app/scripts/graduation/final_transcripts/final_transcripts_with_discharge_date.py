import pandas as pd

from werkzeug.utils import secure_filename

import PyPDF2

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re


def main(form, request):

    PDF = request.files[form.transcript_file.name]


    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Times-Roman", 12)
    c.drawString(1*inch, 1*inch, '1 July 2024')
    c.save()

    pdfWatermarkReader = PyPDF2.PdfReader(buffer)
    pdfWaterMarkPage = pdfWatermarkReader.pages[0]
    print(pdfWaterMarkPage)


    pdfReader = PyPDF2.PdfReader(PDF)
    num_of_pages = pdfReader.pages

    
    pdfWriter = PyPDF2.PdfWriter()
    for page_num, page in enumerate(num_of_pages):
        pageObj = pdfReader.pages[page_num]
        pageObj.merge_page(pdfWaterMarkPage)
        pdfWriter.add_page(pageObj)   
        pdfWriter.add_page(pdfWaterMarkPage)     

    f = BytesIO()
    pdfWriter.write(f)
    f.seek(0)
    
    return f