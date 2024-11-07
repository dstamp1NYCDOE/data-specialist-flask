from flask import session

import pandas as pd

from io import BytesIO
import datetime as dt
import app.scripts.utils as utils
from app.scripts import scripts, files_df


def main():
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

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report_by_semester(
        files_df, "rosters_and_grades", year_and_semester=year_and_semester
    )
    grades_df = utils.return_file_as_df(filename)

    ## assignments
    filename = utils.return_most_recent_report_by_semester(
        files_df, "assignments", year_and_semester=year_and_semester
    )
    assignments_df = utils.return_file_as_df(filename)

    assignments_df = assignments_df[assignments_df["Course"] != ""]

    # drop assignments worth zero
    assignments_df = assignments_df.dropna(subset=["RawScore"])
    assignments_df = assignments_df[assignments_df["WorthPoints"] != 0]

    marks_to_keep = ["0!", "1!", "2!", "3!", "4!", "5!"]
    assignments_df = assignments_df[assignments_df["RawScore"].isin(marks_to_keep)]

    ##drop non-credit bearing classes
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "G"]
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "Z"]

    ##Add Dept
    dept_dict = {
        "R": "CTE",
        "F": "LOTE",
        "P": "PE",
        "B": "CTE",
        "A": "CTE",
        "M": "Math",
        "E": "ELA",
        "T": "CTE",
        "S": "Sci",
        "H": "SS",
    }
    assignments_df["Dept"] = (
        assignments_df["Course"].str[0].apply(lambda x: dept_dict.get(x))
    )

    # prep lists
    lst_of_dept = assignments_df["Dept"].unique()
    lst_of_courses = assignments_df["Course"].unique()
    lst_of_teachers = assignments_df["Teacher"].unique()

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    teacher_pvt = pd.pivot_table(
        assignments_df,
        index=["Teacher", "Course", "Dept"],
        columns=["Category", "RawScore"],
        values="WorthPoints",
        aggfunc="sum",
    ).fillna(0)

    teacher_pvt["Performance"] = (
        teacher_pvt["Performance"]
        .div(teacher_pvt["Performance"].sum(axis=1), axis=0)
        .fillna(0)
    )
    teacher_pvt["Practice"] = (
        teacher_pvt["Practice"]
        .div(teacher_pvt["Practice"].sum(axis=1), axis=0)
        .fillna(0)
    )
    teacher_pvt.loc[("SchoolWide",) * 3, :] = teacher_pvt.sum().values
    for dept in lst_of_dept:
        teacher_pvt.loc[("SchoolWide", "SchoolWide", dept), :] = (
            teacher_pvt.query(f"Dept == '{dept}' ").sum().values
        )

    for course in lst_of_courses:
        dept = course[0]
        teacher_pvt.loc[("SchoolWide", course, dept), :] = (
            teacher_pvt.query(f"Course == '{course}' ").sum().values
        )

    teacher_pvt["Performance"] = (
        teacher_pvt["Performance"]
        .div(teacher_pvt["Performance"].sum(axis=1), axis=0)
        .fillna(0)
    )
    teacher_pvt["Practice"] = (
        teacher_pvt["Practice"]
        .div(teacher_pvt["Practice"].sum(axis=1), axis=0)
        .fillna(0)
    )

    teacher_pvt = teacher_pvt * 100

    teacher_pvt[("Practice", "WeightedAvg")] = teacher_pvt["Practice"].apply(
        weighted_average, axis=1
    )
    teacher_pvt[("Performance", "WeightedAvg")] = teacher_pvt["Performance"].apply(
        weighted_average, axis=1
    )

    flowables = []

    ## charts for APs
    for dept in lst_of_dept:
        overall_comp = teacher_pvt.query(
            "(Dept=='SchoolWide') | (Dept.isin(@lst_of_dept)) & (~Course.isin(@lst_of_courses)) "
        )
        dept_comp = teacher_pvt.query(
            "(Dept == @dept) & (Course.isin(@lst_of_courses))"
        )
        categories = ["Performance", "Practice"]
        for category in categories:
            df = overall_comp[category].reset_index()
            df = df.sort_values(by=["5!"])
            df["y"] = df["Dept"]
            plot_formatting_data = {
                "title": f"Overall Schoolwide - {category}",
                "y_aspect": 200,
                "avg_five_val": df["5!"].mean(),
            }
            I = return_schoolwide_graph(df, plot_formatting_data)
            flowables.append(I)

            df = dept_comp[category].reset_index()
            df = df.sort_values(by=["5!"])
            df["y"] = df["Course"] + " " + df["Teacher"]
            plot_formatting_data = {
                "title": f"Overall {dept} - {category}",
                "y_aspect": 575,
                "avg_five_val": df["5!"].mean(),
            }
            I = return_schoolwide_graph(df, plot_formatting_data)
            flowables.append(I)

        flowables.append(PageBreak())

    ## teacher flowables
    for teacher in lst_of_teachers[0:2]:
        temp_pvt = teacher_pvt.query(f"Teacher == '{teacher}' ")
        teacher_courses = temp_pvt.loc[(teacher)].index.unique(0)
        teacher_depts = temp_pvt.loc[(teacher)].index.unique(1)

        ## prepare teacher's courses compared to schoolwide +
        school_comp = teacher_pvt.query(
            "(Teacher == @teacher | Teacher=='SchoolWide') & (Course.isin(@teacher_courses) | Course=='SchoolWide') & (Dept.isin(@teacher_depts) | Dept=='SchoolWide')"
        )

        ## prepare comparing teacher to others teaching same course
        class_comp = teacher_pvt.query("Course.isin(@teacher_courses)")

        ## schoolwide graphs
        categories = ["Performance", "Practice"]
        for category in categories:
            plot_formatting_data = {
                "title": f"{teacher} - {category}",
                "y_aspect": 250,
                "avg_five_val": df["5!"].mean(),
            }
            school_comp_df = school_comp[category].reset_index()
            school_comp_df["y"] = (
                school_comp_df["Teacher"]
                + " "
                + school_comp_df["Course"]
                + " "
                + school_comp_df["Dept"]
            )
            I = return_schoolwide_graph(school_comp_df, plot_formatting_data)
            flowables.append(I)

        flowables.append(PageBreak())

    f = build_letters(flowables)

    return f, "download.pdf"


import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from reportlab.platypus import Image, PageBreak


def return_schoolwide_graph(df, plot_formatting_data):
    color_discrete_sequence=[
            "#3a3a3a",
            "#838383",
            "#aeaeae",
            "#c9c9c9",
            "#e5e5e5",
            "#ffffff",
        ]
    color_discrete_sequence.reverse()
    y_aspect = plot_formatting_data["y_aspect"]
    avg_five_val = plot_formatting_data["avg_five_val"]

    x_aspect = 600
    scale = 1.50

    title = plot_formatting_data["title"]
    x = ["0!", "1!", "2!", "3!", "4!", "5!"]
    fig = px.bar(
        df,
        y=df["y"],
        title=title,
        x=x,
        text_auto=".0f",
        orientation="h",
        color_discrete_sequence=color_discrete_sequence,
    )
    fig.add_vline(
        x=100 - avg_five_val,
        line_width=3,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Avg 5! - {avg_five_val:.0f} %",
        annotation_position="top",
    )
    fig.update_layout(
        template="simple_white",
        margin=dict(l=75, r=75, t=50, b=25),
        height=scale * y_aspect,
        width=scale * x_aspect,
        # xaxis_tickmode="array",
        # yaxis_visible=False,
        # yaxis_showticklabels=False,
        xaxis_visible=False,
        xaxis_showticklabels=False,
        title=dict(
            x=0.5,  # Center the title horizontally (0 is left, 1 is right)
            y=1,  # Adjust vertical position (0 is bottom, 1 is top)
            xanchor="center",  # Anchor horizontally to the center
            yanchor="top",  # Anchor vertically to the top
            font=dict(size=20),  # Adjust the font size
        ),
        legend_title_text="% of Pts",
        legend=dict(
            orientation="v",  # Make the legend horizontal
            y=0.5,  # Adjust the vertical position to place it below the chart
            xanchor="center",  # Center the legend horizontally
            x=1.1,  # Center the legend horizontally
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
    width = 8 * inch
    I.drawHeight = y_aspect / x_aspect * width
    I.drawWidth = x_aspect / x_aspect * width

    return I


from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.units import mm, inch
from reportlab.lib.pagesizes import letter, landscape


def build_letters(flowables):
    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.25 * inch,
        rightMargin=0.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f


def weighted_average(row):
    sum_of_weights = (
        row["0!"] + row["1!"] + row["2!"] + row["3!"] + row["4!"] + row["5!"]
    )
    return (
        0 * row["0!"]
        + 1 * row["1!"]
        + 2 * row["2!"]
        + 3 * row["3!"]
        + 4 * row["4!"]
        + 5 * row["5!"]
    ) / sum_of_weights
