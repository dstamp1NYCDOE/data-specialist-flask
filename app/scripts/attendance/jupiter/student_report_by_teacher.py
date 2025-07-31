import pandas as pd 
from flask import session
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import files_df

from app.scripts.attendance.jupiter import process as process_jupiter_data


def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}" 

    attendance_marks_df = process_jupiter_data.main()
    filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule", year_and_semester=year_and_semester)
    master_schedule = utils.return_file_as_df(filename).fillna('')
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1","Teacher2", "Period"]
    ]
    attendance_marks_df = attendance_marks_df.merge(master_schedule, on=["Course", "Section"], how='left').fillna('')
    

    attendance_marks_df['AttdMark'] = attendance_marks_df.apply(return_enhanced_attd_mark, axis=1)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)

    cr_3_07_df = cr_3_07_df[
        [
            "StudentID",
            "ParentLN",
            "ParentFN",
            "Phone",

        ]
    ]

    attendance_marks_df = attendance_marks_df.merge(cr_3_07_df, on=["StudentID"], how='left').fillna('')     


    f = BytesIO()
    writer = pd.ExcelWriter(f)
    workbook = writer.book

    cut_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006",'bold': True, 'border':1})
    absent_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    present_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})    
    late_format = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
    late_to_school_format = workbook.add_format({"bg_color": "#CFA500", "font_color": "#FFEB9C",'bold': True, 'border':1})
    excused_format = workbook.add_format({"bg_color": "#2546f0", "font_color": "#FFFFFF"})    

    teachers_lst = pd.unique(attendance_marks_df[["Teacher1", "Teacher2"]].values.ravel("K"))
    teachers_lst = [teacher for teacher in teachers_lst if teacher!='']
    teachers_lst.sort()

    # df.to_excel(writer, sheet_name='combined', index=False)    

    for teacher in teachers_lst:
        
        students_df = attendance_marks_df[(attendance_marks_df['Teacher1']==teacher) | (attendance_marks_df['Teacher2']==teacher)]
        students_pvt = pd.pivot_table(students_df, index=['StudentID','LastName','FirstName','Course','Pd','Section',            "ParentLN",
            "ParentFN",
            "Phone",], columns='Date',values='AttdMark', aggfunc='max')
        students_pvt = students_pvt.reset_index()

        # students_pvt = students_pvt.merge(students_df, left_on=['StudentID','Course','Section'], right_on=['StudentID','Course','Section'], how='left')
        

        student_stats_pvt = pd.pivot_table(students_df, index='StudentID',columns='AttdMark', values='Date',aggfunc='count')
        student_stats_pvt = student_stats_pvt.reset_index().fillna(0)
        

        
        df = student_stats_pvt.merge(students_pvt, on='StudentID', how='left')

        if 'potential cut' in df.columns:
            df = df.sort_values(by=['potential cut'], ascending=[False])


        ## reorder columns
        leading_cols = ['StudentID','LastName','FirstName',"ParentLN","ParentFN","Phone",'Course','Section','Pd']
        df = df[[c for c in leading_cols if c in df]+[c for c in df if c not in leading_cols]]


        df.to_excel(writer, sheet_name=teacher, index=False)



    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()
        end_col_str = 'AZ300'
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"potential cut"',
                                            'format':   cut_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"unexcused"',
                                            'format':   absent_format})        
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"present"',
                                            'format':   present_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"tardy"',
                                            'format':   late_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"potential late to school"',
                                            'format':   late_to_school_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    '"excused"',
                                            'format':   excused_format})
                
    writer.close()
    f.seek(0)
    download_name = f"EnhancedPeriodAttendanceByTeacher.xlsx"

    return f, download_name



def return_enhanced_attd_mark(student_row):
     
    attd_type = student_row['Type']
    potential_cut = student_row['potential_cut']
    first_period_present = student_row['first_period_present']
    class_period = student_row['Pd']

    if potential_cut:
        if class_period > first_period_present:
            return 'potential cut'
        else:
            return 'potential late to school'
    else:
        return attd_type