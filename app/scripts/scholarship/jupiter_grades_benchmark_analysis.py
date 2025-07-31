from flask import session
import pandas as pd

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"  
        
    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    df = utils.return_file_as_df(filename)
    
    ## drop courses with no grades
    df = df.dropna(subset=['Pct'])
    # filter to S1 and S2
    df = df[df['Term'].isin(['S1', 'S2'])]
    ## identify if passing
    df["Passing?"] = df['Pct'] >= 65

    ## pivot table
    pvt_tbl = pd.pivot_table(df, index=['StudentID','Term'], columns='Passing?',values='Course',aggfunc='count').fillna(0)
    pvt_tbl["total_classes"] = pvt_tbl.sum(axis=1)
    pvt_tbl["%_of_classes_passing"] = pvt_tbl[True]/pvt_tbl["total_classes"]
    pvt_tbl["passing_all_classes"] = pvt_tbl[False] == 0
    pvt_tbl = pvt_tbl.reset_index()

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    pvt_tbl = pvt_tbl.merge(students_df, on=['StudentID'], how='left')
    return pvt_tbl
