import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

import os
from flask import current_app, session



def main():
    school_year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "1_49")
    students_df = utils.return_file_as_df(filename).fillna({'Counselor':'D75'})

    filename = utils.return_most_recent_report(files_df, "1_08")
    current_registrations_df = utils.return_file_as_df(filename)

    registrations_pvt = pd.pivot_table(current_registrations_df, index='StudentID',columns='Course', values='Section', aggfunc='max')
    registrations_pvt = registrations_pvt.fillna(0)
    registrations_pvt = registrations_pvt.apply(lambda x: x>0)
    registrations_pvt = registrations_pvt.reset_index()
    
    students_df = students_df[['StudentID','LastName','FirstName','Counselor']]

    students_df = students_df.merge(registrations_pvt, on='StudentID',how='left').fillna(False)
    students_df = students_df.sort_values(by=['Counselor','LastName','FirstName'])

    return students_df
    