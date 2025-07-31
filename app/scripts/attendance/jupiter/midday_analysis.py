import datetime as dt
import pandas as pd  #


from io import BytesIO
from flask import session, current_app
import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df


from app.scripts.attendance.jupiter.process import process_uploaded_file as process_jupiter

def main(request, form):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    jupiter_attd_filename = request.files[form.jupiter_attd_file.name]
    jupiter_attd_df = pd.read_csv(jupiter_attd_filename)

    jupiter_attd_df = process_jupiter(jupiter_attd_df)

    date_str = jupiter_attd_df['Date'].max()


    jupiter_rosters_df = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    jupiter_rosters_df = utils.return_file_as_df(jupiter_rosters_df).drop_duplicates(subset=['StudentID','Course','Section'])

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    workbook = writer.book

    cut_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006",'bold': True, 'border':1})
    absent_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    present_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})    
    late_format = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
    late_to_school_format = workbook.add_format({"bg_color": "#CFA500", "font_color": "#FFEB9C",'bold': True, 'border':1})
    excused_format = workbook.add_format({"bg_color": "#2546f0", "font_color": "#FFFFFF"})    

    attd_error = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100",'bold': True, 'border':1})


    # main page stats
    daily_attd_df = jupiter_attd_df.drop_duplicates(subset=['StudentID'], keep='last')
    student_daily_attd_stats = pd.pivot_table(daily_attd_df, index=['overall_late_to_school','in_school?'],values='StudentID',aggfunc='nunique',)
    student_daily_attd_stats.columns = ['#_of_students']
    
    student_daily_attd_stats.to_excel(writer, sheet_name=f"OverallStats")
    
    #by grade level
    for year_in_hs in [1,2,3,4]:
        students_df = jupiter_attd_df[jupiter_attd_df['year_in_hs'] == year_in_hs]
        students_pvt = pd.pivot_table(students_df, index=['StudentID','LastName','FirstName','Counselor','overall_late_to_school','in_school?'], columns='Pd', values='enhanced_mark',aggfunc='max').fillna('').reset_index()
        students_pvt = students_pvt.sort_values(by=['in_school?','overall_late_to_school','LastName','FirstName'])
        students_pvt.to_excel(writer, sheet_name=f"year_in_hs_{year_in_hs}", index=False)

    ## cutting students
    cuts_df = jupiter_attd_df[jupiter_attd_df['cutting?'] == True]

    cuts_pvt = pd.pivot_table(cuts_df, index=['StudentID'], columns='Pd', values='Teacher',aggfunc='max').fillna('').reset_index()
    cuts_count_pvt = pd.pivot_table(cuts_df, index=['StudentID','LastName','FirstName','year_in_hs','Counselor'], values='Pd',aggfunc='count').fillna('').reset_index()
    cuts_count_pvt = cuts_count_pvt.rename(columns={'Pd':'#_of_cuts'})
    cuts_pvt = cuts_count_pvt.merge(cuts_pvt, on='StudentID', how='left')
    cuts_pvt = cuts_pvt.sort_values(by=['#_of_cuts','LastName','FirstName'], ascending=[False,True,True])
    cuts_pvt.to_excel(writer, sheet_name=f"PotentialCuts", index=False)
    worksheet = writer.sheets['PotentialCuts']
    worksheet.freeze_panes(1, 6)
    worksheet.autofit()
    ## return teacher info
    teachers = jupiter_attd_df['Teacher'].sort_values().unique().tolist()
    for teacher in teachers:
        StudentIDs = jupiter_rosters_df[jupiter_rosters_df['Teacher1']==teacher]['StudentID']
        teacher_roster_df = jupiter_rosters_df[jupiter_rosters_df['Teacher1']==teacher][['StudentID','Course','Section',]]
        students_df = jupiter_attd_df[jupiter_attd_df['StudentID'].isin(StudentIDs)]
        students_pvt = pd.pivot_table(students_df, index=['StudentID','LastName','FirstName','overall_late_to_school','in_school?'], columns='Pd', values='enhanced_mark',aggfunc='max').fillna('').reset_index()
        students_pvt = students_pvt.drop_duplicates(subset=['StudentID'], keep='last')
        teacher_roster_df = teacher_roster_df.merge(students_pvt, on='StudentID', how='left').sort_values(by=['Section','Course','LastName','FirstName']).dropna(subset=['LastName'])
        
        teacher_roster_df.to_excel(writer, sheet_name=teacher, index=False)
    
    student_grids = ['year_in_hs_1','year_in_hs_2','year_in_hs_3','year_in_hs_4'] + teachers
    for sheet in student_grids:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 7)
        worksheet.autofit()
        end_col_str = 'Q500'
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'Possible Attd Err',
                                            'format':   attd_error})         
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'potential late to school',
                                            'format':   late_to_school_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'potential cut',
                                            'format':   cut_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'unexcused',
                                            'format':   absent_format})        
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'present',
                                            'format':   present_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'tardy',
                                            'format':   late_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'text',
                                            'criteria': 'containing',
                                            'value':    'excused',
                                            'format':   excused_format})    

        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    'False',
                                            'format':   absent_format})   
        
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    'True',
                                            'format':   late_to_school_format})    

        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    'True',
                                            'format':   present_format})   

    # return ''
    writer.close()
    f.seek(0)

    download_name = f"JupiterMiddayReport-{year_and_semester}-{date_str}.xlsx"
    return f, download_name
