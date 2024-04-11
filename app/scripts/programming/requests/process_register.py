import pandas as pd
import numpy as np


import app.scripts.utils as utils

from flask import session

def main(register_raw_df):
    register_raw_df['year_in_hs'] = register_raw_df['GEC'].apply(return_year_in_hs)

    cols = [
        'StudentID',
        'LastName',
        'FirstName',
        'year_in_hs',
        'LEPFlag'
    ]
    return register_raw_df[cols]

def return_year_in_hs(gec):
    school_year = session["school_year"]
    return utils.return_year_in_hs(gec, school_year) + 1

