import pandas as pd

import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.process_course_list as process_course_list
import app.scripts.programming.master_schedule.process_cte_dept as process_cte_dept
import app.scripts.programming.master_schedule.process_pe_dept as process_pe_dept
import app.scripts.programming.master_schedule.process_half_credit as process_half_credit
import app.scripts.programming.master_schedule.process_functional_dept as process_functional_dept
import app.scripts.programming.master_schedule.exam_book as exam_book

import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids
import app.scripts.programming.master_schedule.gsheet_utils as gsheet_utils
import app.scripts.programming.master_schedule.identify_irresolvables as identify_irresolvables

from app.scripts.programming.master_schedule.utils import output_cols

from app.scripts import gsheets_df

from flask import session

from app.scripts.utils.utils import return_gsheet_url_by_title

def main():

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    output_list = []

    for academic_dept in ['Spanish','Math','Science','SS','ELA']:
        output_list.extend(process_course_list.main(academic_dept))
        output_list.extend(process_half_credit.main(academic_dept))

    for academic_dept in ['CTE']:
        output_list.extend(process_cte_dept.main('CTE'))
        output_list.extend(process_half_credit.main(academic_dept))
    output_list.extend(process_pe_dept.main('PE'))
    output_list.extend(process_functional_dept.main())

    ## Exam Book
    output_list.extend(exam_book.main())

    ## Hard Coded
    output_list.extend(process_functional_dept.return_hard_coded())

    output_df = pd.DataFrame(output_list)
    output_df = output_df.sort_values(by=['CourseCode','SectionID'])

    ## insert room grid
    room_grid_df = utils.return_master_schedule_by_sheet('RoomLookups').set_index('Teacher Name')
    room_grid_dict = room_grid_df.to_dict('index')
    output_df['Room'] = output_df.apply(utils.return_room_by_teacher_by_period, args=(room_grid_dict,), axis=1)
    output_df['Teacher Name'] = output_df.apply(utils.return_combined_teacher_names, args=(output_df,), axis=1)
    output_df['Course name'] = ''

    ## identify if the value should be added
    output_df['to_count'] = output_df.apply(to_count,axis=1)
    output_cols.append('to_count')
    spreadsheet_id = return_gsheet_url_by_title(gsheets_df, 'master_schedule_planning', year_and_semester=year_and_semester)
    gsheet_utils.set_df_to_dataframe(
        output_df[output_cols], spreadsheet_id, sheet="Output")

    # identify_irresolvables.main(filename)

    return output_df[output_cols].to_html()

def to_count(course_row):
    CourseCode = course_row['CourseCode']
    MappedCourse = course_row['Mapped Course']
    CycleDay = course_row['Cycle Day']
    is_tuesday = CycleDay[2] == '1'
    is_not_mapped = MappedCourse == ''

    return is_tuesday and is_not_mapped
    
