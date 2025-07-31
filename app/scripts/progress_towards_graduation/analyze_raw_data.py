import pandas as pd
from io import BytesIO

from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def return_progress_towards_graduation():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    # Load student transcripts from CR 1_14 
    cr_1_14_filename = utils.return_most_recent_report_by_semester(files_df, "1_14", year_and_semester=year_and_semester)
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    # load regents max from CR 1_42 
    cr_1_42_filename = utils.return_most_recent_report_by_semester(files_df, "1_42", year_and_semester=year_and_semester)
    cr_1_42_df = utils.return_file_as_df(cr_1_42_filename)


    return ""