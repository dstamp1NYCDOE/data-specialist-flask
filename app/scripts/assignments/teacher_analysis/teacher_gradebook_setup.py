from flask import session

import pandas as pd

from io import BytesIO
import datetime as dt
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from app.scripts.date_to_marking_period import return_mp_from_date

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    ## assignments
    filename = utils.return_most_recent_report_by_semester(
        files_df, "assignments", year_and_semester=year_and_semester
    )
    assignments_df = utils.return_file_as_df(filename)

    assignments_df['DueDate'] = assignments_df['DueDate'].ffill()
    assignments_df['DueDate'] = pd.to_datetime(assignments_df['DueDate'],'coerce')
    assignments_df['MP'] = assignments_df['DueDate'].apply(return_mp_from_date, args=(school_year,))
    


    assignments_df = assignments_df[assignments_df["Course"] != ""]

    # drop assignments worth zero
    assignments_df = assignments_df.dropna(subset=["RawScore"])
    assignments_df = assignments_df[assignments_df["WorthPoints"] != 0]

    marks_to_keep = ["0!", "1!", "2!", "3!", "4!", "5!"]
    assignments_df = assignments_df[assignments_df["RawScore"].isin(marks_to_keep)]

    ##drop non-credit bearing classes
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "G"]
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "Z"]
    assignments_df = assignments_df[assignments_df["Course"].str[0] != "R"]

    assignment_pvt = pd.pivot_table(
        assignments_df,
        index=["Teacher", "Course", "Category", "Assignment", "DueDate","MP"],
        aggfunc={"CategoryWeight": "max", "WorthPoints": "max", "Percent": "mean"},
    ).reset_index()

    category_pvt = pd.pivot_table(
        assignment_pvt,
        index=["Teacher", "Course", "Category"],
        aggfunc={"WorthPoints": "sum"},
    )
    category_pvt.columns = ["TotalWorth"]
    category_pvt = category_pvt.reset_index()


    category_by_mp_pvt = pd.pivot_table(
        assignment_pvt,
        index=["Teacher", "Course", "Category",],
        columns=['MP'],
        aggfunc={"WorthPoints": "sum"},
    ).fillna(0)  
    category_by_mp_pvt['TotalWorth'] = category_by_mp_pvt.sum(axis=1)
    category_by_mp_pvt = category_by_mp_pvt.reset_index()

    print(category_by_mp_pvt)


    assignment_pvt = assignment_pvt.merge(
        category_pvt, on=["Teacher", "Course", "Category"], how="left"
    )

    assignment_pvt["category_net"] = (
        assignment_pvt["WorthPoints"] / assignment_pvt["TotalWorth"]
    )
    assignment_pvt["overall_net"] = (
        assignment_pvt["category_net"] * assignment_pvt["CategoryWeight"] / 100
    )







    f = BytesIO()
    writer = pd.ExcelWriter(f)
    assignment_pvt.to_excel(writer, sheet_name='All')
    category_by_mp_pvt.to_excel(writer, sheet_name='ByMarkingPeriod')


    writer.close()
    f.seek(0)

    date_str = dt.datetime.now().strftime("%Y-%m-%d")
    download_name = f"teacher_gradebook_setup_analysis_{date_str}.xlsx"
    return f, download_name
