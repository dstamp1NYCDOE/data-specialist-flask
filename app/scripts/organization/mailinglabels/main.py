from app.scripts import scripts, files_df

from flask import session

from io import BytesIO
from reportlab.graphics import shapes

from reportlab.lib.pagesizes import letter, landscape

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate
from werkzeug.utils import secure_filename
import app.scripts.utils.utils as utils
import labels

import pandas as pd
import PyPDF2
import re

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


def draw_label(label, width, height, obj):
    if obj.get("Teacher"):
        teacher_name = f"{obj['Teacher']}"
        label.add(
            shapes.String(
                5,
                40,
                teacher_name,
                fontName="Helvetica",
                fontSize=24,
            )
        )

    elif obj.get("LastName"):
        student_name = f"Parent of: {obj['LastName']}, {obj['FirstName']}"

        label.add(
            shapes.String(
                5,
                50,
                student_name,
                fontName="Helvetica",
                fontSize=10,
            )
        )

        AptNum = obj["AptNum"]
        street = obj["Street"]
        city = obj["City"]
        state = obj["State"]
        zipcode = obj["Zip"]

        if AptNum != "":
            street_address = f"{street}, {AptNum}"
        else:
            street_address = f"{street}"

        label.add(
            shapes.String(
                5,
                30,
                street_address,
                fontName="Helvetica",
                fontSize=10,
            )
        )

        label.add(
            shapes.String(
                5,
                15,
                f"{city}, {state} {zipcode}",
                fontName="Helvetica",
                fontSize=10,
            )
        )

    else:
        pass


def by_list_of_students(form, request):

    student_lst_str = form.subset_lst.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]

    

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    student_info_df = utils.return_file_as_df(filename).fillna("")
    
    student_info_df["Zip"] = student_info_df["Zip"].apply(lambda x: str(x).zfill(5)[0:5])

    student_info_df = student_info_df.set_index('StudentID')
    student_info_df = student_info_df.reindex(student_lst)
    

    labels_to_make = student_info_df.to_dict('records')

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    f = BytesIO()
    sheet.save(f)
    f.seek(0)
    return f


def main(form, request):

    PDF = request.files[form.student_records_pdf.name]
    

    StudentID_Regex = r"\d{9}"
    StudentIDRegex = re.compile(StudentID_Regex)

    pdfReader = PyPDF2.PdfReader(PDF)
    num_of_pages = pdfReader.pages

    StudentID_dict = {}
    StudentID_lst = []

    for page_num, page in enumerate(num_of_pages):
        try:
            page_text = page.extract_text()
        except AttributeError:
            continue
        page_text = page_text.replace(" ", "")

        mo = StudentIDRegex.search(page_text)

        if mo:
            StudentID = mo.group()
            

            if StudentID_dict.get(StudentID):
                StudentID_dict[StudentID].append(page_num)
            else:
                
                StudentID_dict[StudentID] = [page_num]
                StudentID = int(StudentID)
                StudentID_lst.append(StudentID)

    

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    student_info_df = utils.return_file_as_df(filename).fillna("")
    
    student_info_df["Zip"] = student_info_df["Zip"].apply(lambda x: str(x).zfill(5)[0:5])

    student_info_df = student_info_df.set_index('StudentID')
    student_info_df = student_info_df.reindex(StudentID_lst)
    

    labels_to_make = student_info_df.to_dict('records')

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    f = BytesIO()
    sheet.save(f)
    f.seek(0)

    
    return f



def by_student_class_list(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    student_info_df = utils.return_file_as_df(filename).fillna("")
    
    student_info_df["Zip"] = student_info_df["Zip"].apply(lambda x: str(x).zfill(5)[0:5])

    labels_to_make = student_info_df.to_dict('records')

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    f = BytesIO()
    sheet.save(f)
    f.seek(0)

    
    return f