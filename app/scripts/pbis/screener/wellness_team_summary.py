import pandas as pd
from pandas.api.types import CategoricalDtype

import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for


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


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_small", parent=styles["Normal"], alignment=TA_CENTER, fontSize=8
    )
)

from app.scripts.pbis.screener.main import process_screener_data


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.file.name]

    dfs_dict = pd.read_excel(filename, sheet_name=None)
    df = process_screener_data(dfs_dict)

    df = df.dropna(subset="LastName")

    f = return_download_file(df)

    download_name = f"UniversalScreenerAnalysisWellnessTeam.xlsx"
    # return '', ''
    return f, download_name


def return_download_file(df):

    sheets = []

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Counselor",
        "IEPFlag","LunchPeriod",
        "How well does this student interact with peers in the classroom during small group and pair work? - Above Average",
        "How well does this student leverage work habits (studying, note-taking, time management, etc.) to meet their full academic potential in this class? - Above Average",
        "How well does this student remain engaged in class during individual or whole class work? - Above Average",
        "How well does this student interact with peers in the classroom during small group and pair work? - Below Average",
        "How well does this student leverage work habits (studying, note-taking, time management, etc.) to meet their full academic potential in this class? - Below Average",
        "How well does this student remain engaged in class during individual or whole class work? - Below Average",
        "I feel like I belong at HSFI",
        "I feel like my HSFI classmates care about me",
        "I feel comfortable interacting with other students in my classes",
        "I have friends at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with making friends at HSFI",
        "I have an adult at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with getting to HSFI on time every day.",
        "I need help from the school with learning how to control my emotions",
        "I need help from the school with learning how to improve my work habits to reach my academic potential",
        "risk_factor",
    ]

    df = df.sort_values(by=["Total Net"])
    students_df = df.drop_duplicates(subset="StudentID")

    student_survey_questions = [
        "I feel like I belong at HSFI",
        "I feel like my HSFI classmates care about me",
        "I feel comfortable interacting with other students in my classes",
        "I have friends at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with making friends at HSFI",
        "I have an adult at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with getting to HSFI on time every day.",
        "I need help from the school with learning how to control my emotions",
        "I need help from the school with learning how to improve my work habits to reach my academic potential",
    ]

    students_df["risk_factor"] = 0
    for question in student_survey_questions:
        students_df["risk_factor"] = students_df["risk_factor"] + students_df[
            question
        ].apply(return_at_risk, args=(question,))

    for cohort, cohort_students_df in students_df.groupby("GEC"):
        sheets.append((f"{cohort}", cohort_students_df[cols]))

        sheets.append((f"{cohort}_summary", return_questions_pvt(cohort_students_df)))

    sheets.append((f"AllStudents", students_df[cols]))

    sheets.append((f"AllStudents_summary", return_questions_pvt(students_df)))

    for counselor, counselor_students_df in students_df.groupby("Counselor"):
        risk_factor_students = counselor_students_df[
            counselor_students_df["risk_factor"] > 0
        ].sort_values(by=["risk_factor"], ascending=[False])
        students_of_interest = pd.concat(
            [
                counselor_students_df.head(10),
                counselor_students_df.tail(10),
                risk_factor_students,
            ]
        )
        students_of_interest = students_of_interest.drop_duplicates(
            subset=["StudentID"], keep="first"
        )
        sheets.append((f"{counselor}", students_of_interest[cols]))
        

    f = BytesIO()

    writer = pd.ExcelWriter(f)
    workbook = writer.book
    perc_fmt = workbook.add_format({"num_format": "0%", "align": "center"})
    text_wrap_fmt = workbook.add_format({"text_wrap": True})
    text_wrap_fmt.set_text_wrap()

    for sheet_name, sheet_df in sheets:

        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        if "_summary" in sheet_name:
            worksheet = writer.sheets[sheet_name]
            # worksheet.set_column('b2:f15', 10.00, perc_fmt)
            insert_student_survey_questions_chart(writer, sheet_name)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()
        worksheet.set_column(3, 17, 20, text_wrap_fmt)
        if "_summary" in sheet_name:
            worksheet.set_column(1, 8, 10, perc_fmt)

    writer.close()
    f.seek(0)

    return f


def return_at_risk(student_response, question):
    student_response = str(student_response)

    if "I need help" in question:
        look_for = "Agree"
    else:
        look_for = "Disagree"

    if f"Strongly {look_for}" in student_response:
        return 1
    if look_for in student_response:
        return 0.5
    else:
        return 0


def insert_student_survey_questions_chart(writer, sheet):

    workbook = writer.book
    worksheet = writer.sheets[sheet]

    diverging_bar_chart = workbook.add_chart(
        {"type": "bar", "subtype": "percent_stacked"}
    )

    cols = [
        "left_buffer",
        "Strongly Agree",
        "Agree",
        "Disagree",
        "Strongly Disagree",
        "right_buffer",
    ]
    fill_colors = [
        {"none": True},
        {"color": "#118ab2"},
        {"color": "#06d6a0"},
        {"color": "#ffd166"},
        {"color": "#ef476f"},
        {"none": True},
    ]
    patterns = []
    letters = ["B", "C", "D", "E", "F", "G"]
    custom_label_letters = ["", "H", "I", "J", "K", ""]
    custom_label_letters = ["", "C", "D", "E", "F", ""]
    i = 11
    for col, letter, fill_color, custom_letter in zip(
        cols, letters, fill_colors, custom_label_letters
    ):
        custom_labels = [
            {"value": f"={sheet}!${custom_letter}${j}"} for j in range(2, i)
        ]

        series_dict = {
            "name": col,
            "categories": f"={sheet}!$A$2:$A${i-1}",
            "values": f"={sheet}!${letter}$2:${letter}${i-1}",
            "fill": fill_color,
        }

        if custom_letter != "":
            series_dict["data_labels"] = {"value": True, "custom": custom_labels}

        diverging_bar_chart.add_series(series_dict)

    diverging_bar_chart.set_legend(
        {
            "position": "bottom",
            "font": {"size": 12, "bold": True, "name": "Helvetica Neue"},
            "delete_series": [0, 5],
        }
    )

    diverging_bar_chart.set_y_axis(
        {"name_font": {"size": 14, "bold": True, "name": "Helvetica Neue"}}
    )

    diverging_bar_chart.set_x_axis(
        {
            "visible": False,
        }
    )
    chart_title_string = f"Cohort {sheet[0]} Survey"
    diverging_bar_chart.set_title({"name": chart_title_string})
    diverging_bar_chart.set_size({"x_scale": 2, "y_scale": 1.5})

    # Insert the chart into the worksheet (with an offset).
    chartsheet = workbook.add_chartsheet(f"{sheet}_chart")
    chartsheet.set_chart(diverging_bar_chart)
    return ""


def return_questions_pvt(df):
    questions_for_graph = [
        "I feel like I belong at HSFI",
        "I feel like my HSFI classmates care about me",
        "I feel comfortable interacting with other students in my classes",
        "I have friends at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with making friends at HSFI",
        "I have an adult at HSFI I feel a connection with and can go to if I have concerns",
        "I need help from the school with getting to HSFI on time every day.",
        "I need help from the school with learning how to control my emotions",
        "I need help from the school with learning how to improve my work habits to reach my academic potential",
    ]
    id_vars = [x for x in df.columns if x not in questions_for_graph]
    dff = df.melt(id_vars=id_vars, var_name="Question", value_name="StudentResponse")

    cat_type = CategoricalDtype(
        categories=["Strongly Agree", "Agree", "Disagree", "Strongly Disagree"],
        ordered=True,
    )
    dff["StudentResponse"] = dff["StudentResponse"].astype(cat_type)

    student_pvt = pd.pivot_table(
        dff,
        index=["Question"],
        columns="StudentResponse",
        values="Counselor",
        aggfunc="count",
        margins=True,
    ).fillna(0)

    student_pvt = student_pvt.iloc[:-1]
    student_pvt = student_pvt / student_pvt["All"].mean()

    student_pvt["right_buffer"] = student_pvt["Agree"] + student_pvt["Strongly Agree"]
    student_pvt["left_buffer"] = (
        student_pvt["Disagree"] + student_pvt["Strongly Disagree"]
    )

    student_pvt = student_pvt[
        [
            "left_buffer",
            "Strongly Agree",
            "Agree",
            "Disagree",
            "Strongly Disagree",
            "right_buffer",
        ]
    ]

    return student_pvt.reset_index()
