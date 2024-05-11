import datetime as dt
from io import BytesIO


import pandas as pd

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main(data):
    term = data['form']['marking_period']
    semester, marking_period = term.split('-')

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    grades_df = utils.return_file_as_df(filename)
    
    ## keep grades from current semester
    grades_df = grades_df[grades_df['Term']==semester]
    ## drop courses with no grades
    grades_df = grades_df.dropna(subset=['Pct'])
    ## determine failing classes
    grades_df['failing?'] = grades_df['Pct'] < 65

    ## drop non-credit-bearing-classes
    grades_df = grades_df[~grades_df['Course'].str[0].isin(['G'])]

    #grades_pvt 
    grades_pvt = pd.pivot_table( 
        grades_df, index=['StudentID'], columns='failing?', values='Pct', aggfunc='count'
    ).fillna(0).reset_index()

    ## student's passing zero class
    students_failing_all_classes =  grades_pvt[grades_pvt[False]==0]['StudentID']
    

    students_df = grades_df[(grades_df['StudentID'].isin(students_failing_all_classes)) & (grades_df['failing?'])]

    filename = utils.return_most_recent_report(files_df, "1_49")
    cr_1_49 = utils.return_file_as_df(filename)
    cr_1_49 = cr_1_49[['StudentID','LastName','FirstName','Counselor']]
    
    students_df = cr_1_49[cr_1_49['StudentID'].isin(students_failing_all_classes)]

    ## process assignments
    filename = utils.return_most_recent_report(files_df, "assignments")
    assignments_df = utils.return_file_as_df(filename)
    # Keep Assignments from Marking Period
    assignments_df = assignments_df[assignments_df['Term']==term]
    # keep just assignments from relevant students
    assignments_df = assignments_df[assignments_df['StudentID'].isin(students_failing_all_classes)]
    # keep assignments less than passing
    assignments_df = assignments_df[assignments_df['Percent'] < 65]
    ## drop duplicates due to mutliple objectives
    assignments_df = assignments_df.drop_duplicates(subset=['StudentID','Course','Assignment','DueDate'])
    assignments_df = assignments_df.sort_values(by=['Category','Missing','WorthPoints'], ascending=[True,True,False])
    
    assignments_df = assignments_df.merge(grades_df, on=['StudentID','Course'], how='left').dropna(subset=['Pct'])
    

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    students_df.to_excel(writer, sheet_name='StudentFailingAllClasses', index=False)
    
    table_cols = ['Teacher','Course','Pct','Assignment','Category','DueDate','RawScore','WorthPoints']
    for index, student in students_df.iterrows():
        first_name = student['FirstName']
        last_name = student['LastName']
        StudentID = student['StudentID']
        sheet_name = f"{last_name} {first_name[0]}"
        df = assignments_df[assignments_df['StudentID']==StudentID]
        df[table_cols].to_excel(writer, sheet_name=sheet_name, index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 0)
        worksheet.autofit()

    writer.close()

    f.seek(0)

    return f