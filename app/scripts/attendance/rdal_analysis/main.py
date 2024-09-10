import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session, redirect, url_for




def main(form, request):
    filename = request.files[form.rdal_file.name]
    class_date = form.class_date.data
    rdal_df = process_rdal_csv_and_save(filename, class_date)





    f = return_rdal_report(class_date, rdal_df)

    download_name = f"RDAL_{class_date}.csv"

    
    return f, download_name

def return_rdal_report(date_str, rdal_df):
    absent_students_lst = rdal_df["STUDENT ID"]

    

    f = BytesIO()
    rdal_df.to_excel(f, index=False)
    f.seek(0)

    return f


def process_rdal_csv_and_save(filename, class_date):

    rdal_df = pd.read_csv(filename, skiprows=2, skipfooter=1)
    rdal_df["Date"] = class_date

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = f"{year_and_semester}_{class_date}_RDAL.xlsx"

    path = os.path.join(current_app.root_path, f"data/{year_and_semester}/RDAL")
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    full_filename = os.path.join(path, filename)

    rdal_df.to_excel(full_filename, index=False)

    return rdal_df
