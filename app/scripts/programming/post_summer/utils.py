import datetime as dt
import pandas as pd
def return_new_to_hsfi(admit_date,school_year):
    school_year_start = dt.datetime(school_year, 7, 1)
    
    return admit_date >= school_year_start