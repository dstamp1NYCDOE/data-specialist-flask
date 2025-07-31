from flask import session

import pandas as pd

from io import BytesIO
import datetime as dt
import app.scripts.utils.utils as utils
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
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "R"]

    ## drop non core ELA
    assignments_df = assignments_df[assignments_df["Course"].str[0:2] != "EQ"]
    assignments_df = assignments_df[assignments_df["Course"].str[0:2] != "ES"]


    ## remove success skills asessments
    assignments_df = assignments_df[assignments_df["Objective"] != "Success Skills"]

    ## attach student info
    assignments_df = assignments_df.merge(students_df, on=["StudentID"], how="left")

    ## pull in analyzed_jupiter
    from app.scripts.attendance.jupiter.process import main as processed_jupiter_attd

    jupiter_df = processed_jupiter_attd()

    cuts_by_students_by_class_df = pd.pivot_table(
        jupiter_df[jupiter_df["potential_cut"]],
        index=["StudentID", "Course", "Section"],
        values=["Date"],
        aggfunc="count",
    )
    cuts_by_students_by_class_df.columns = ["num_of_cuts"]
    cuts_by_students_by_class_df = cuts_by_students_by_class_df.reset_index()

    assignments_df = assignments_df.merge(
        cuts_by_students_by_class_df, on=["StudentID", "Course", "Section"], how="left"
    ).fillna(0)

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
    assignments_df["Dept"] = assignments_df["Course"].apply(return_department)

    # prep lists
    lst_of_dept = assignments_df["Dept"].unique()
    lst_of_courses = assignments_df["Course"].unique()
    lst_of_teachers = assignments_df["Teacher"].unique()
    lst_of_cuts = assignments_df["num_of_cuts"].unique()

    f = BytesIO()

    #### teacher pvt

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
        dept = return_department(course)
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

    #### with cuts pvt

    cuts_pvt = pd.pivot_table(
        assignments_df,
        index=["Teacher", "Course", "Dept", "num_of_cuts"],
        columns=["Category", "RawScore"],
        values="WorthPoints",
        aggfunc="sum",
    ).fillna(0)

    cuts_pvt["Performance"] = (
        cuts_pvt["Performance"]
        .div(cuts_pvt["Performance"].sum(axis=1), axis=0)
        .fillna(0)
    )
    cuts_pvt["Practice"] = (
        cuts_pvt["Practice"].div(cuts_pvt["Practice"].sum(axis=1), axis=0).fillna(0)
    )
    cuts_pvt.loc[("SchoolWide",) * 4, :] = cuts_pvt.sum().values

    for dept in lst_of_dept:
        cuts_pvt.loc[("SchoolWide", "SchoolWide", dept, "SchoolWide"), :] = (
            cuts_pvt.query(f"Dept == '{dept}' ").sum().values
        )
        for num_of_cuts in lst_of_cuts:
            cuts_pvt.loc[("SchoolWide", "SchoolWide", dept, num_of_cuts), :] = (
                cuts_pvt.query(f"(num_of_cuts == {num_of_cuts}) & (Dept == '{dept}') ")
                .sum()
                .values
            )

    for course in lst_of_courses:
        dept = return_department(course)
        cuts_pvt.loc[("SchoolWide", course, dept, "SchoolWide"), :] = (
            cuts_pvt.query(f"Course == '{course}' ").sum().values
        )
        for num_of_cuts in lst_of_cuts:
            cuts_pvt.loc[("SchoolWide", course, dept, num_of_cuts), :] = (
                cuts_pvt.query(
                    f"(num_of_cuts == {num_of_cuts}) & (Course == '{course}') "
                )
                .sum()
                .values
            )

    for num_of_cuts in lst_of_cuts:
        cuts_pvt.loc[("SchoolWide", "SchoolWide", "SchoolWide", num_of_cuts), :] = (
            cuts_pvt.query(f"num_of_cuts == {num_of_cuts} ").sum().values
        )

    cuts_pvt["Performance"] = (
        cuts_pvt["Performance"]
        .div(cuts_pvt["Performance"].sum(axis=1), axis=0)
        .fillna(0)
    )
    cuts_pvt["Practice"] = (
        cuts_pvt["Practice"].div(cuts_pvt["Practice"].sum(axis=1), axis=0).fillna(0)
    )

    cuts_pvt = cuts_pvt * 100

    cuts_pvt[("Practice", "WeightedAvg")] = cuts_pvt["Practice"].apply(
        weighted_average, axis=1
    )
    cuts_pvt[("Performance", "WeightedAvg")] = cuts_pvt["Performance"].apply(
        weighted_average, axis=1
    )

    flowables = []

    overall_comp = teacher_pvt.query(
        "(Dept=='SchoolWide') | (Dept.isin(@lst_of_dept)) & (~Course.isin(@lst_of_courses)) "
    )
    categories = ["Performance", "Practice"]
    for category in categories:
        df = overall_comp[category].reset_index()
        df = df.sort_values(by=["5!"])
        df["y"] = df["Dept"]
        plot_formatting_data = {
            "title": f"Overall Schoolwide - {category}",
            "y_aspect": 750,
            "avg_five_val": df[df['y']=='SchoolWide']["5!"].mean(),
            'avg_score':df[df['y']=='SchoolWide']["WeightedAvg"].mean(),
        }
        I = return_schoolwide_graph(df, plot_formatting_data)
        flowables.append(I)
        flowables.append(PageBreak())

    ## looking at cuts
    # cuts_comp = cuts_pvt.query(
    #     "(Dept=='SchoolWide') & (Course=='SchoolWide')  & (Teacher=='SchoolWide') & (num_of_cuts!='SchoolWide')"
    # )
    # categories = ["Performance", "Practice"]
    # for category in categories:
    #     df = cuts_comp[category].reset_index()
    #     df = df.sort_values(by=["num_of_cuts"])
    #     df["y"] = df["num_of_cuts"]
    #     plot_formatting_data = {
    #         "title": f"Overall Schoolwide by Cuts - {category}",
    #         "y_aspect": 750,
    #         "avg_five_val": df["5!"].mean(),
    #         'avg_score':df["WeightedAvg"].mean(),
    #     }
    #     I = return_schoolwide_graph(df, plot_formatting_data)
    #     flowables.append(I)
    #     flowables.append(PageBreak())

    ## charts for APs
    for dept in lst_of_dept:
        dept_comp = teacher_pvt.query(
            "(Dept == @dept) & (Course.isin(@lst_of_courses)) & (Teacher != 'SchoolWide') "
        )

        for category in categories:
            df = dept_comp[category].reset_index()
            for i in range(2):
                if i == 0:
                    df = df.sort_values(by=["5!"])
                else:
                    df = df.sort_values(by=["Course", "5!"])

                df["y"] = df["Course"] + "<br>" + df["Teacher"]
                plot_formatting_data = {
                    "title": f"Overall {dept} - {category}",
                    "y_aspect": 750,
                    "avg_five_val": df["5!"].mean(),
                    'avg_score':df["WeightedAvg"].mean(),
                }
                I = return_schoolwide_graph(df, plot_formatting_data)
                flowables.append(I)

                flowables.append(PageBreak())

    f = build_letters(flowables)

    RETURN_CHARTS = True
    if RETURN_CHARTS:
        return f, "JupiterAssignmentsAnalysis.pdf"
    else:
        f = BytesIO()
        writer = pd.ExcelWriter(f)
        teacher_pvt.reset_index().to_excel(writer, sheet_name="by_teacher")
        cuts_pvt.reset_index().to_excel(writer, sheet_name="by_cuts")
        writer.close()
        f.seek(0)
        return f, "JupiterAssignmentsAnalysis.xlsx"


def return_department(course_code):
    if course_code[1] == "K" and course_code[0] != "B":
        return "CTE-SD"
    if course_code[0:2] == "TQ":
        return "CTE-SD"
    if course_code[0] == "S":
        return "Science"
    if course_code[0] == "M":
        return "Math"
    if course_code[0] == "E":
        return "ELA"
    if course_code[0] == "F":
        return "LOTE"
    if course_code[0] == "H":
        return "SS"
    if course_code[0:2] == "PP":
        return "PE"
    if course_code[0:2] == "PH":
        return "Health"    
    if course_code[0:2] == "AH":
        return "SS"
    if course_code[0:2] == "AF":
        return "CTE-FD"
    if course_code[0] == "B":
        return "CTE-FMM"
    if course_code[0:2] == "TU":
        return "CTE-FMM"
    if course_code[0:2] == "AC":
        return "CTE-Photo"
    if course_code == "ALS21TP":
        return "CTE-Photo"
    if course_code == "ABS11":
        return "CTE-FMM"
    if course_code[0] == "A":
        return "CTE-AD"
    else:
        return "check"


import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from reportlab.platypus import Image, PageBreak


def return_schoolwide_graph(df, plot_formatting_data):
    color_discrete_sequence = [
        # "#000000",
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
    avg_score = plot_formatting_data["avg_score"]
    

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

    if (100 - avg_five_val) > avg_score * 20:
        avg_five_annotation_position = "bottom right"
        avg_score_annotation_position = "bottom left"
    else:
        avg_five_annotation_position = "bottom left"
        avg_score_annotation_position = "bottom right"

    fig.add_vline(
        x=100 - avg_five_val,
        line_width=4,
        line_dash="dash",
        line_color="red",
        annotation_text=f"{avg_five_val:.0f}%",
        annotation_position=avg_five_annotation_position,
        annotation_textangle=-90,
        showlegend=True,
        name="Avg 5! %",
    )

    fig.add_vline(
        x=avg_score * 20,
        line_width=4,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"{avg_score:.1f}",
        showlegend=True,
        name="Avg Mark",
        annotation_position=avg_score_annotation_position,
        annotation_textangle=-90,
    )

    fig.update_layout(
        template="simple_white",
        margin=dict(l=75, r=75, t=50, b=25),
        height=scale * y_aspect,
        width=scale * x_aspect,
        # yaxis_visible=False,
        # yaxis_showticklabels=False,
        yaxis_title="",
        xaxis_visible=False,
        xaxis_showticklabels=False,
        title=dict(
            x=0.5,  # Center the title horizontally (0 is left, 1 is right)
            y=0.98,  # Adjust vertical position (0 is bottom, 1 is top)
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
        insidetextanchor="middle",
        cliponaxis=False,
        marker_line_width=2,
        marker_line_color="grey",
        width=0.55,
    )

    for trace in fig.data:
        if trace.name == "5!":
            trace.textposition = "outside"

    fig.add_trace(
        go.Scatter(
            x=20 * df["WeightedAvg"],
            y=df["y"],
            text=df["WeightedAvg"].apply(lambda x: round(x, 1)),
            mode="markers+text",
            textposition="middle center",
            textfont=dict(size=10),
            marker=dict(
                size=20,
                symbol="square",
                color="white",
                line=dict(width=1, color="black"),
            ),
            name="Avg",
        )
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
        topMargin=0.1 * inch,
        leftMargin=0.1 * inch,
        rightMargin=0.1 * inch,
        bottomMargin=0.1 * inch,
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
