"""Instantiate a Dash app."""

import numpy as np
import pandas as pd


import dash
from dash import dash_table
from dash import html
from dash import dcc
import dash_daq as daq
import dash_bootstrap_components as dbc  # https://dash-bootstrap-components.opensource.faculty.ai/
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from app.scripts.templates.dashboards.layout import html_layout

import datetime as dt
import os

from app.scripts.attendance.process_RATR import main as process_RATR
import app.scripts.utils as utils


from app.scripts import scripts, files_df


def create_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(
        server=server,
        routes_pathname_prefix="/dashapp/attendance/overall/",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    # Prepare a DataFrame
    period_statistics_df = pd.DataFrame(
        [{"Banana": 1, "Peanuts": 2}, {"Banana": 3, "Peanuts": 4}]
    )

    RATR_filename = utils.return_most_recent_report(files_df, "RATR")
    RATR_df = utils.return_file_as_df(RATR_filename)
    student_attd_df = process_RATR(RATR_df)

    fig = px.histogram(student_attd_df, x="ytd_absence_%")

    # Create Layout
    dash_app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H1("Period Attendance Data Analysis"), width=12),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(html.H2("Student Period Attendance"), width=9),
                                dbc.Col(
                                    create_data_table(
                                        period_statistics_df, "student_data"
                                    ),
                                    width=12,
                                ),
                            ]
                        ),
                        width=12,
                    ),
                    dbc.Col(
                        dcc.Graph(figure=fig),
                    ),
                ]
            )
        ]
    )

    return dash_app.server


def create_data_table(df, id, columnsList=None):
    """Create Dash datatable from Pandas DataFrame."""
    if columnsList:
        columnsList = columnsList
    else:
        columnsList = df.columns.values
    table = dash_table.DataTable(
        style_data={"overflow": "hidden", "textOverflow": "ellipsis", "maxWidth": 0},
        id=id,
        columns=[{"name": i, "id": i} for i in columnsList],
        data=df[columnsList].to_dict("records"),
        fixed_rows={"headers": True},
        sort_action="native",
        sort_mode="native",
        filter_action="native",
        page_size=25,
        export_format="xlsx",
        # fixed_rows={'headers': True},
    )
    return table
