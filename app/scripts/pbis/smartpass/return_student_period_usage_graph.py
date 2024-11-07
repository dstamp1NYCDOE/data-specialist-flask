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

def main(student_row):
    y_aspect = 400
    x_aspect = 900

    

    y = ['Pd-1','Pd-2','Pd-3','Pd-4','Pd-5','Pd-6','Pd-7','Pd-8','Pd-9']
    
    x = [student_row[1.0],student_row[2.0],student_row[3.0],student_row[4.0],student_row[5.0],student_row[6.0],student_row[7.0],student_row[8.0],student_row[9.0]]
    
    text = [get_time_hh_mm_ss_short(x) for x in x[::-1]]
    data = [go.Bar(x=x[::-1],y=y[::-1], text=text, orientation='h')]
    fig = go.Figure(data=data)

    x_tickvals = [i*30*60 for i in range(1,100) if i*30*60 <= max(x)+30*60]
    x_ticktext = [get_time_hh_mm_ss_short(x) for x in x_tickvals]

    scale = 0.75

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
