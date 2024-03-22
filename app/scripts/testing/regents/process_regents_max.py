import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
    filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(filename)

    return cr_1_14_df