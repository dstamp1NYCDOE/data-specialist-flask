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
import app.scripts.utils.utils as utils
import pandas as pd

from app.scripts.attendance.jupiter.process import process_local_file as process_jupiter


def main(form, request):
    week_number = form.week_of.data

    student_period_attendance_df = process_jupiter(week_number)

    start_date = min(student_period_attendance_df["Date"])
    end_date = max(student_period_attendance_df["Date"])
    dates_covered_by_report = student_period_attendance_df["Date"].unique()


    attendance_errors_df = student_period_attendance_df[
        student_period_attendance_df["attd_error"]
    ]
    cols = [
        "Teacher",
        "Date",
        "Course",
        "Section",
        "Pd",
        "Type",
        "LastName",
        "FirstName",
    ]
    attendance_errors_df = attendance_errors_df[cols].sort_values(
        by=["Teacher", "Pd", "Course", "Section"]
    )

    

    filename = utils.return_most_recent_report(files_df, "JupiterStaff")
    jupiter_staff_df = utils.return_file_as_df(filename)

    attendance_errors_df = attendance_errors_df.merge(
        jupiter_staff_df[['Teacher','Email']],
        on="Teacher",
        how="left",
    )
    
    list_of_posts = []
    output_cols = [
        "Date",
        "Pd",
        "Course",
        "Section",
        "LastName",
        "FirstName",
        "Type",
    ]
    for (teacher, teacher_email), df in attendance_errors_df.groupby(['Teacher','Email']):
        list_of_posts.append({"to": teacher_email, "message": f"Possible Jupiter Attendance errors for {teacher} for the week of {start_date} to {end_date}. Please review your attendance records for the following students who were only marked present/late in your class organized by period:\n{df[output_cols].to_html(index=False)}"})

    utils.post_to_ms_teams(list_of_posts, method='chat')

    return  attendance_errors_df.to_html()

