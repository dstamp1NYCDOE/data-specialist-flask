from io import BytesIO
import pandas as pd 
import datetime as dt
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

def main():
    f = BytesIO()

    attd_by_student = process_jupiter_attendance()
    attd_by_student = attd_by_student.merge(photos_df, on=['StudentID'], how='left')
    flowables = []
    for period in [1,2,3,4,5,6,7,8,9]:
        page_header = f"Top Lates by Period {period}"
        top_30_lates = attd_by_student[attd_by_student['Pd']==period].sort_values(by=['tardy']).drop_duplicates(subset=['StudentID']).tail(27)
        flowables.extend(return_photo_roster_pdf(page_header, top_30_lates))

    attd_by_student = return_top_lates_overall()
    attd_by_student = attd_by_student.merge(photos_df, on=['StudentID'], how='left')
    page_header = f"Top Lates Overall"
    top_30_lates = attd_by_student.sort_values(by=['%_late']).drop_duplicates(subset=['StudentID']).tail(27)
    flowables.extend(return_photo_roster_pdf(page_header, top_30_lates))    

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
    today_str = dt.datetime.now().strftime('%Y_%m_%d')
    download_name = f'top_lates_by_period_{today_str}.pdf'
    return f, download_name

def return_top_lates_overall():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    ## pivot table on number of lates by period

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student['total'] = attd_by_student.sum(axis=1)

    attd_by_student["%_late"] = attd_by_student["tardy"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student["%_absent"] = attd_by_student["unexcused"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student = attd_by_student.fillna(0)

    attd_by_student["late_freq"] = attd_by_student["%_late"].apply(utils.convert_percentage_to_ratio)

    attd_by_student = attd_by_student.reset_index()
    attd_by_student = attd_by_student.merge(students_df, on=['StudentID'], how='left')
    attd_by_student['Room'] = ''
    attd_by_student['Teacher1'] = ''
    
    return attd_by_student


def process_jupiter_attendance():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    ### pull in class info
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[rosters_df['Course'].str[0]!='Z']
    rosters_df = rosters_df[['StudentID','Period','Teacher1','Room']]
    

    ## pivot table on number of lates by period

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID","Pd"],
        columns="Type",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student['total'] = attd_by_student.sum(axis=1)

    attd_by_student["%_late"] = attd_by_student["tardy"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student["%_absent"] = attd_by_student["unexcused"] / (
        attd_by_student["total"] - attd_by_student["excused"]
    )
    attd_by_student = attd_by_student.fillna(0)

    attd_by_student["late_freq"] = attd_by_student["%_late"].apply(utils.convert_percentage_to_ratio)

    attd_by_student = attd_by_student.reset_index()
    attd_by_student = attd_by_student.merge(students_df, on=['StudentID'], how='left')
    attd_by_student = attd_by_student.merge(rosters_df, left_on=['StudentID','Pd'], right_on=['StudentID','Period'], how='left')
    attd_by_student = attd_by_student.dropna()
    
    return attd_by_student



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
        FirstName = student["FirstName"]
        LastName = student["LastName"]
        Room = student["Room"]
        Teacher = student["Teacher1"]


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
                            Paragraph(f"Room {Room}", styles["Normal_medium"]),
                            Paragraph(f"{Teacher}", styles["Normal_medium"]),
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