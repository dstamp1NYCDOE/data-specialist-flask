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
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from io import BytesIO


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

## files needed
# 1_01
# 1_32 save as .xlsx
# 1_40
# 1_49
# 3_07
# HonorRoll resave with this filename + as an .xlsx
# RATR
# SmartPassExport
# sync jupiter attendance and jupiter assignments
# FashionDollarTransactions


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    marking_period = form.marking_period.data
    students_df = return_students_df(marking_period).sort_values(
        by=["LastName", "FirstName"]
    )

    dfs_dict = return_dfs_dict(marking_period)
    f = generate_letters(students_df, dfs_dict, marking_period)
    download_name = f"{school_year}_{term}_Report_Cards.pdf"

    return f, download_name


def return_students_df(marking_period):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )

    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)

    counselors_df = return_counselors_df()
    cr_3_07_df = cr_3_07_df.merge(counselors_df, on=["StudentID"], how="left")
    fd_balances = return_fashion_dollar_balances()
    cr_3_07_df = cr_3_07_df.merge(fd_balances, on=["StudentID"], how="left").fillna(
        {"fashion_dollar_balance": 0}
    )

    honor_roll_df = return_honor_roll_flag_df(marking_period)
    cr_3_07_df = cr_3_07_df.merge(honor_roll_df, on=["StudentID"], how="left").fillna(
        "Not on Honor Roll"
    )
    cr_1_40_df = return_df_by_title("1_40", year_and_semester)
    cr_1_40_df = cr_1_40_df.rename(columns={"Student": "StudentID"})
    cr_1_40_df = cr_1_40_df[["StudentID", "Average", "Minimum"]]
    cr_3_07_df = cr_3_07_df.merge(cr_1_40_df, on=["StudentID"], how="left").fillna("")

    return cr_3_07_df


from app.scripts.attendance.process_RATR import main as process_RATR

from app.scripts.privileges.attendance_benchmark.attendance_benchmark import (
    return_overall_attd_benchmark,
)
from app.scripts.pbis.smartpass.main import (
    return_total_time_per_period_by_student,
    process_smartpass_data,
)


def return_dfs_dict(marking_period):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    RATR_df = return_df_by_title("RATR", year_and_semester)
    smartpass_df = return_df_by_title("SmartPassExport", year_and_semester)
    smartpass_df = process_smartpass_data(smartpass_df)
    dfs_dict = {
        "1_01": return_student_grades(),
        "HonorRoll": return_df_by_title("HonorRoll", year_and_semester),
        "assignments_df": return_df_by_title("assignments", year_and_semester),
        "jupiter_period_attendance_df": return_df_by_title(
            "jupiter_period_attendance", year_and_semester
        ),
        "jupiter_attd_summary_df": return_jupiter_attd_pvt(),
        "RATR_Summary_df": process_RATR(RATR_df),
        "jupiter_missing_assignment_pvt": return_jupiter_assignment_missing_pvt(),
        "RATR_df": RATR_df,
        "attd_benchmark_df": return_overall_attd_benchmark(),
        "smartpass_df": return_total_time_per_period_by_student(smartpass_df),
    }

    return dfs_dict


def return_fashion_dollar_balances():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    FashionDollarTransactions_df = return_df_by_title(
        "FashionDollarTransactions", year_and_semester
    )

    fashion_dollar_balances_df = pd.pivot_table(
        FashionDollarTransactions_df,
        index=["student"],
        columns="type",
        values="amount",
        aggfunc="sum",
    ).fillna(0)
    fashion_dollar_balances_df["fashion_dollar_balance"] = (
        fashion_dollar_balances_df["Deposit"] - fashion_dollar_balances_df["Withdrawal"]
    )
    fashion_dollar_balances_df = fashion_dollar_balances_df.reset_index()
    fashion_dollar_balances_df = fashion_dollar_balances_df.rename(
        columns={"student": "StudentID"}
    )
    return fashion_dollar_balances_df[["StudentID", "fashion_dollar_balance"]]


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
            values="Section",
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

    narrative_df = return_df_by_title("1_32", year_and_semester)
    cr_1_01_df = cr_1_01_df.merge(
        narrative_df[["StudentID", "Course", "Section", "Narrative"]],
        on=["StudentID", "Course", "Section"],
        how="left",
    ).fillna("")

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

    courses_to_exclude = [
        "EQS11S",
        "EAS11QQI",
        "MQS11S",
        "MAS11PE",
        "GQS11",
        "MQS11UQ1",
        "HGS11UQ1",
        "MSS11UQ1",
        "GLS11QYL",
        "GLS11QA",
        "GLS11QB",
        "RQS41TY",
        "RQS43TY",
    ]
    cr_1_01_df = cr_1_01_df[~cr_1_01_df["Course"].isin(courses_to_exclude)]
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
        "CARTER ANIKA": 'Ms. Carter - Room 723<br/> (212)-255-1235 x7235 - <a href="acarter15@schools.nyc.gov">acarter15@schools.nyc.gov</a>',
        "DE LEON ANGELINA": 'Ms. De Leon - Room 504<br/>(212)-255-1235 x5047 - <a href="adeleon23@schools.nyc.gov">adeleon23@schools.nyc.gov</a>',
        "MARIN BETH": 'Ms. Marin - Room 423<br/>(212)-255-1235 x4236 - <a href="bmarin5@schools.nyc.gov">bmarin5@schools.nyc.gov</a>',
        "DUKE JOSHUA": 'Mr. Duke - Room 643<br/>(212)-255-1235 x6430 - <a href="jduke@schools.nyc.gov">jduke@schools.nyc.gov</a>',
        "JONES ALEX": "",
        "WEISS JESSICA": 'Ms. Weiss - Room 423<br/>(212)-255-1235 x4235 - <a href="jweiss4@schools.nyc.gov">jweiss4@schools.nyc.gov</a>',
        "SAN JORGE AMELIA": 'Ms. San Jorge - Room 329<br/>(212)-255-1235 x3291 - <a href="asanjorge@schools.nyc.gov">asanjorge@schools.nyc.gov</a>',
        "POWIS TAFARI": 'Mr. Powis - Room 504<br/>(212)-255-1235 x5049 - <a href="tpowis@schools.nyc.gov">tpowis@schools.nyc.gov</a>',
        "PADRON AMANDA": 'Ms. Padron - Room 723<br/>(212)-255-1235 x7233 - <a href="apadron@schools.nyc.gov">apadron@schools.nyc.gov</a>',
        "CASTELLANO ASHLEY": 'Ms. Castellano - Room 643<br/>(212)-255-1235 x6432 - <a href="acastellano7@schools.nyc.gov">acastellano7@schools.nyc.gov</a>',
    }
    cr_1_49_df["counselor_str"] = cr_1_49_df["Counselor"].apply(
        lambda x: f"<b>Counselor:</b> {counselor_email_dict.get(x)}"
    )
    return cr_1_49_df


def return_honor_roll_flag_df(mp):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    HonorRoll_df = return_df_by_title("HonorRoll", year_and_semester)
    HonorRoll_df["honor_roll_flag"] = HonorRoll_df.apply(
        determine_honor_roll_flag, axis=1
    )
    HonorRoll_df = HonorRoll_df.rename(columns={"Student Id": "StudentID"})

    return HonorRoll_df[["StudentID", "honor_roll_flag"]]


def determine_honor_roll_flag(student):
    gpa = student["Average"]
    if gpa >= 90:
        return f"Principal's Honor Roll (90+)"
    else:
        return f"Honor Roll (85-90)"

    return f"Not on Honor Roll"


def return_df_by_title(title, year_and_semester):
    filename = utils.return_most_recent_report_by_semester(
        files_df, title, year_and_semester=year_and_semester
    )
    df = utils.return_file_as_df(filename)
    return df


def generate_letters(students_df, dfs_dict, marking_period):
    students_df["flowables"] = students_df.apply(
        generate_letter_flowables, axis=1, args=(dfs_dict, marking_period)
    )
    flowables = students_df["flowables"].explode().to_list()

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def generate_letter_flowables(student_row, dfs_dict, marking_period):

    flowables = []
    chart_style = TableStyle(
        [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    )

    left_flowables = return_left_flowables(student_row, dfs_dict, marking_period)
    right_flowables = return_student_class_flowables(
        student_row, dfs_dict, marking_period
    )

    flowables.append(
        Table(
            [[left_flowables, right_flowables]],
            colWidths=[4.25 * inch, 6.25 * inch],
            rowHeights=[7 * inch],
            style=chart_style,
        )
    )
    flowables.append(PageBreak())

    return flowables


def return_student_class_flowables(student_row, dfs_dict, marking_period):
    StudentID = student_row["StudentID"]
    class_flowables = []

    cr_1_01_df = dfs_dict["1_01"]

    student_classes_df = cr_1_01_df[cr_1_01_df["StudentID"] == StudentID]

    student_classes_df = student_classes_df.sort_values(by=["Period"])

    if len(student_classes_df) > 0:
        student_classes_df["flowables"] = student_classes_df.apply(
            return_class_flowables, axis=1, args=(dfs_dict, marking_period)
        )
        class_flowables = student_classes_df["flowables"].explode().to_list()

    return class_flowables


def return_class_flowables(student_row, dfs_dict, marking_period):
    StudentID = student_row["StudentID"]

    course_code = student_row["Course"]
    course_name = student_row["CourseName"]
    period = student_row["Period"]
    teacher = student_row["Teacher1"]
    mark = student_row[f"Mark{marking_period}"]
    narrative = student_row["Narrative"]

    if marking_period == "2":
        previous_mark = student_row[f"Mark1"]
    elif marking_period == "3":
        previous_mark = student_row[f"Mark2"]
    else:
        previous_mark = student_row[f"Mark1"]

    mark_indicator = return_mark_indicator(mark, previous_mark, marking_period)

    JupiterCourseCode = student_row["JupiterCourse"]
    # assignments_df = dfs_dict["assignments_df"]
    # assignments_df = assignments_df[assignments_df["StudentID"] == StudentID]
    # assignments_df = assignments_df[assignments_df["Course"] == JupiterCourseCode]

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

    has_practice = "Practice" in jupiter_missing_assignment_pvt["Category"].to_list()
    has_performance = (
        "Performance" in jupiter_missing_assignment_pvt["Category"].to_list()
    )

    if num_of_missing_practice == 0:
        practice_str = f"Completed all {total_practice:.0f} practice assignments"
    elif not has_practice:
        practice_str = ""
    else:
        practice_str = f"Missing {num_of_missing_practice:.0f} of {total_practice:.0f} practice assignments"

    if num_of_missing_performance == 0:
        performance_str = (
            f"Completed all {total_performance:.0f} performance assignments"
        )
    elif not has_performance:
        performance_str = ""
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
    try:
        if int(mark) >= 65:
            mark_fontname = "Helvetica"
        else:
            mark_fontname = "Helvetica-Bold"
    except:
        mark_fontname = "Helvetica-Bold"
    table_data = [
        [f"P{period}", course_name, I],
        [f"{mark}{mark_indicator}", teacher, ""],
        ["", practice_str, performance_str],
    ]
    colWidths = [0.75 * inch, 2.625 * inch, 2.625 * inch]
    rowHeights = [0.275 * inch, 0.275 * inch, 0.25 * inch]
    table_style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        # ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 2, colors.black),
        ("SPAN", (2, 0), (2, 1)),
        ("SPAN", (0, 1), (0, 2)),
        ("FONTSIZE", (0, 1), (0, 1), 20),
        ("FONTNAME", (0, 1), (0, 1), mark_fontname),
        ("BOTTOMPADDING", (0, 1), (0, 1), 25),
    ]
    if narrative:
        narrative_paragraph = Paragraph(
            f"{narrative}",
            styles["Normal"],
        )
        table_data.append([narrative_paragraph, "", ""])
        rowHeights = [0.275 * inch, 0.275 * inch, 0.25 * inch, None]
        table_style.append(("SPAN", (0, 3), (2, 3)))

    t = Table(table_data, colWidths=colWidths, rowHeights=rowHeights)
    t.setStyle(TableStyle(table_style))
    return t


def return_mark_indicator(mark, previous_mark, marking_period):
    if marking_period == "1":
        return ""
    try:
        if int(mark) > int(previous_mark):
            return "▲"
        if int(mark) < int(previous_mark):
            return "▼"
        else:
            return ""
    except:
        return ""


def return_left_flowables(student_row, dfs_dict, marking_period):
    flowables = []
    LastName = student_row["LastName"]
    FirstName = student_row["FirstName"]
    StudentID = student_row["StudentID"]

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    paragraph = Paragraph(
        f"{year_and_semester}-MP{marking_period} Report Card",
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
    gpa = student_row["Average"]
    paragraph = Paragraph(
        f"<b>GPA:</b> {gpa} - {honor_roll_flag}",
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

    fashion_dollar_balance = student_row["fashion_dollar_balance"]
    paragraph = Paragraph(
        f"<b>Fashion Dollar Balance:</b> {fashion_dollar_balance:.0f}",
        styles["Normal"],
    )
    flowables.append(paragraph)

    smartpass_df = dfs_dict["smartpass_df"]
    student_smartpass_df = smartpass_df[smartpass_df["StudentID"] == StudentID]
    if len(student_smartpass_df) > 0:

        total_time_str = get_time_hh_mm_ss(student_smartpass_df.iloc[0]["Total"])
        class_periods_equivalent_str = return_class_period_equivalence(
            student_smartpass_df.iloc[0]["Total"]
        )
        paragraph = Paragraph(
            f"<b>Bathroom Passes by Period:</b> Since the beginning of the school year, you have missed {total_time_str} of classtime -- this is equivalent to {class_periods_equivalent_str} class periods",
            styles["Normal"],
        )
        flowables.append(paragraph)
        I = smartpass_usage_by_period(student_smartpass_df.iloc[0])
        flowables.append(I)

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
        out_to_lunch_str = "<b>Eligible for Out to Lunch Pass</b>: You have met the out to lunch criteria of (1) passing all classes and (2) present 90% and on time 80% to all of your classes!"
    elif passed_all_classes:
        out_to_lunch_str = "<b>Not Eligible for Out to Lunch Pass</b>: You have met the out to lunch criteria of (1) passing all classes but not (2) present 90% and on time 80% to all of your classes. Work on improving your attendance next marking period."
    elif attd_benchmark:
        out_to_lunch_str = "<b>Not Eligible for Out to Lunch Pass</b>: You have not met the out to lunch criteria of (1) passing all classes but you have (2) present 90% and on time 80% to all of your classes. Work on passing all of your classes next marking period."
    else:
        out_to_lunch_str = "<b>Not Eligible for Out to Lunch Pass</b>: You have not met the out to lunch criteria of (1) passing all classes or (2) present 90% and on time 80% to all of your classes. Work on improving your period attendance and passing all of your classes next marking period."

    paragraph = Paragraph(
        f"{out_to_lunch_str}",
        styles["Normal"],
    )
    return paragraph


def return_attendance_sentence_paragraphs(student_RATR_df):
    total_days = len(student_RATR_df)

    if total_days == 0:
        paragraph = Paragraph(
            f"<b>Attendance:</b> Enrolled zero days at this time.",
            styles["Normal"],
        )
        return [paragraph]

    days_present_and_on_time = student_RATR_df[student_RATR_df["ATTD"] == "P"][
        "Date"
    ].to_list()
    num_of_days_present_and_on_time = len(days_present_and_on_time)
    days_present_and_on_time_frequency_str = utils.convert_percentage_to_ratio(
        num_of_days_present_and_on_time / total_days
    )
    paragraphs = []

    paragraph = Paragraph(
        f"<b>Present and On Time:</b> {num_of_days_present_and_on_time} of {total_days} days ({days_present_and_on_time_frequency_str})",
        styles["Normal"],
    )
    paragraphs.append(paragraph)

    days_late = student_RATR_df[student_RATR_df["ATTD"] == "L"]["Date"].to_list()
    num_of_days_late = len(days_late)
    days_late_lst_str = ", ".join([x.strftime("%m/%d") for x in days_late])
    days_late_frequency_str = utils.convert_percentage_to_ratio(
        num_of_days_late / total_days
    )
    if num_of_days_late == 0:
        paragraph = Paragraph(
            f"<b>Lates:</b> Zero days so far this semester. Keep it up!",
            styles["Normal"],
        )
        paragraphs.append(paragraph)
    else:
        paragraph = Paragraph(
            f"<b>Lates:</b> {num_of_days_late} days ({days_late_frequency_str}) so far this semester: {days_late_lst_str}",
            styles["Normal"],
        )
        paragraphs.append(paragraph)

    days_absent = student_RATR_df[student_RATR_df["ATTD"] == "A"]["Date"].to_list()
    num_of_days_absent = len(days_absent)
    days_absent_lst_str = ", ".join([x.strftime("%m/%d") for x in days_absent])
    days_absent_frequency_str = utils.convert_percentage_to_ratio(
        num_of_days_absent / total_days
    )

    if num_of_days_absent == 0:
        paragraph = Paragraph(
            f"<b>Absences:</b> Zero days so far this semester. Keep it up!",
            styles["Normal"],
        )
        paragraphs.append(paragraph)
    else:
        paragraph = Paragraph(
            f"<b>Absences:</b> {num_of_days_absent} days ({days_absent_frequency_str}) so far this semester: {days_absent_lst_str}",
            styles["Normal"],
        )
        paragraphs.append(paragraph)

    return paragraphs


color_discrete_sequence = ["#32CD32", "#FAFA33", "#FF3131"]


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
        color_discrete_sequence=color_discrete_sequence,
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
        marker_line_color="grey",
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
    y_aspect = 190
    x_aspect = 600
    scale = 0.7

    fig = px.bar(
        df,
        y=df.index,
        x=["present", "late", "absent"],
        title="<br>Period Attendance",
        text_auto=True,
        # pattern_shape_sequence=[".", "x", "+"],
        orientation="h",
        # color="ATTD",
        color_discrete_sequence=color_discrete_sequence,
        barmode="stack",
    )

    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=5, b=5),
        height=scale * y_aspect,
        width=scale * x_aspect,
        # xaxis_tickmode="array",
        yaxis_visible=False,
        yaxis_showticklabels=False,
        xaxis_visible=False,
        xaxis_showticklabels=False,
        legend_title_text="# of Periods",
        title=dict(
            x=0.5,  # Center the title horizontally (0 is left, 1 is right)
            y=0.9,  # Adjust vertical position (0 is bottom, 1 is top)
            xanchor="center",  # Anchor horizontally to the center
            # yanchor="top",  # Anchor vertically to the top
            # font=dict(size=20),  # Adjust the font size
        ),
        legend=dict(
            orientation="h",  # Make the legend horizontal
            y=0.275,  # Adjust the vertical position to place it below the chart
            xanchor="center",  # Center the legend horizontally
            x=0.5,  # Center the legend horizontally
        ),
    )
    fig.update_traces(
        textfont_size=26,
        textangle=0,
        textposition="auto",
        cliponaxis=False,
        marker_line_width=2,
        marker_line_color="grey",
        width=0.4,
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)

    I = Image(buffer)
    width = 2.1 * inch
    I.drawHeight = y_aspect / x_aspect * width
    I.drawWidth = x_aspect / x_aspect * width

    return I


from datetime import timedelta


def get_time_hh_mm_ss_short(sec):
    td_str = str(timedelta(seconds=sec))
    x = td_str.split(":")
    if x[0] == "0":
        return f"{x[1]}m"
    else:
        if x[1][0] == "0":
            return f"{x[0]}h{x[-1]}m"
        else:
            return f"{x[0]}h{x[1]}m"


def smartpass_usage_by_period(student_row):
    y_aspect = 200
    x_aspect = 500

    y = ["Pd-1", "Pd-2", "Pd-3", "Pd-4", "Pd-5", "Pd-6", "Pd-7", "Pd-8", "Pd-9"]

    x = [
        student_row[1.0],
        student_row[2.0],
        student_row[3.0],
        student_row[4.0],
        student_row[5.0],
        student_row[6.0],
        student_row[7.0],
        student_row[8.0],
        student_row[9.0],
    ]

    text = [get_time_hh_mm_ss_short(x) for x in x[::-1]]
    data = [go.Bar(x=x[::-1], y=y[::-1], text=text, orientation="h")]
    fig = go.Figure(data=data)

    MINUTE_INCREMENT = 45
    SECONDS_INCREMENT = 60 * MINUTE_INCREMENT

    x_tickvals = [
        i * SECONDS_INCREMENT
        for i in range(1, 100)
        if i * SECONDS_INCREMENT <= max(x) + SECONDS_INCREMENT
    ]
    x_ticktext = [get_time_hh_mm_ss_short(x) for x in x_tickvals]

    scale = 1
    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=0, b=0),
        height=scale * y_aspect,
        width=scale * x_aspect,
        xaxis_tickmode="array",
        xaxis_tickvals=x_tickvals,
        xaxis_ticktext=x_ticktext,
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)
    I = Image(buffer)
    I.drawHeight = y_aspect / x_aspect * 4 * inch
    I.drawWidth = x_aspect / x_aspect * 4 * inch

    return I


def return_class_period_equivalence(sec):
    return f"{round(sec/(45*60))}"


def get_time_hh_mm_ss(sec):
    td_str = str(timedelta(seconds=int(sec)))
    x = td_str.split(":")
    return f"{x[0]} hours and {x[1]} minutes"
