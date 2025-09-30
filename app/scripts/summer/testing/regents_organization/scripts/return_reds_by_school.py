import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

import os
from io import BytesIO
from flask import current_app, session


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"


    ### process the REDS combined file
    reds_filename = request.files[form.reds_filename.name]
    df_dict = pd.read_excel(reds_filename, sheet_name=None)

    df_lst = []
    for (exam, df) in df_dict.items():
        df["Exam"] = exam
        df['ExamTitle'] = df['Exam'].apply(replace_exam_code_with_title)
        df_lst.append(df)

    dff = pd.concat(df_lst, ignore_index=True)

    ## rename Student Id
    dff = dff.rename(columns={"Student Id": "StudentID"})


    ### attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school", "school_name"]] 

    dff = dff.merge(cr_s_01_df, on="StudentID", how="left")
    dff['school_name'] = dff['school_name'].fillna("WalkIn")
    dff['Sending school'] = dff['Sending school'].fillna("Walkin")

    students_by_school_pvt = pd.pivot_table(dff, index=['StudentID', 'Name','Sending school', 'school_name'], columns='ExamTitle', values='Final Score', aggfunc='max')
    students_by_school_pvt = students_by_school_pvt.reset_index()

    ### generate final sheet by sending school 
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    for sending_school, students_by_school in students_by_school_pvt.groupby('Sending school'):
        students_by_school = students_by_school.drop(columns=['Sending school'])
        students_by_school = students_by_school.sort_values(by=['Name','StudentID'])
        students_by_school.to_excel(writer, sheet_name=sending_school, index=False)


    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()


    writer.close()
    f.seek(0)
    ### return the file
    download_name = f"RegentsResultsBySchool_{year_and_semester}.xlsx"
    return f, download_name


def replace_exam_code_with_title(exam_code):
    exam_code_dict = {
        'EXRC':'ELA',
        'HXRC':'Global',
        'HXRK':'USH',
        'MXRF':'Alg1',
        'MXRJ':'Geo',
        'MXRN':'Alg2',
        'SXRK':'LE',
        'SXR3':'Bio',
        'SXR2':'ESS',
        'SXRU':'ES',
        'SXRX':'Chem'
    }
    return exam_code_dict.get(exam_code, exam_code)