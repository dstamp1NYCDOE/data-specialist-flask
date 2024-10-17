import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from io import BytesIO

from datetime import timedelta
from reportlab.lib.units import mm, inch
from reportlab.platypus import Image


def get_time_hh_mm_ss_short(sec):
    td_str = str(timedelta(seconds=sec))
    x = td_str.split(':')
    return f"{x[0]} hrs, {x[1]} min"

def get_time_hh_short(sec):
    td_str = str(timedelta(seconds=sec))
    x = td_str.split(':')
    if int(x[0]) == 1:
        return '1 hr'
    return f"{x[0]} hrs"

def main(student_passes_df):
    y_aspect = 400
    x_aspect = 700

    dfg=student_passes_df[['Destination','Duration (sec)']].groupby('Destination').sum().reset_index()
    dfg['text'] = dfg['Duration (sec)'].apply(get_time_hh_mm_ss_short)
    dfg['Duration (hh:mm)'] = dfg['Duration (sec)']

    max_duration = dfg['Duration (sec)'].max()
    x_tickvals = [i*60*60 for i in range(1,100) if i*60*60 <= max_duration+60*60]
    x_ticktext = [get_time_hh_short(x) for x in x_tickvals]


    fig = px.bar(dfg,
             y='Destination',
             x='Duration (hh:mm)',
             text = 'text',
             orientation='h',
             #color='Items',
             barmode='stack')

    scale = 1.25
    fig.update_layout(
        template="simple_white",
        margin=dict(l=0, r=0, t=0, b=0),
        height=scale * y_aspect,
        width=scale * x_aspect,
        xaxis_tickmode = 'array',
        xaxis_tickvals=x_tickvals,
        xaxis_ticktext=x_ticktext,      
    )

    buffer = BytesIO()
    pio.write_image(fig, buffer)
    I = Image(buffer)
    I.drawHeight = y_aspect / x_aspect * 6 * inch
    I.drawWidth = x_aspect / x_aspect * 6 * inch

    return I
