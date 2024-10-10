import pandas as pd
import numpy as np
import os
from io import BytesIO
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df, gsheets_df

from flask import current_app, session, redirect, url_for

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    attendance_flowables = return_attendance_flowables(year_and_semester)

    flowables = attendance_flowables



    download_name = "2024-2025_DataSpecialistProject_Artifacts.pdf"
    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=1 * inch,
        leftMargin=1.5 * inch,
        rightMargin=1.5 * inch,
        bottomMargin=1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f, download_name 


def return_attendance_flowables(year_and_semester):
    jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
    
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )

    ## keep period 1&2 only
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Pd'].isin([1,2])]        
    ## Drop z codes
    attendance_marks_df = attendance_marks_df[attendance_marks_df['Course'].str[0]!='Z']  

    attendance_by_teacher_pvt = pd.pivot_table(
        attendance_marks_df,
        index=["Teacher",'Course','Pd','Section'],
        columns="Type",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)

    attendance_by_teacher_pvt['tardy_%'] =100* attendance_by_teacher_pvt['tardy'] / (attendance_by_teacher_pvt['tardy'] + attendance_by_teacher_pvt['present'] )
    attendance_by_teacher_pvt['tardy_%'] = attendance_by_teacher_pvt['tardy_%'].astype(int)



    attendance_by_teacher_pvt = attendance_by_teacher_pvt.reset_index()
    attendance_by_teacher_pvt = attendance_by_teacher_pvt.sort_values(by=['Pd','tardy_%'])

    attendance_by_teacher_pvt_T = utils.return_df_as_table(attendance_by_teacher_pvt)

    return [attendance_by_teacher_pvt_T]