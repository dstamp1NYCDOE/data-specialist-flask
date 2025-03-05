import pandas as pd
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO


def return_teacher_df():
    filenames = utils.return_most_recent_report_per_semester(files_df, "6_42")
    df_lst = [utils.return_file_as_df(x) for x in filenames]
    df = pd.concat(df_lst)
    df = df.drop_duplicates(subset=["EmployeeID"])
    df = df.sort_values(by=["LastName", "FirstName"])
    return df


def return_teacher_names():
    df = return_teacher_df()
    df["Text"] = df["FirstName"].str.title() + " " + df["LastName"].str.title()
    lst = df[["EmployeeID", "Text"]].to_records(index=False).tolist()
    return lst


def main(form, request):
    grades_df = return_combined_df_by_report("1_07")
    section_properties_df = return_combined_df_by_report("4_23")
    section_properties_cols = ["Course", "Section", "Term", "Co-Teacher"]
    section_properties_df = section_properties_df[section_properties_cols]

    dff = grades_df.merge(
        section_properties_df, on=["Course", "Section", "Term"], how="left"
    )
    dff["Co-Teacher"] = dff["Co-Teacher"].fillna("")
    dff = dff.dropna(subset=["FinalMark"])

    print(dff)


def return_combined_df_by_report(report_str):
    filenames = utils.return_most_recent_report_per_semester(files_df, report_str)

    df_lst = []
    for filename in filenames:
        term = filename[9 : 9 + 6]
        df = utils.return_file_as_df(filename)
        df["Term"] = term
        df_lst.append(df)

    df = pd.concat(df_lst)
    return df
