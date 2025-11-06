from io import BytesIO
import pandas as pd
import datetime as dt
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

from .main import process_smartpass_data

def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.smartpass_file.name]
    date_of_interest = form.date_of_interest.data

    smartpass_df = pd.read_csv(filename)
    smartpass_df = process_smartpass_data(smartpass_df)
    


    f = BytesIO()



    # students_to_exclude = [221272438,233601582]
    # attd_by_student = attd_by_student[~attd_by_student['StudentID'].isin(students_to_exclude)]
    # total_cuts_by_student = pd.pivot_table(
    #     attd_by_student,
    #     index=["StudentID", "FirstName", "LastName"],
    #     values=True,
    #     aggfunc="sum",
    # )

    # attd_by_student = attd_by_student.merge(photos_df, on=["StudentID"], how="left")


    overtime_passes_df = smartpass_df[smartpass_df["OvertimeFlag"] == True]

    overtime_pivot = pd.pivot_table(
        overtime_passes_df,
        index=["StudentID", "Student Name", "class_period"],
        values=["Grade", "Origin"],
        aggfunc={
            "Grade": "count",
            "Origin": lambda x: x.mode()[0] if not x.mode().empty else None
        }
    )
    overtime_pivot.columns = ["#_overtime_passes", "Most_Common_Origin"]
    overtime_pivot = overtime_pivot.reset_index()

    overtime_pivot = overtime_pivot.merge(photos_df, on=["StudentID"], how="left")


    flowables = []
    for period, group_df in overtime_pivot.groupby('class_period'):
    # Get top 27 students by Pass_Count (or whatever your count column is named)
        top_27_df = group_df.nlargest(27, '#_overtime_passes')
        page_header = f"Top Overtime Passes by Period {period}"
        
        flowables.extend(return_photo_roster_pdf(page_header, top_27_df))


    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    today_str = dt.datetime.now().strftime("%Y_%m_%d")
    download_name = f"top_pass_overtime_by_period_{today_str}.pdf"
    return f, download_name


from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.enums import TA_JUSTIFY


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=8,
        leading=8,
    )
)


def return_photo_roster_pdf(page_header, students_df):
    flowables = []

    paragraph = Paragraph(
        f"{page_header}",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    temp_flowables = []
    if len(students_df) < (9 * 2):
        image_dim = 1.5
        nCols = 2
    elif len(students_df) <= (9 * 3):
        image_dim = 1.05
        nCols = 3
    else:
        image_dim = 0.75
        nCols = 4
    for index, student in students_df.iterrows():
        photo_path = student["photo_filename"]
        StudentName = student["Student Name"]
        Most_Common_Origin = student["Most_Common_Origin"]
        # Room = student["Room"]
        # Teacher = student["Teacher1"]


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
                            Paragraph(f"{StudentName}", styles["Normal_medium"]),
                            Paragraph(f"Room {Most_Common_Origin}", styles["Normal_medium"]),
                            
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
    flowables.append(PageBreak())
    return flowables
