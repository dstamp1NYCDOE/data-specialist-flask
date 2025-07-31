import pandas as pd
import datetime as dt
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO

from flask import session

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    student_subset_title = form.subset_title.data

    student_lst_str = form.subset_lst.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[['StudentID','LastName','FirstName']]
    student_info_df['FullName'] = student_info_df['LastName'] + ', ' + student_info_df['FirstName']

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()
    rosters_df = rosters_df[rosters_df["StudentID"].isin(student_lst)]

    filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule", year_and_semester=year_and_semester)
    master_schedule = utils.return_file_as_df(filename).fillna('')
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1","Teacher2", "Period"]
    ]
    master_schedule['Floor'] = master_schedule['Room'].apply(return_floor_from_room_number)
    

    df = rosters_df.merge(master_schedule, on=["Course", "Section"], how='left').fillna('')
    df = df.merge(student_info_df, on='StudentID', how='left')

             

    ## periods
    periods = form.periods.data
    
    if 'ALL' in periods:
        periods = [1,2,3,4,5,6,7,8,9]
    else:
        periods = [x for x in periods if x!='ALL']
        period_regex_match = ''.join(periods)
        df = df[df['Period'].str.contains(f"[{period_regex_match}]")]

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    list_of_dfs = []
    for period in periods:
        dff = df[df['Period'].str.contains(f"[{period}]")]

        dff_pvt = pd.pivot_table(dff, index=['Floor','Room','Teacher1'], values='FullName', aggfunc=lambda x: '\n'.join(x))
        dff_pvt = dff_pvt.reset_index()
        dff_pvt.insert(0,'Period','')
        dff_pvt['Period'] = period
        dff_pvt.to_excel(writer, sheet_name=f'P{period}', index=False)
        list_of_dfs.append(dff_pvt)

    enhanced_line_schedule_df = pd.concat(list_of_dfs)
    enhanced_line_schedule_df.to_excel(writer, sheet_name='Enhanced Line Schedule', index=False)

    ## list by teacher
    
    for teacher, students_by_teacher_df in enhanced_line_schedule_df.groupby('Teacher1'):
        students_by_teacher_df.to_excel(writer, sheet_name=teacher, index=False)
        


    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()            
    
    writer.close()
    f.seek(0)

    
    
    
    student_subset_title = form.subset_title.data
    download_name = (
        f"enhanced_line_schedule_{student_subset_title}_{dt.datetime.today().strftime('%Y-%m-%d')}.xlsx"
    )

    # return ''
    return f, download_name


def return_floor_from_room_number(room_number):
    if room_number > 999:
        return 10
    else:
        return int(str(room_number)[0])