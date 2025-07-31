import pandas as pd 
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.date_to_marking_period import return_mp_from_date

def return_candidates():
    school_year = session["school_year"]

    term = session["term"]

    ## Analyze attendance
    jupiter_attd_filename = utils.return_most_recent_report(files_df, "jupiter_period_attendance")
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)
    attendance_marks_df["Date"] = pd.to_datetime(attendance_marks_df["Date"])
    attendance_marks_df["Term"] = attendance_marks_df["Date"].apply(return_mp_from_date, args=(school_year,))
    attendance_marks_df = attendance_marks_df[attendance_marks_df["Term"].str[1]==str(term)]

    ##Analyze Assignments
    filename = utils.return_most_recent_report(files_df, "assignments")
    assignments_df = utils.return_file_as_df(filename)
    # keep assignments from current semester
    assignments_df = assignments_df[assignments_df["Term"].str[1]==str(term)]
    # keep assignments in a category
    CATEGORIES = ['Practice','Performance']
    assignments_df = assignments_df[assignments_df['Category'].isin(CATEGORIES)]

    ## drop extra rows where the assignment was scored objectives separately.
    subset = ['StudentID','Teacher','Course','Section','Assignment','Category','DueDate']
    assignments_df = assignments_df.drop_duplicates(subset=subset)

    ## pvt on missing assignments 

    assignment_pvt = pd.pivot_table( 
        assignments_df,index=['StudentID','Course','Term'], columns=['Category','Missing'],values='WorthPoints',aggfunc='sum'
    ).fillna(0)
    assignment_pvt[('Performance','Total')] = assignment_pvt[('Performance','Y')] + assignment_pvt[('Performance','N')]
    assignment_pvt[('Practice','Total')] = assignment_pvt[('Practice','Y')] + assignment_pvt[('Practice','N')]
    assignment_pvt[('Performance','%_missing')] = assignment_pvt[('Performance','Y')] / assignment_pvt[('Performance','Total')]
    assignment_pvt[('Practice','%_missing')] =  assignment_pvt[('Practice','Y')] /  assignment_pvt[('Practice','Total')]

    assignment_pvt['missing_more_than_50%_of_performance'] = assignment_pvt[('Performance','%_missing')] >0.5

    assignment_pvt = assignment_pvt.reset_index()
    ## pivot on benchmark

    at_risk_by_students_by_term = pd.pivot_table(assignment_pvt, index=['StudentID','Term'], columns='missing_more_than_50%_of_performance', values='Course',aggfunc='count').fillna(0)
    # at_risk_by_students_by_term.columns = ['_'.join(col) for col in at_risk_by_students_by_term.columns]

    return at_risk_by_students_by_term.reset_index()