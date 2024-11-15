import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
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

    df = df.dropna(subset='LastName')

    f = return_download_file(df)

    download_name = f"UniversalScreenerAnalysisByTeacher.pdf"

    return f, download_name


def return_download_file(df):
    for question in ['I feel like I belong at HSFI','I feel like my HSFI classmates care about me','I feel comfortable interacting with other students in my classes','I need help from the school with making friends at HSFI','I need help from the school with learning how to improve my work habits to reach my academic potential']:
        df = df.fillna({question:'no response'})

    teachers_lst = pd.unique(df[["Teacher1", "Teacher2"]].values.ravel("K"))    

    flowables = []
    for teacher in teachers_lst:
        students_df = df[(df['Teacher1']==teacher) | (df['Teacher2']==teacher)].sort_values(by=['Total Net'])
        
        flowables.append(Paragraph(f"{teacher}",styles['Normal'] ))

        top_student_in_class_section = students_df.groupby(['Course','Section']).tail(1)
        top_student_in_class_section['Group'] = 'Top'
        bottom_student_in_class_section = students_df.groupby(['Course','Section']).head(1)
        bottom_student_in_class_section['Group'] = 'Bottom'

        
        
        students_that_dont_feel_like_they_belong = students_df[students_df['I feel comfortable interacting with other students in my classes'].str.contains('Disagree')]
        students_that_dont_feel_like_they_belong['Group'] = 'Bottom'

        students_of_interest_df = pd.concat([top_student_in_class_section,bottom_student_in_class_section,students_that_dont_feel_like_they_belong])

        students_of_interest_df = students_of_interest_df.drop_duplicates(subset='StudentID')
        

        table_cols = ['Group','LastName', 'FirstName', 
                      'Period',
                      'I feel like I belong at HSFI',
       'I feel like my HSFI classmates care about me',
       'I feel comfortable interacting with other students in my classes',
       'I need help from the school with making friends at HSFI',
       'I need help from the school with learning how to improve my work habits to reach my academic potential',
        ]
        
        colWidths = [0.5*inch, 1.25*inch, 1*inch, 0.6*inch] + [1.2*inch]*5
        flowables.append(Paragraph(f"Students of Interest",styles['Heading2'] ))
        T = return_df_as_table(students_of_interest_df, table_cols, colWidths=colWidths)
        flowables.append(T)


        questions_for_graph = [                      'I feel like I belong at HSFI',
       'I feel like my HSFI classmates care about me',
       'I feel comfortable interacting with other students in my classes',
       'I need help from the school with making friends at HSFI',
       'I need help from the school with learning how to improve my work habits to reach my academic potential',]
        id_vars = [x for x in df.columns if x not in questions_for_graph]
        dff = students_df.melt(id_vars=id_vars, var_name="Question", value_name="StudentResponse")
        student_pvt = pd.pivot_table(
            dff,
            index=["Question"],
            columns="StudentResponse",
            values="Counselor",
            aggfunc="count",
        ).fillna(0)  

        I = return_student_survey_responses_by_teacher(student_pvt.reset_index())
        flowables.append(I)
        
        flowables.append(PageBreak())
        

    return build_letters(flowables)

import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
def return_student_survey_responses_by_teacher(df):
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

    

    x_aspect = 600
    y_aspect = 300
    scale = 1.50

    
    x = ["Strongly Disagree","Disagree","Agree","Strongly Agree","no response"]
    for _ in x:
        if _ not in df.columns:
            df[_] = 0

    fig = px.bar(
        df,
        y="Question",
        # title=title,
        x=x,
        text_auto=".0f",
        orientation="h",
        color_discrete_sequence=color_discrete_sequence,
    )

    fig.update_layout(
        template="simple_white",
        margin=dict(l=75, r=75, t=50, b=25),
        height=scale * y_aspect,
        width=scale * x_aspect,
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
        pagesize=landscape(letter),
        topMargin=0.1 * inch,
        leftMargin=0.1 * inch,
        rightMargin=0.1 * inch,
        bottomMargin=0.1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f

def return_df_as_table(df, cols=None, colWidths=None, rowHeights=None):
    if cols:
        table_data = df[cols].values.tolist()
    else:
        cols = df.columns
        table_data = df.values.tolist()
    table_data.insert(0, [Paragraph(col, styles['Normal_small']) for col in cols])
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t