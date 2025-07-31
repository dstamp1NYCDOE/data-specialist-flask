import pandas as pd
import app.scripts.utils as utils

import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

from io import BytesIO
import re
from reportlab.graphics.barcode.qr import QrCodeWidget


def main(data):
    year = data["year"]
    sort_by_df = utils.process_sort_by_df(data)
    source = data["source"]
    date = data["date"]

    # Generate Info From Student Schedules
    cr_1_49 = f"{year}/1_49.xlsx"
    student_counselors_df = pd.read_excel(cr_1_49)

    # Generate Info From Student Schedules
    cr_1_01 = f"{year}/1_01.xlsx"
    student_programs_df = pd.read_excel(cr_1_01)

    student_lunch_dict = (
        student_programs_df[student_programs_df["Course"] == "ZL"]
        .set_index("StudentID")[["Period"]]
        .to_dict("index")
    )

    sel_yl_list = list(
        student_programs_df[student_programs_df["Course"] == "ZLYL"]["StudentID"]
    )

    ZLTAs = list(
        student_programs_df[student_programs_df["Course"] == "ZA"]["StudentID"].unique()
    )

    student_session_dict = utils.process_student_session_dict(student_programs_df)

    # Generate Info From Student Schedules
    barcodes_df = f"{year}/barcodes.csv"
    barcodes_df = pd.read_csv(barcodes_df)

    StudentID_Regex = data["StudentID_Regex"]
    StudentIDRegex = re.compile(StudentID_Regex)

    PDF = f"{year}/PDFs/Inputs/Programs.pdf"
    pdfFileObj = open(PDF, "rb")
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
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

    sort_by_col = data["sort_by_col"]
    student_sort_by_col = data["student_sort_by_col"]

    sort_by_list = sort_by_df[sort_by_col].to_list()

    sort_by_landscape_dict = utils.generate_sortby_dict_landscape(sort_by_list)
    sort_by_potrait_dict = utils.generate_sortby_dict_portrait(sort_by_list)

    counselors_lst = student_counselors_df["Counselor"].unique().tolist()
    counselors_pdf_dict = utils.generate_counselors_df_dict(counselors_lst)
    lunch_period_pdf_dict = utils.generate_lunch_period_overlay_dict()
    session_pdf_dict = utils.generate_session_overlay_dict(student_session_dict)
    student_qr_codes_dict = utils.generate_student_qr_codes(barcodes_df)

    pdfWriter = PyPDF2.PdfWriter()

    sort_by_df = sort_by_df.merge(
        student_counselors_df[["StudentID", "Counselor"]],
        on="StudentID",
        how="left",
    ).fillna("")

    for sort_by, students_df in sort_by_df.groupby(sort_by_col):
        pdfWaterMarkPage = sort_by_landscape_dict.get(sort_by)
        pdfWriter.add_page(pdfWaterMarkPage)

        students_df = students_df.sort_values(by=[student_sort_by_col])

        for index, student in students_df.iterrows():
            StudentID = student["StudentID"]
            counselor = student["Counselor"]

            page_nums = StudentID_dict.get(StudentID)

            StudentLunchPeriod = student_lunch_dict.get(StudentID)
            Student_Session = student_session_dict.get(StudentID)
            Student_QR_code = student_qr_codes_dict.get(StudentID)

            if page_nums:
                for pageNum in page_nums:
                    pageObj = pdfReader.pages[pageNum]

                    pdfWaterMarkPage = sort_by_landscape_dict.get(sort_by)
                    pageObj.merge_page(pdfWaterMarkPage, expand=True)

                    pdfWaterMarkPage = counselors_pdf_dict.get(counselor)

                    if pdfWaterMarkPage:
                        pageObj.merge_page(pdfWaterMarkPage, expand=True)
                        # Merge Lunch Period
                    if StudentID in sel_yl_list:
                        pdfWaterMarkPage = lunch_period_pdf_dict["ZLYL"]
                        pageObj.merge_page(pdfWaterMarkPage, expand=True)
                    elif StudentLunchPeriod:
                        pdfWaterMarkPage = lunch_period_pdf_dict[
                            StudentLunchPeriod["Period"]
                        ]
                        pageObj.merge_page(pdfWaterMarkPage, expand=True)
                    # Merge Session Period
                    if Student_Session:
                        pdfWaterMarkPage = session_pdf_dict[Student_Session]
                        pageObj.merge_page(pdfWaterMarkPage, expand=True)
                    # Merge Session Period
                    if Student_QR_code:
                        pdfWaterMarkPage = Student_QR_code
                        pageObj.merge_page(pdfWaterMarkPage, expand=True)

                    pdfWriter.add_page(pageObj)

    pdfOutputFilename = PDF.replace("Inputs", "Outputs")
    pdfOutputFilename = pdfOutputFilename.replace(".pdf", f"_by_{source}_{date}.pdf")

    pdfOutputFile = open(pdfOutputFilename, "wb")
    pdfWriter.write(pdfOutputFile)
    pdfOutputFile.close()

    return True


if __name__ == "__main__":
    data = {
        "year": 2023,
        "term": "Fall",
        "source": "ROCL",
        "skip_rows": 3,
        "sort_by_col": "Teacher",
        "sort_by_transform_function": utils.convert_teacher_name,
        "student_sort_by_col": "Name",
        "StudentID_Regex": "\d{9}",
        "date": "2024_01_25",
    }
    main(data)
    # data = {
    #     'year': 2023,
    #     'term': 'Fall',
    #     'source': 'ClassList-P3',
    #     'skip_rows': 0,
    #     'sort_by_col': 'TeacherName',
    #     'sort_by_transform_function': utils.bypass_convert_teacher_name,
    #     'student_sort_by_col': 'StudentName',
    #     'StudentID_Regex': "\d{9}",
    #     'date': '2023_09_15',
    # }
    # main(data)
