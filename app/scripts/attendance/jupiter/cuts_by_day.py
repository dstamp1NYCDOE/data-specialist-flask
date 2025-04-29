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

    student_period_attendance_df = process_jupiter(day_of=day_of)
    
    potential_cuts_df = student_period_attendance_df[
        student_period_attendance_df["cutting?"]
    ]

    
    filename = utils.return_most_recent_report(files_df, "JupiterStaff")
    jupiter_staff_df = utils.return_file_as_df(filename)

    potential_cuts_df = potential_cuts_df.merge(
        jupiter_staff_df[['Teacher','Email']],
        on="Teacher",
        how="left",
    )
    
    list_of_posts = []
    output_cols = [
        "Course",'Section','Period',
        "LastName",
        "FirstName",
        "enhanced_mark",
        "Comment",
    ]
    for (teacher, teacher_email), df in potential_cuts_df.groupby(['Teacher','Email']):
        list_of_posts.append({"to": teacher_email, "message": f"Dear {teacher}, These students were marked present or tardy in at least two periods during the day {day_of}. It is possible they (1) were incorrectly marked present or tardy on this day or (2) cut class, arrived late, left early, or were in another location for the duration of the period. Please confirm your attendance records and speak with student about their location if they were not in class. As necessary, update their attendance from A to E for excused. Log any interactions in the dashboard. If you determine the student was cutting, take appropriate action --- update their attendance from A to C for cut --- and, if this is a repeat offense, submit a discipline referral.\n{df[output_cols].to_html(index=False)}"})
        

    utils.post_to_ms_teams(list_of_posts, method='chat')

    return  potential_cuts_df.to_html()

