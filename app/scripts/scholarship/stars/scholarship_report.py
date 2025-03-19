import pandas as pd
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO


def return_teacher_df():
    filenames = utils.return_most_recent_report_per_semester(files_df, "6_42")
    df_lst = [utils.return_file_as_df(x) for x in filenames]
    df = pd.concat(df_lst)
    df = df.drop_duplicates(subset=["Teacher"])
    
    df = df.sort_values(by=["LastName", "FirstName"])
    return df


def return_teacher_names():
    df = return_teacher_df()
    df = df.drop_duplicates(subset=["EmployeeID"])
    df["Text"] = df["FirstName"].str.title() + " " + df["LastName"].str.title()
    lst = df[["EmployeeID", "Text"]].to_records(index=False).tolist()
    return lst


def main(form, request):
    grades_df = return_combined_df_by_report("1_07")
    grades_df = grades_df.drop(columns=['Teacher'])
    grades_df = grades_df.dropna(subset=["FinalMark"])
    grades_df = grades_df[grades_df['FinalMark'].str.isnumeric()]
    grades_df['FinalMark'] = grades_df['FinalMark'].astype(int)

    bins = [0, 65, 69, 75,79,84,89,100]
    labels = ['Total Failing', '65-69', '70-74', '75-79', '80-84', '85-89', '90-100']
    
    grades_df['final_mark_bin'] = pd.cut(grades_df['FinalMark'], bins=bins, labels=labels, right=True)

    print(grades_df)

    section_properties_df = return_combined_df_by_report("4_23")
    section_properties_cols = ["Course", "Section", "Term", "Teacher","Co-Teacher"]
    section_properties_df = section_properties_df[section_properties_cols]
    for teacher_col in ["Teacher", "Co-Teacher"]:
        section_properties_df[teacher_col] = section_properties_df[teacher_col].str.strip()

    dff = grades_df.merge(
        section_properties_df, on=["Term","Course", "Section"], how="left"
    )
    dff["Co-Teacher"] = dff["Co-Teacher"].fillna("")
    dff = dff.dropna(subset=["FinalMark"])

    teachers_df = return_teacher_df()
    attach_teacher_df = teachers_df[["EmployeeID", "Teacher"]]
    attach_teacher_df = attach_teacher_df.rename(columns={"EmployeeID": "EmployeeID_1"})

    attach_co_teacher_df = teachers_df[["EmployeeID", "Teacher"]]
    attach_co_teacher_df = attach_co_teacher_df.rename(columns={"EmployeeID": "EmployeeID_2", "Teacher": "Co-Teacher"})

    dff = dff.merge(attach_teacher_df, on="Teacher", how="left")
    dff = dff.merge(attach_co_teacher_df, on="Co-Teacher", how="left")


    teacher_of_interest = float(form.staff_member.data)
    
    dff['teacher_of_interest'] = (dff["EmployeeID_1"] == teacher_of_interest) | (dff["EmployeeID_2"] == teacher_of_interest)

    dff['RowLabel'] = dff['Course'].astype(str) + "/" + dff['Section'].astype(str) + " - " + dff['Teacher']

    grades_bin_pvt = pd.pivot_table(
        dff,
        index=["Term","Course", "Section", "Teacher","teacher_of_interest"],
        values="StudentID",
        columns="final_mark_bin",
        aggfunc="count",
        margins=True,
        margins_name="Total",
    )
    grades_bin_pvt = grades_bin_pvt[grades_bin_pvt['Total']>0]


    print(grades_bin_pvt)

    # f = BytesIO()

    # writer.close()
    # f.seek(0)
    # return f, "STARs_Scholarship_Report.xlsx"
    
    return grades_bin_pvt.to_html()

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
