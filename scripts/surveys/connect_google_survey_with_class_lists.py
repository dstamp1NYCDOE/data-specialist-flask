import pandas as pd
import .utils as utils

files_df = utils.return_dataframe_of_files()

def connect_google_survey_with_class_lists(data):
    year_and_semester = data['year_and_semester']
    gsheet_url = data['gsheet_url']

    cr_1_01_df = utils.return_most_recent_report_by_semester('1-01',year_and_semester)
    print(cr_1_01_df)

    return True


if __name__ == '__main__':
    data = {
        'year_and_semester':'2023-2',
        'gsheet_url':'https://docs.google.com/spreadsheets/d/1rV0Yk7rw33RtzDU71FjJ70E_y82f-2QdBlxolmWasnI/edit?resourcekey#gid=120356711'
    }
    connect_google_survey_with_class_lists(data)