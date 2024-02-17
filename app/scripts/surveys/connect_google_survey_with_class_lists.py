import pandas as pd
from flask import flash

import app.scripts.utils as utils

files_df = utils.return_dataframe_of_files()

def connect_google_survey_with_class_lists(data):
    year_and_semester = data['year_and_semester']
    gsheet_url = data['gsheet_url']

    cr_1_01_filename = utils.return_most_recent_report_by_semester(files_df,'1_01',year_and_semester)
    cr_1_01_df = utils.return_file_as_df(cr_1_01_filename)
    print(cr_1_01_df)

    cr_6_31_filename = utils.return_most_recent_report_by_semester(
        files_df, "6_31", year_and_semester
    )
    cr_6_31_df = utils.return_file_as_df(cr_6_31_filename).dropna()
    print(cr_6_31_df)

    cr_1_01_df = cr_1_01_df.merge(cr_6_31_df, left_on=['Teacher1'], right_on=['NickName'], how='left')
    cr_1_01_df = cr_1_01_df.merge(
        cr_6_31_df, left_on=["Teacher2"], right_on=["NickName"], how="left"
    )

    output_filename = f"data/output.xlsx"
    cr_1_01_df.to_excel(output_filename)

    flash('Report complete', category="success")
    return True
