import pandas as pd #

import app.scripts.utils as utils
import datetime as dt
import os

files_df = utils.return_dataframe_of_files()

def generate_class_list(data):

    year_and_semester = data["year_and_semester"]

    cr_1_01_df = utils.return_most_recent_report(files_df, "1_01")

    print(cr_1_01_df)

    return True

    filename = 'class_lists'
    filename = f"{dt.today().strftime('%Y-%m-%d')}_{filename}"

    path = os.path.join(app.root_path, f"data/{year_and_semester}/class_lists")
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
    filename = os.path.join(path, filename)
