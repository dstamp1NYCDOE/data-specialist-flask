import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session

from app.scripts.summer.testing.regents_organization import utils as regents_organization_utils

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = f"{month}_{school_year+1}_Student_Exam_Grid.xlsx"

    cr_1_08_df = regents_organization_utils.return_processed_registrations()
    f = BytesIO()
    writer = pd.ExcelWriter(f)

    for day, registrations_by_day in cr_1_08_df.groupby('Day'):
        day_pvt = pd.pivot_table(registrations_by_day,index=['LastName','FirstName','StudentID','Sending school'], columns=['Time','ExamTitle'],values='Room',aggfunc='max').fillna('').reset_index()
        day_pvt.to_excel(writer, sheet_name=day.split(',')[1])

    for (hub_location, day, time), registrations_by_hub_by_day_by_time in cr_1_08_df.groupby(['hub_location','Day','Time']):
        day_pvt = pd.pivot_table(registrations_by_hub_by_day_by_time,index=['LastName','FirstName','StudentID','Sending school'], columns=['Time','ExamTitle'],values='Room',aggfunc='max').fillna('').reset_index()
        sheet_name = f"{hub_location} - {day.split(',')[1]} - {time}"
        day_pvt.to_excel(writer, sheet_name=sheet_name)


    for dbn, registrations_by_dbn in cr_1_08_df.groupby('Sending school'):
        dbn_pvt = pd.pivot_table(registrations_by_dbn,index=['LastName','FirstName','StudentID'], columns=['Day','Time','ExamTitle'],values='Room',aggfunc='max').fillna('').reset_index()
        dbn_pvt.to_excel(writer, sheet_name=dbn)


    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(3, 3)
        worksheet.autofit()



    cr_1_08_df.to_excel(writer)
    writer.close()
    f.seek(0)

    return f, filename