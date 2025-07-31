import pandas as pd
from flask import flash, send_file
from io import BytesIO

import app.scripts.utils.utils as utils

files_df = utils.return_dataframe_of_files()

def connect_google_survey_with_class_lists(data):
    year_and_semester = data['year_and_semester']
    gsheet_url = data['gsheet_url']
    student_id_columns = data["student_id_columns"]

    cr_1_01_filename = utils.return_most_recent_report_by_semester(files_df,'1_01',year_and_semester)
    cr_1_01_df = utils.return_file_as_df(cr_1_01_filename)
    cr_1_01_df = cr_1_01_df[cr_1_01_df.str[0]!='Z']

    cr_6_31_filename = utils.return_most_recent_report_by_semester(
        files_df, "6_31", year_and_semester
    )
    cr_6_31_df = utils.return_file_as_df(cr_6_31_filename).dropna()
    print(cr_6_31_df)

    cr_1_01_df = cr_1_01_df.merge(cr_6_31_df, left_on=['Teacher1'], right_on=['NickName'], how='left')
    cr_1_01_df = cr_1_01_df.merge(
        cr_6_31_df, left_on=["Teacher2"], right_on=["NickName"], how="left"
    )

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    output_cols = [
        'StudentID',
        'LastName',
        'FirstName',
        'OffClass',
        'Grade',
        'Course',
        'Section',
        'Period',
        'Room',
    ]

    DelegatedNickNames = cr_6_31_df['DelegatedNickName']
    for teacher in DelegatedNickNames:
        students_df = cr_1_01_df[
            (cr_1_01_df["DelegatedNickName_x"] == teacher)
            | (cr_1_01_df["DelegatedNickName_y"] == teacher)
        ]
        students_df = students_df.sort_values(by=['Period','Section'])
        students_df = students_df.reset_index()
        students_df.index = students_df.index+2
        students_df = students_df[output_cols]

        args = (
            "GoogleSheet",
            f"{student_id_columns}:{student_id_columns}",
            f"{student_id_columns}:W",
        )
        students_df[f"=unique(GoogleSheet!{student_id_columns}1:1"] = students_df.apply(
            return_lookup_formula, args=args, axis=1
        )

        students_df.to_excel(writer, sheet_name=f"{teacher}", index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    workbook = writer.book
    worksheet = workbook.add_worksheet("GoogleSheet")
    import_formula = f'=importrange("{gsheet_url}", "A:Z")'
    worksheet.write_formula(0, 0, import_formula)
    writer.close()

    f.seek(0)
    download_name = f"ClassListsWithGoogleSheet.xlsx"

    return send_file(f, as_attachment=True, download_name=download_name)


def return_lookup_formula(row, lookup_sheet, lookup_match, lookup_index):
    lookup_match_range = f"'{lookup_sheet}'!{lookup_match}"
    lookup_index_range = f"'{lookup_sheet}'!{lookup_index}"
    lookup_val_range = f"A{row.name}"

    formula_str = f"=index({lookup_index_range}, match({lookup_val_range}, {lookup_match_range},0) , 0)"
    return formula_str
