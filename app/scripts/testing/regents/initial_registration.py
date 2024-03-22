import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.testing.regents import process_regents_max

def main(month):
    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()

    regents_max_df = process_regents_max()

    if month == 'January':
        return for_january(rosters_df,regents_max_df)
    if month == 'June':
        return for_june(rosters_df,regents_max_df)



def for_january(rosters_df,regents_max_df):
    df = pd.DataFrame()
    return df

def for_june(rosters_df,regents_max_df):

    df = pd.DataFrame()
    return df    