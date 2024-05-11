from flask import session

import pandas as pd
from sklearn.linear_model import LinearRegression

import app.scripts.utils as utils
from app.scripts import scripts, files_df


def main():

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    grades_df = utils.return_file_as_df(filename)
