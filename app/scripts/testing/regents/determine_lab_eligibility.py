import pandas as pd
import numpy as np
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import session

from io import BytesIO
import os

from flask import current_app

def main():
    year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_42_df = utils.return_file_as_df(filename)
    
    filename = utils.return_most_recent_report(files_df, "1_01")
    cr_1_01_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)

    year_and_semester = f"{year}-{term}"
    
    filename = f"{year_and_semester}_9999-12-31_lab-eligibility.xlsx"

    path = os.path.join(
        current_app.root_path, f"data/{year_and_semester}/lab-eligibility"
    )
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    
    filename = os.path.join(path, filename)

    writer = pd.ExcelWriter(filename)
    cr_1_08_df.to_excel(writer, index=False, sheet_name='1_08')
    cr_1_01_df.to_excel(writer, index=False, sheet_name='1_01')

    writer.close()




    return open(filename,"rb")