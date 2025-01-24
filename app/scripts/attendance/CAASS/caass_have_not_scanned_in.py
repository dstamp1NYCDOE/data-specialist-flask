from io import BytesIO
import pandas as pd
import datetime as dt
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df


def main(form, request):
    f = BytesIO()

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    CAASS_file = request.files[
        form.CAASS_file.name
    ]
    CAASS_df = pd.read_csv(CAASS_file)    


    students_present = CAASS_df['Student ID']

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[['StudentID','LastName','FirstName','Student DOE Email']]

    students_not_scanned_in_yet_df = student_info_df[student_info_df['StudentID'].isin(students_present)]

    print(students_not_scanned_in_yet_df)