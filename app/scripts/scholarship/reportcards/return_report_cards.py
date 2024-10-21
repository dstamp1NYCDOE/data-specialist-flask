from reportlab.graphics import shapes
from reportlab_qrcode import QRCodeImage

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

import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from io import BytesIO
import matplotlib

matplotlib.use("Agg")
import calmap


from datetime import timedelta
from reportlab.lib.units import mm, inch
from reportlab.platypus import Image

styles = getSampleStyleSheet()


import datetime as dt
import pandas as pd  #
import os

from io import BytesIO
from flask import session, current_app


import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.programming.jupiter.return_master_schedule import (
    return_jupiter_course,
    return_jupiter_schedule,
)


def main(form, request):
    students_df = (
        return_students_df().sort_values(by=["LastName", "FirstName"]).head(10)
    )
    dfs_dict = return_dfs_dict()
    f = generate_letters(students_df, dfs_dict)
    download_name = f"ReportCards.pdf"

    return f, download_name


def return_students_df():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    counselors_df = return_counselors_df()
    cr_3_07_df = cr_3_07_df.merge(counselors_df, on=["StudentID"], how="left")

    mp = "1"
    honor_roll_df = return_honor_roll_flag_df(mp)
    cr_3_07_df = cr_3_07_df.merge(honor_roll_df, on=["StudentID"], how="left").fillna(
        ""
    )
    return cr_3_07_df


from app.scripts.attendance.process_RATR import main as process_RATR

from app.scripts.privileges.attendance_benchmark.attendance_benchmark import (
    return_overall_attd_benchmark,
)


def return_dfs_dict():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    RATR_df = return_df_by_title("RATR", year_and_semester)
    dfs_dict = {
        "1_01": return_student_grades(),
        "1_40": return_df_by_title("1_40", year_and_semester),
        "assignments_df": return_df_by_title("assignments", year_and_semester),
        "jupiter_period_attendance_df": return_df_by_title(
            "jupiter_period_attendance", year_and_semester
        ),
        "jupiter_attd_summary_df": return_jupiter_attd_pvt(),
        "RATR_Summary_df": process_RATR(RATR_df),
        "jupiter_missing_assignment_pvt": return_jupiter_assignment_missing_pvt(),
        "RATR_df": RATR_df,
        "attd_benchmark_df": return_overall_attd_benchmark(),
    }
    return dfs_dict


def return_jupiter_assignment_missing_pvt():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    df = return_df_by_title("assignments", year_and_semester)

    df = df.drop_duplicates(subset=["StudentID", "Course", "Assignment", "DueDate"])
    missing_assignment_pvt = (
        pd.pivot_table(
            df,
            index=["StudentID", "Course", "Category"],
            columns="Missing",
            values="DueDate",
            aggfunc="count",
            margins=True,
        )
        .fillna(0)
        .reset_index()
    )
    return missing_assignment_pvt


def return_jupiter_attd_pvt():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    jupiter_period_attendance_df = return_df_by_title(
        "jupiter_period_attendance", year_and_semester
    )
    jupiter_period_attendance_df["ATTD"] = jupiter_period_attendance_df["Type"].apply(
        swap_attd_marks_on_jupiter
    )
    attd_pvt = pd.pivot_table(
        jupiter_period_attendance_df,
        index=["StudentID", "Course"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).reset_index()

    return attd_pvt


def swap_attd_marks_on_jupiter(attd_mark):
    attd_mark_dict = {
        "excused": "absent",
        "unexcused": "absent",
        "tardy": "late",
        "present": "present",
    }
    return attd_mark_dict.get(attd_mark)


def return_student_grades():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_01_df = return_df_by_title("1_01", year_and_semester)
    jupiter_master_schedule_df = return_jupiter_schedule()
    jupiter_master_schedule_df = jupiter_master_schedule_df[
        ["CourseCode", "SectionID", "JupiterCourse", "JupiterSection"]
    ]

    cr_1_01_df = cr_1_01_df.merge(
        jupiter_master_schedule_df,
        right_on=["CourseCode", "SectionID"],
        left_on=["Course", "Section"],
        how="left",
    )

    code_deck_df = return_df_by_title("CodeDeck", year_and_semester)

    code_deck_df = code_deck_df.rename(columns={"CourseCode": "Course"})

    cr_1_01_df = cr_1_01_df.merge(
        code_deck_df[["Course", "CourseName", "Credits"]],
        on="Course",
        how="left",
    )
    cr_1_01_df = cr_1_01_df[cr_1_01_df["Course"].str[0] != "Z"]
    cr_1_01_df = cr_1_01_df[cr_1_01_df["Course"].str[1] != "X"]
    cr_1_01_df = cr_1_01_df.drop_duplicates(subset=["StudentID", "Course"])
    return cr_1_01_df


def return_counselors_df():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    cr_1_49_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester=year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor"]]

    counselor_email_dict = {
        "CARTER ANIKA": 'Ms. Carter - Room 723 x7235 - <a href="acarter15@schools.nyc.gov">acarter15@schools.nyc.gov</a>',
        "DE LEON ANGELINA": 'Ms. De Leon - Room 504 x5047 - <a href="adeleon23@schools.nyc.gov">adeleon23@schools.nyc.gov</a>',
        "MARIN BETH": 'Ms. Marin - Room 423 x4236 - <a href="bmarin5@schools.nyc.gov">bmarin5@schools.nyc.gov</a>',
        "DUKE JOSHUA": 'Mr. Duke - Room 643 x6430 - <a href="jduke@schools.nyc.gov">jduke@schools.nyc.gov</a>',
        "JONES ALEX": "",
        "WEISS JESSICA": 'Ms. Weiss - Room 423 x4235 - <a href="jweiss4@schools.nyc.gov">jweiss4@schools.nyc.gov</a>',
        "SAN JORGE AMELIA": 'Ms. San Jorge - Room 329 x3291 - <a href="asanjorge@schools.nyc.gov">asanjorge@schools.nyc.gov</a>',
        "POWIS TAFARI": 'Mr. Powis - Room 504 x5049 - <a href="tpowis@schools.nyc.gov">tpowis@schools.nyc.gov</a>',
        "PADRON AMANDA": 'Ms. Padron - Room 723 x7233 - <a href="apadron@schools.nyc.gov">apadron@schools.nyc.gov</a>',
        "CASTELLANO ASHLEY": 'Ms. Castellano - Room 643 x6432 - <a href="acastellano7@schools.nyc.gov">acastellano7@schools.nyc.gov</a>',
    }
    cr_1_49_df["counselor_str"] = cr_1_49_df["Counselor"].apply(
        lambda x: counselor_email_dict.get(x)
    )
    return cr_1_49_df


def return_honor_roll_flag_df(mp):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_40_df = return_df_by_title("1_40", year_and_semester)
    cr_1_40_df["honor_roll_flag"] = cr_1_40_df.apply(determine_honor_roll_flag, axis=1)
    cr_1_40_df = cr_1_40_df.rename(columns={"Student": "StudentID"})

    return cr_1_40_df[["StudentID", "honor_roll_flag", "Average", "Minimum"]]


def determine_honor_roll_flag(student):
    gpa = student["Average"]
    min_grade = student["Minimum"]

    if min_grade < 65 and gpa < 85:
        return f"GPA {gpa} - Not on Honor Roll"
    if min_grade < 65 and gpa >= 85:
        return f"GPA {gpa} - Not on Honor Roll | failed a class"
    if gpa >= 90:
        return f"GPA {gpa} - Principal's Honor Roll (90+)"
    if gpa >= 85:
        return f"GPA {gpa} - Honor Roll (85-90)"

    return f"GPA {gpa} - Not on Honor Roll"


def return_df_by_title(title, year_and_semester):
    filename = utils.return_most_recent_report_by_semester(
        files_df, title, year_and_semester=year_and_semester
    )
    df = utils.return_file_as_df(filename)
    return df


def generate_letters(students_df, dfs_dict):
    students_df["flowables"] = students_df.apply(
        generate_letter_flowables, axis=1, args=(dfs_dict,)
    )
    flowables = students_df["flowables"].explode().to_list()

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=0.50 * inch,
        rightMargin=0.50 * inch,
        bottomMargin=0.5 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def generate_letter_flowables(student_row, dfs_dict):

    flowables = []
    chart_style = TableStyle(
        [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    )

    left_flowables = return_left_flowables(student_row, dfs_dict)
    right_flowables = return_student_class_flowables(student_row, dfs_dict)

    flowables.append(
        Table(
            [[left_flowables, right_flowables]],
            colWidths=[4 * inch, 6 * inch],
            rowHeights=[7 * inch],
            style=chart_style,
        )
    )
    flowables.append(PageBreak())

    return flowables


def return_student_class_flowables(student_row, dfs_dict):
    StudentID = student_row["StudentID"]
    class_flowables = []

    cr_1_01_df = dfs_dict["1_01"]

    student_classes_df = cr_1_01_df[cr_1_01_df["StudentID"] == StudentID]

    student_classes_df = student_classes_df.sort_values(by=["Period"])

    if len(student_classes_df) > 0:
        student_classes_df["flowables"] = student_classes_df.apply(
            return_class_flowables, axis=1, args=(dfs_dict,)
        )
        class_flowables = student_classes_df["flowables"].explode().to_list()

    return class_flowables


def return_class_flowables(student_row, dfs_dict):
    StudentID = student_row["StudentID"]

    course_code = student_row["Course"]
    course_name = student_row["CourseName"]
    period = student_row["Period"]
    teacher = student_row["Teacher1"]
    mark = student_row["Mark1"]

    JupiterCourseCode = student_row["JupiterCourse"]
    assignments_df = dfs_dict["assignments_df"]
    assignments_df = assignments_df[assignments_df["StudentID"] == StudentID]
    assignments_df = assignments_df[assignments_df["Course"] == JupiterCourseCode]

    jupiter_missing_assignment_pvt = dfs_dict["jupiter_missing_assignment_pvt"]
    jupiter_missing_assignment_pvt = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["StudentID"] == StudentID
    ]
    jupiter_missing_assignment_pvt = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["Course"] == JupiterCourseCode
    ]

    num_of_missing_practice = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["Category"] == "Practice"
    ]["Y"].max()
    total_practice = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["Category"] == "Practice"
    ]["All"].max()

    num_of_missing_performance = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["Category"] == "Performance"
    ]["Y"].max()
    total_performance = jupiter_missing_assignment_pvt[
        jupiter_missing_assignment_pvt["Category"] == "Performance"
    ]["All"].max()

    if num_of_missing_practice == 0:
        practice_str = f"Completed all {total_practice:.0f} practice assignments"
    else:
        practice_str = f"Missing {num_of_missing_practice:.0f} of {total_practice:.0f} practice assignments"

    if num_of_missing_performance == 0:
        performance_str = (
            f"Completed all {total_performance:.0f} performance assignments"
        )
    else:
        performance_str = f"Missing {num_of_missing_performance:.0f} of {total_performance:.0f} performance assignments"

    ## jupiter attendance
    jupiter_attd_summary_df = dfs_dict["jupiter_attd_summary_df"]
    jupiter_attd_summary_df = jupiter_attd_summary_df[
        jupiter_attd_summary_df["StudentID"] == StudentID
    ]
    jupiter_attd_summary_df = jupiter_attd_summary_df[
        jupiter_attd_summary_df["Course"] == JupiterCourseCode
    ]
    if len(jupiter_attd_summary_df) > 0:
        I = return_jupiter_attd_summary_graph(jupiter_attd_summary_df)
    else:
        I = ""

    table_data = [
        [f"P{period}", course_name, I],
        [mark, teacher, ""],
        ["", practice_str, performance_str],
    ]
    colWidths = [0.5 * inch, 2.5 * inch, 2.5 * inch]
    rowHeights = [0.3 * inch, 0.3 * inch, 0.3 * inch]
    # rowHeights = None
    t = Table(table_data, colWidths=colWidths, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                # ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 2, colors.black),
                ("SPAN", (2, 0), (2, 1)),
            ]
        )
    )
    return t


def return_left_flowables(student_row, dfs_dict):
    flowables = []
    LastName = student_row["LastName"]
    FirstName = student_row["FirstName"]
    StudentID = student_row["StudentID"]

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    paragraph = Paragraph(
        f"{year_and_semester} Report Card",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{LastName}, {FirstName} ({StudentID})",
        styles["Heading2"],
    )
    flowables.append(paragraph)

    counselor_str = student_row["counselor_str"]
    paragraph = Paragraph(
        f"{counselor_str}",
        styles["Normal"],
    )
    flowables.append(paragraph)

    honor_roll_flag = student_row["honor_roll_flag"]
    paragraph = Paragraph(
        f"{honor_roll_flag}",
        styles["Normal"],
    )
    flowables.append(paragraph)

    student_RATR_df = dfs_dict["RATR_df"]
    student_RATR_df = student_RATR_df[student_RATR_df["StudentID"] == StudentID]

    RATR_Summary_df = dfs_dict["RATR_Summary_df"]
    student_RATR_summary_df = RATR_Summary_df[RATR_Summary_df["StudentID"] == StudentID]

    if len(student_RATR_summary_df) > 0:
        I = return_daily_attd_summary_graph(student_RATR_summary_df)
        flowables.append(I)

    paragraphs = return_attendance_sentence_paragraphs(student_RATR_df)
    flowables.extend(paragraphs)

    attd_benchmark_df = dfs_dict["attd_benchmark_df"]
    attd_benchmark_df = attd_benchmark_df[attd_benchmark_df["StudentID"] == StudentID]
    attd_benchmark = attd_benchmark_df["overall_meet_attd_standard"].any()

    out_to_lunch_paragraph = return_out_to_lunch_paragraph(
        attd_benchmark, student_row["Minimum"]
    )
    flowables.append(out_to_lunch_paragraph)

    return flowables


def return_out_to_lunch_paragraph(attd_benchmark, minimum_grade):
    try:
        if int(minimum_grade) >= 65:
            passed_all_classes = True
        else:
            passed_all_classes = False
    except:
        passed_all_classes = False

    if attd_benchmark and passed_all_classes:
        out_to_lunch_str = "You have met the out to lunch criteria of (1) passing all classes and (2) present 90% and on time 80% to all of your classes!"
    elif passed_all_classes:
        out_to_lunch_str = "You have met the out to lunch criteria of (1) passing all classes but not (2) present 90% and on time 80% to all of your classes. Work on improving your attendance next marking period."
    elif attd_benchmark:
        out_to_lunch_str = "You have not met the out to lunch criteria of (1) passing all classes but you have (2) present 90% and on time 80% to all of your classes. Work on passing all of your classes next marking period."
    else:
        out_to_lunch_str = "You have not met the out to lunch criteria of (1) passing all classes or (2) present 90% and on time 80% to all of your classes. Work on improving your period attendance and passing all of your classes next marking period."

    paragraph = Paragraph(
        f"{out_to_lunch_str}",
        styles["Normal"],
    )
    return paragraph


def return_attendance_sentence_paragraphs(student_RATR_df):
    days_absent = student_RATR_df[student_RATR_df["ATTD"] == "A"]["Date"].to_list()
    num_of_days_absent = len(days_absent)
    days_absent_lst_str = ", ".join([x.strftime("%-m/%-d") for x in days_absent])
    paragraphs = []
    if num_of_days_absent == 0:
        paragraph = Paragraph(
            f"You've been absent zero days so far this school year. Keep it up!",
            styles["Normal"],
        )
        paragraphs.append(paragraph)
    else:
        paragraph = Paragraph(
            f"You've been absent {num_of_days_absent} days so far this school year: {days_absent_lst_str}",
            styles["Normal"],
        )
        paragraphs.append(paragraph)

    days_late = student_RATR_df[student_RATR_df["ATTD"] == "L"]["Date"].to_list()
    num_of_days_late = len(days_late)
    days_late_lst_str = ", ".join([x.strftime("%-m/%-d") for x in days_late])
    if num_of_days_late == 0:
        paragraph = Paragraph(
            f"You've been late zero days so far this school year. Keep it up!",
            styles["Normal"],
        )
        paragraphs.append(paragraph)
    else:
        paragraph = Paragraph(
            f"You've been late {num_of_days_late} days so far this school year: {days_late_lst_str}",
            styles["Normal"],
        )
        paragraphs.append(paragraph)
    return paragraphs


def return_daily_attd_summary_graph(RATR_Summary_df):
    y_aspect = 200
    x_aspect = 600
    scale = 0.75

    attd_marks = ["Present", "Late", "Absent"]
    labels_dict = {"P": "Days Present", "L": "Days Late", "A": "Days Absent"}
    fig = px.bar(
        RATR_Summary_df,
        y=RATR_Summary_df.index,
        x=["P", "L", "A"],
        labels=labels_dict,
        title="Overall Daily Attendance<br><sup>Based on p3 attendance</sup>",
        text_auto="%{x:$.0f Days",
        # pattern_shape_sequence=[".", "x", "+"],
        orientation="h",
        # color="ATTD",
        color_discrete_sequence=["grey", "white", "black"],
        barmode="stack",
    )

    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=50, b=0),
        height=scale * y_aspect,
        width=scale * x_aspect,
        # xaxis_tickmode="array",
        yaxis_visible=False,
        yaxis_showticklabels=False,
        xaxis_visible=False,
        xaxis_showticklabels=False,
        title=dict(
            x=0.5,  # Center the title horizontally (0 is left, 1 is right)
            y=0.7,  # Adjust vertical position (0 is bottom, 1 is top)
            xanchor="center",  # Anchor horizontally to the center
            # yanchor="top",  # Anchor vertically to the top
            font=dict(size=20),  # Adjust the font size
        ),
        legend_title_text="# of Days",
        legend=dict(
            orientation="h",  # Make the legend horizontal
            y=0.2,  # Adjust the vertical position to place it below the chart
            xanchor="center",  # Center the legend horizontally
            x=0.5,  # Center the legend horizontally
        ),
    )
    fig.update_traces(
        textfont_size=28,
        textangle=0,
        textposition="auto",
        cliponaxis=False,
        marker_line_width=2,
        marker_line_color="black",
        width=0.55,
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)

    I = Image(buffer)
    width = 4 * inch
    I.drawHeight = y_aspect / x_aspect * width
    I.drawWidth = x_aspect / x_aspect * width

    return I


def return_jupiter_attd_summary_graph(df):
    y_aspect = 200
    x_aspect = 600
    scale = 0.75

    fig = px.bar(
        df,
        y=df.index,
        x=["present", "late", "absent"],
        title="<br>Period Attendance",
        text_auto=True,
        # pattern_shape_sequence=[".", "x", "+"],
        orientation="h",
        # color="ATTD",
        color_discrete_sequence=["grey", "white", "black"],
        barmode="stack",
    )

    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=25, b=0),
        height=scale * y_aspect,
        width=scale * x_aspect,
        # xaxis_tickmode="array",
        yaxis_visible=False,
        yaxis_showticklabels=False,
        xaxis_visible=False,
        xaxis_showticklabels=False,
        legend_title_text="# of Periods",
    )
    fig.update_traces(
        textfont_size=24,
        textangle=0,
        textposition="auto",
        cliponaxis=False,
        marker_line_width=2,
        marker_line_color="black",
        width=0.5,
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)

    I = Image(buffer)
    width = 2 * inch
    I.drawHeight = y_aspect / x_aspect * width
    I.drawWidth = x_aspect / x_aspect * width

    return I
