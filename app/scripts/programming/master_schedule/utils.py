import numpy as np
import pandas as pd
import xlrd

from dotenv import load_dotenv
load_dotenv()

import pygsheets
import app.scripts.programming.master_schedule.gsheet_utils as gsheet_utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids


gc = pygsheets.authorize(service_account_env_var = "GDRIVE_API_CREDENTIALS")


def return_master_schedule_by_sheet(sheet_name):
    spreadsheet_id = spreadsheet_ids.master_schedule_planning
    df = gsheet_utils.return_google_sheet_as_dataframe(spreadsheet_id,sheet=sheet_name)
    df = df.fillna('')
    if 'department' in df.columns:
        df = df[df['department'] != '']
    return df


def return_room_by_teacher_by_period(master_row, room_grid_dict):
    period_key = f"Period{master_row['PeriodID']}"
    teacher_name = master_row['Teacher Name']
    default_room = master_row['Room']

    if room_grid_dict.get(teacher_name):
        if room_grid_dict.get(teacher_name).get(period_key) != '':
            return room_grid_dict.get(teacher_name).get(period_key)
    else:
        return default_room


def return_combined_teacher_names(master_row, output_df):
    PeriodID = master_row['PeriodID']
    SectionID = master_row['SectionID']
    Room = master_row['Room']
    Teacher_Name = master_row['Teacher Name']

    mask = (output_df['PeriodID'] == PeriodID) & (output_df['SectionID'] == SectionID) & (output_df['Room'] == Room)

    list_of_teachers = output_df[mask]['Teacher Name'].unique()
    if len(list_of_teachers) == 2:
        return convert_list_of_names_to_coteachers(list_of_teachers)
    return Teacher_Name


def convert_list_of_names_to_coteachers(list_of_names):
    output_list = []
    for name in list_of_names:
        last_name = name.split()[0]
        output_list.append(last_name)
    return ' '.join(output_list)


output_cols = [
    'SchoolDBN',
    'SchoolYear',
    'TermID',
    'CourseCode',
    'SectionID',
    'Course name',
    'PeriodID',
    'Cycle Day',
    'Capacity',
    'Remaining Capacity',
    'Gender',
    'Teacher Name',
    'Room',
    'Mapped Course',
    'Mapped Section',
]