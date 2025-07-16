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
    potential_cuts_df['Comment'] = potential_cuts_df['Comment'].replace(-1, "")
    
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
        

    

    
    ## cuts count 
    num_cuts_df = pd.pivot_table(potential_cuts_df,
                              index=["StudentID"],values=['Pd'],aggfunc='count' ) 
    num_cuts_df.columns = ['#_of_cuts']
    num_cuts_df = num_cuts_df.reset_index()
    

    ## cuts pivot 
    potential_cuts_df['Label'] = potential_cuts_df['Course'].astype(str) + ' (' +potential_cuts_df['ClassGrade'].astype(str) + '%) ' + potential_cuts_df['Teacher'].astype(str) + ' ' + potential_cuts_df['Comment'].astype(str)
    
    cuts_pvt = pd.pivot_table(potential_cuts_df,
                              index=["StudentID","LastName", "FirstName","Counselor"],
        columns=["Pd"],
        values="Label",
        aggfunc="max",
    ).fillna("")
    # cuts_pvt = cuts_pvt.replace(-1, "Potential Cut")
    cuts_pvt = cuts_pvt.reset_index()
    

    cuts_pvt = cuts_pvt.merge(num_cuts_df,on=['StudentID'],how='left')
    cuts_pvt = cuts_pvt.sort_values(by=['#_of_cuts'], ascending=False)

    cuts_pvt_peace_teacher_df = cuts_pvt.copy()

    cuts_pvt_peace_teacher_df['Email'] = cuts_pvt_peace_teacher_df['StudentID'].apply(utils.return_peace_teacher_email)


    # for peace_teacher_email, df in cuts_pvt_peace_teacher_df.groupby('Email'):
        # list_of_posts.append({"to": peace_teacher_email, "message": f"These students may have cut class on {day_of}. Within your capacity for the day, please follow up with as many students as possible. \n{df.head(10).to_html(index=False)}"})
      
    
    list_of_posts.append({"to": 'graschi@schools.nyc.gov', "message": f"These students may have cut class on {day_of}. \n{cuts_pvt_peace_teacher_df.to_html(index=False)}"})

    
    
    ### counselors
    cuts_pvt_counselor_df = cuts_pvt.copy()
    cuts_pvt_counselor_df['Email'] = cuts_pvt_counselor_df['Counselor'].apply(utils.return_counselor_email_address)

    list_of_posts.append({"to": 'lreyes@schools.nyc.gov', "message": f"These students may have cut class on {day_of}. \n{cuts_pvt_counselor_df.to_html(index=False)}"})
    for email_address, df in cuts_pvt_counselor_df.groupby('Email'):
        list_of_posts.append({"to": email_address, "message": f"These students may have cut class on {day_of} because they were marked present in an earlier period. Within your capacity for the day, please follow up with as many students as possible. If these are not cuts and the student was absent for the day, contact the teachers who marked the student present to correct the attendance to absent. \n{df.to_html(index=False)}"})
    


    
    
    # utils.post_to_ms_teams(list_of_posts, method='chat')
    return  cuts_pvt_counselor_df.to_html()

