import pandas as pd
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
import datetime as dt 

from app.scripts.attendance.jupiter.process import main as process_jupiter



def main():
        ## import processed jupiter
    jupiter_df = process_jupiter() 