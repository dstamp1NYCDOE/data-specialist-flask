from io import BytesIO
import pandas as pd
import datetime as dt
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df


def main():
    f = BytesIO()

    attd_by_student = process_jupiter_attendance()

    students_to_exclude = [221272438,233601582]
    attd_by_student = attd_by_student[~attd_by_student['StudentID'].isin(students_to_exclude)]
    total_cuts_by_student = pd.pivot_table(
        attd_by_student,
        index=["StudentID", "FirstName", "LastName"],
        values=True,
        aggfunc="sum",
    )

    attd_by_student = attd_by_student.merge(photos_df, on=["StudentID"], how="left")
    flowables = []
    for period in [2, 3, 4, 5, 6, 7, 8, 9]:
        page_header = f"Top Cuts by Period {period}"
        
        top_27_df = (
            attd_by_student[attd_by_student["Pd"] == period]
            .sort_values(by=[True], ascending=[False])
            .drop_duplicates(subset=["StudentID"])
            .head(27)
        )
        
        flowables.extend(return_photo_roster_pdf(page_header, top_27_df))

    total_cuts_by_student = total_cuts_by_student.reset_index()
    total_cuts_by_student = total_cuts_by_student.merge(
        photos_df, on=["StudentID"], how="left"
    )
    page_header = f"Top Cuts Overall"
    top_27_cuts = (
        total_cuts_by_student.sort_values(by=[True], ascending=[False])
        .drop_duplicates(subset=["StudentID"])
        .head(27)
    )
    top_27_cuts["Teacher1"] = top_27_cuts[True]
    top_27_cuts["Room"] = ""
    flowables.extend(return_photo_roster_pdf(page_header, top_27_cuts))

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
    download_name = f"top_cuts_by_period_{today_str}.pdf"
    return f, download_name


def process_jupiter_attendance():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]
    shared_instruction_students = cr_3_07_df[cr_3_07_df["GradeLevel"] == "ST"][
        "StudentID"
    ]

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## only keep students still on register
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"].isin(students_df["StudentID"])
    ]

    ## drop shared instruction students
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["StudentID"].isin(shared_instruction_students)
    ]

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attd_by_student_by_day = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="count",
    ).fillna(0)

    attd_by_student_by_day["in_school?"] = (
        attd_by_student_by_day["present"] + attd_by_student_by_day["tardy"]
    ) >= 2
    attd_by_student_by_day = attd_by_student_by_day.reset_index()[
        ["StudentID", "Date", "in_school?"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        attd_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    first_period_present_by_student_by_day = pd.pivot_table(
        attendance_marks_df[attendance_marks_df["in_school?"]],
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="min",
    ).reset_index()

    first_period_present_by_student_by_day["first_period_present"] = (
        first_period_present_by_student_by_day[["present", "tardy"]].min(axis=1)
    )

    first_period_present_by_student_by_day = first_period_present_by_student_by_day[
        ["StudentID", "Date", "first_period_present"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        first_period_present_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    attendance_marks_df["potential_cut"] = attendance_marks_df.apply(
        determine_potential_cut, axis=1
    )

    ### pull in class info
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[rosters_df["Course"].str[0] != "Z"]
    rosters_df = rosters_df[["StudentID", "Period", "Teacher1", "Room"]]

    ## pivot table on number of cuts by period

    attd_by_student = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Pd"],
        columns="potential_cut",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    attd_by_student["total"] = attd_by_student.sum(axis=1)

    attd_by_student["%_cut"] = attd_by_student[True] / (attd_by_student["total"])
    attd_by_student = attd_by_student.fillna(0)

    attd_by_student = attd_by_student.reset_index()
    attd_by_student = attd_by_student.merge(students_df, on=["StudentID"], how="left")
    attd_by_student = attd_by_student.merge(
        rosters_df,
        left_on=["StudentID", "Pd"],
        right_on=["StudentID", "Period"],
        how="left",
    )
    attd_by_student = attd_by_student.dropna()
    
    return attd_by_student



def determine_potential_cut(student_row):
    is_in_school = student_row["in_school?"]

    if is_in_school == False:
        return False

    attendance_type = student_row["Type"]
    period = student_row["Pd"]
    first_period_present = student_row["first_period_present"]
    if attendance_type == "unexcused" and period >= first_period_present:
        return True

    return False


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
