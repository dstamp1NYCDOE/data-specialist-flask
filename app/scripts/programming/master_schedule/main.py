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

    # for academic_dept in ['Spanish','Math','Science','SS','ELA']:
    for academic_dept in ['PE','ELA','CTE','Science']:
        output_list.extend(process_course_list.main(academic_dept))
        # output_list.extend(process_half_credit.main(academic_dept))

    # for academic_dept in ['CTE']:
    #     output_list.extend(process_cte_dept.main('CTE'))
    #     output_list.extend(process_half_credit.main(academic_dept))

    # output_list.extend(process_pe_dept.main('PE'))
    output_list.extend(process_functional_dept.main())

    ## Exam Book
    # output_list.extend(exam_book.main())

    ## Hard Coded
    output_list.extend(process_functional_dept.return_hard_coded())

    output_df = pd.DataFrame(output_list)
    output_df = output_df.sort_values(by=['CourseCode','SectionID'])

    ## Combine Teacher Names
    output_df['Teacher Name'] = output_df.apply(utils.return_combined_teacher_names, args=(output_df,), axis=1)
    output_df['Course name'] = ''

    ## convert Cycle Day to string with a leading '
    output_df['Cycle Day'] = output_df['Cycle Day'].apply(lambda x: f"'{x}")

    spreadsheet_id = return_gsheet_url_by_title(gsheets_df, 'master_schedule_planning', year_and_semester=year_and_semester)
    gsheet_utils.set_df_to_dataframe(
        output_df[output_cols], spreadsheet_id, sheet="Output")

    return output_df[output_cols].to_html()

    
