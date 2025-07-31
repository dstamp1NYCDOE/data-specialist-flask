import datetime as dt
import pandas as pd  #
import os

from io import BytesIO
from flask import session, current_app
import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from app.scripts.reportlab_utils import reportlab_letter_head, reportlab_closing
import app.scripts.utils as utils


def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    
    first_day_of_school_year = dt.datetime(month=9,day=1,year=school_year)

    filename = utils.return_most_recent_report_by_semester(files_df, "1_49", year_and_semester=year_and_semester)
    cr_1_49_df = pd.read_csv(filename).fillna('')

    ## remove shared instruction
    cr_1_49_df = cr_1_49_df[cr_1_49_df['GradeLevel'] != 'ST']

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = pd.read_csv(filename).fillna('')
    cr_3_07_df = cr_3_07_df[['StudentID','GEC']]


    cr_1_49_cols = [
        'StudentID',
        'LastName','FirstName',
        'Counselor',
    ]
    cr_1_49_df = cr_1_49_df[cr_1_49_cols]
    

    cr_1_49_df = cr_1_49_df.merge(cr_3_07_df, on=['StudentID'], how='left')

    
    cr_1_73_filename = request.files[form.cr_1_73.name]
    cr_1_73_df = pd.read_excel(cr_1_73_filename)
    cr_1_73_cols = ['StudentID','Experience','Experience Start Date']

    cr_1_73_df = cr_1_73_df[cr_1_73_cols]

    ## filter to this school year
    cr_1_73_df = cr_1_73_df[cr_1_73_df['Experience Start Date']>first_day_of_school_year]
    cr_1_73_df = cr_1_73_df.sort_values(by=['Experience Start Date'])

    ## review all experience by counselor + cohort
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    combined_dfs = []
    for (experience,), df in cr_1_73_df.groupby(['Experience']):
        dff = df.drop_duplicates(subset=['StudentID'], keep='last')
        dff = cr_1_49_df.merge( 
            dff, on='StudentID', how='left'
        ).fillna('')
        dff[f'{experience}_Completed?'] = dff['Experience'].apply(lambda x: x == experience)
        combined_dfs.append(dff.drop(columns=['Experience','Experience Start Date']).set_index(['StudentID','LastName','FirstName','Counselor','GEC']))


        for index in ['Counselor','GEC']:
            dff_tbl = pd.pivot_table(dff,columns=f'{experience}_Completed?', index=index, margins=True,values='StudentID', aggfunc='count').fillna(0)
            dff_tbl[f'{experience}_%'] = 100*dff_tbl[True]/dff_tbl['All']
            dff_tbl[f'{experience}_%'] = dff_tbl[f'{experience}_%'].apply(lambda x: int(x))
            dff_tbl = dff_tbl.reset_index()
            sheet_name = f"{index}_{experience}"
            sheet_name = sheet_name[0:31]
            dff_tbl.to_excel(writer, sheet_name=sheet_name)

    combined_df = pd.concat(combined_dfs, axis=1)
    combined_df = combined_df.reset_index()
    combined_df['IPR_or_1_on_1_Completed?'] = combined_df['Annual Individual Progress Review_Completed?'] | combined_df['1 on 1 Postsecondary Planning Conference_Completed?']
    experience = 'IPR_or_1_on_1'
    for index in ['Counselor','GEC']:
        dff_tbl = pd.pivot_table(combined_df,columns=f'{experience}_Completed?', index=index, margins=True,values='StudentID', aggfunc='count').fillna(0)
        dff_tbl[f'{experience}_%'] = 100*dff_tbl[True]/dff_tbl['All']
        dff_tbl[f'{experience}_%'] = dff_tbl[f'{experience}_%'].apply(lambda x: int(x))
        dff_tbl = dff_tbl.reset_index()
        sheet_name = f"{index}_{experience}"
        sheet_name = sheet_name[0:31]
        dff_tbl.to_excel(writer, sheet_name=sheet_name)
    

    ## students without experience
    for cohort, students_df in combined_df.groupby('GEC'):
        students_dff = students_df[students_df['1 on 1 Postsecondary Planning Conference_Completed?']==False]
        experience = '1 on 1 Postsecondary Planning Conference'
        sheet_name = f"{cohort}_incomplete_{experience}"
        sheet_name = sheet_name[0:31]
        students_dff.to_excel(writer, sheet_name=sheet_name)
    

    ## students without IPR but not divided by cohort
    students_dff = combined_df[combined_df['Annual Individual Progress Review_Completed?']==False]
    experience = 'Annual Individual Progress Review'
    sheet_name = f"all_incomplete_{experience}"
    sheet_name = sheet_name[0:31]
    students_dff.to_excel(writer, sheet_name=sheet_name)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 0)
        worksheet.autofit()

    writer.close()

    f.seek(0)
    return f