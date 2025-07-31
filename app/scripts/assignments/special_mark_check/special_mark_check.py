from flask import session

import pandas as pd

from io import BytesIO
import datetime as dt
import app.scripts.utils as utils
from app.scripts import scripts, files_df


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    grades_df = utils.return_file_as_df(filename)

    ## assignments
    filename = utils.return_most_recent_report_by_semester(files_df, "assignments",year_and_semester=year_and_semester)
    assignments_df = utils.return_file_as_df(filename)

    assignments_df = assignments_df[assignments_df["Course"] != ""]

    # drop assignments worth zero
    assignments_df = assignments_df.dropna(subset=["RawScore"])
    assignments_df = assignments_df[assignments_df["WorthPoints"] != 0]

    # drop assignments not graded yet
    not_graded_marks = ["NG", "Ng", "ng"]
    assignments_df = assignments_df[~assignments_df["RawScore"].isin(not_graded_marks)]
    # drop excused assignments
    excused_marks = ["EX", "Ex", "ex", "es", "eng"]
    assignments_df = assignments_df[~assignments_df["RawScore"].isin(excused_marks)]
    # drop assignments with no grade entered
    assignments_df = assignments_df[assignments_df["RawScore"] != ""]
    # drop checkmarks
    assignments_df = assignments_df[assignments_df["RawScore"] != "✓"]

    possible_errors_df = assignments_df[~assignments_df['RawScore'].str.contains('!|/|%')]
    
    possible_errors_df = students_df.merge(possible_errors_df, on=['StudentID'], how='right')
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    for teacher, errors_df in possible_errors_df.groupby('Teacher'):
        errors_df.to_excel(writer, sheet_name = teacher)

    writer.close()
    f.seek(0)

    date_str = dt.datetime.now().strftime('%Y-%m-%d')
    download_name = f'JupiterGradeEntryErrors{date_str}.xlsx'
    return f, download_name
