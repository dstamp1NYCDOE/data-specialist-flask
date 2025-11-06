import pandas as pd

from io import BytesIO

from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df



def return_jupiter_logins_analysis(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = request.files[form.jupiter_login_file.name]
    

    login_df = pd.read_csv(filename)
    login_df = process_login_data(login_df)
    f = return_login_report(login_df)

    download_name = f"Jupiter_Login_Analysis.xlsx"

    return f, download_name

def process_login_data(login_df):
    login_df['Timestamp'] = pd.to_datetime(login_df['Timestamp'])
    login_df['login_type'] = login_df['ContactID'].apply(lambda x: 'Student' if x==0 else 'Parent/Guardian')

    return login_df

def return_login_report(login_df):

    pvt_tbl = pd.pivot_table(
        login_df,
        index=['StudentID'],
        columns=['login_type'],
        values=['ContactID','Timestamp'],
        aggfunc={'ContactID':'count','Timestamp':'max'},
    )
    pvt_tbl = pvt_tbl.reset_index()
    pvt_tbl.columns = ['StudentID','#_Family_Logins','#_Student_Logins','Last_Family_Login','Last_Student_Login']

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    register_df = utils.return_file_as_df(filename)

    register_df = register_df[['StudentID','LastName','FirstName']]

    df = register_df.merge(pvt_tbl, on=['StudentID'], how='left')


    f = BytesIO()
    writer = pd.ExcelWriter(f)
    df.to_excel(writer, index=False)
    writer.close()
    f.seek(0)


    return f