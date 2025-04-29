from PyPDF2 import PdfMerger

from io import BytesIO

from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate
import PyPDF2

from app.scripts import scripts, files_df
import app.scripts.utils as utils
import pandas as pd
from flask import session 

from app.scripts.attendance.jupiter.process import process_local_file as process_jupiter


def main(form, request):
    day_of = form.day_of.data
    
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    student_period_attendance_df = utils.return_file_as_df(jupiter_attd_filename)
    
    student_period_attendance_df = student_period_attendance_df[student_period_attendance_df['Date']== day_of]
    students_on_trips_df = student_period_attendance_df[student_period_attendance_df['Attendance']=='T']

    

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)


    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName"]]
    
    students_on_trips_df = students_on_trips_df.merge(students_df, on=['StudentID'], how='left')
    

    

    filename = utils.return_most_recent_report(files_df, "JupiterStaff")
    jupiter_staff_df = utils.return_file_as_df(filename)

    students_on_trips_df = students_on_trips_df.merge(
        jupiter_staff_df[['Teacher','Email']],
        on="Teacher",
        how="left",
    )
    
    list_of_posts = []
    output_cols = [
        "Course",'Section','Period',
        "LastName",
        "FirstName",
        "Comment",
    ]
    for (teacher, teacher_email), df in students_on_trips_df.groupby(['Teacher','Email']):
        
        list_of_posts.append({"to": teacher_email, "message": f"Dear {teacher}, The following students have been excused for a trip in Jupiter for {day_of}.\n{df[output_cols].to_html(index=False)}"})
        

    utils.post_to_ms_teams(list_of_posts, method='chat')

    summary_pvt = pd.pivot_table(students_on_trips_df,index=['StudentID', 'LastName', 'FirstName'],columns=['Period'],values='Type',aggfunc='count')
    return  summary_pvt.to_html()

