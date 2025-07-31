import pandas as pd
from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
import itertools


def main():
    sheets = []
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

    shared_instruction_students = cr_3_07_df[cr_3_07_df["GradeLevel"] == "ST"][
        "StudentID"
    ]

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    jupiter_attd_filename = utils.return_most_recent_report_by_semester(
        files_df, "jupiter_period_attendance", year_and_semester=year_and_semester
    )
    attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

    ## only keep students still on register
    attendance_marks_df = attendance_marks_df[
        attendance_marks_df["StudentID"].isin(students_df["StudentID"])
    ]

    ## drop shared instruction students
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["StudentID"].isin(shared_instruction_students)
    ]

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(utils.return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    attd_by_student_by_day = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="count",
    ).fillna(0)

    attd_by_student_by_day["in_school?"] = (
        attd_by_student_by_day["present"] + attd_by_student_by_day["tardy"]
    ) >= 2
    attd_by_student_by_day = attd_by_student_by_day.reset_index()[
        ["StudentID", "Date", "in_school?"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        attd_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    first_period_present_by_student_by_day = pd.pivot_table(
        attendance_marks_df[attendance_marks_df["in_school?"]],
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc="min",
    ).reset_index()

    first_period_present_by_student_by_day["first_period_present"] = (
        first_period_present_by_student_by_day[["present", "tardy"]].min(axis=1)
    )

    first_period_present_by_student_by_day = first_period_present_by_student_by_day[
        ["StudentID", "Date", "first_period_present"]
    ]

    attendance_marks_df = attendance_marks_df.merge(
        first_period_present_by_student_by_day, on=["StudentID", "Date"], how="left"
    )

    attendance_marks_df["potential_cut"] = attendance_marks_df.apply(
        determine_potential_cut, axis=1
    )

    cuts_df = attendance_marks_df[attendance_marks_df["potential_cut"]]

    pvt = pd.pivot_table(
        cuts_df,
        index=["StudentID"],
        columns="Pd",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt["Total"] = pvt.sum(axis=1)
    pvt = pvt.merge(students_df, on=["StudentID"], how="left")
    pvt = pvt.reset_index()
    pvt = pvt.sort_values(by=["Total"], ascending=[False])
    student_total_cuts_df = pvt[['StudentID','Total']]

    print(student_total_cuts_df)
    
    sheets.append(("cuts_by_period", pvt))

    dff_lst = []
    for (date, period), df in cuts_df.groupby(["Date", "Pd"]):
        students_lst = df["StudentID"]
        permutations = list(itertools.permutations(students_lst, 2))
        dff = pd.DataFrame(permutations, columns=["StudentID1", "StudentID2"])
        dff["Date"] = date
        dff["Pd"] = period
        dff_lst.append(dff)

    dff = pd.concat(dff_lst)

    pvt = pd.pivot_table(
        dff,
        index=["StudentID1", "StudentID2"],
        columns="Pd",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt["pair_total"] = pvt.sum(axis=1)

    pvt = pvt.reset_index()

    pvt = pvt.merge(students_df, left_on=["StudentID1"], right_on=["StudentID"])
    pvt = pvt.merge(students_df, left_on=["StudentID2"], right_on=["StudentID"])
    pvt = pvt.drop(columns=['StudentID_x', 'StudentID_y'])

    print(pvt)

    pvt = pvt.sort_values(by=["pair_total"], ascending=[False])

    student_total_pairs_df = pd.pivot_table(pvt, index=['StudentID1'], values='pair_total', aggfunc='sum').reset_index()
    student_total_pairs_df.columns = ['StudentID', 'total_pair_total']

    pvt = pvt.merge(student_total_cuts_df, left_on=["StudentID1"], right_on=['StudentID'])
    pvt = pvt.merge(student_total_cuts_df, left_on=["StudentID2"], right_on=['StudentID'])

    # pvt = pvt.drop(columns=['StudentID_x', 'StudentID_y'])
    pvt['pair_frac_x'] = pvt['pair_total']/pvt['Total_x']
    pvt['pair_frac_y'] = pvt['pair_total']/pvt['Total_y']

    pvt['pair_frac_delta'] = (pvt['pair_frac_x'] - pvt['pair_frac_y'])**2
    
    pvt = pvt.sort_values(by=['pair_frac_delta'],ascending=[True])

    sheets.append(("total", pvt))

    f = BytesIO()

    writer = pd.ExcelWriter(f)

    for sheet_name, sheet_df in sheets:
        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()
    f.seek(0)

    download_name = "cut_report_by_groups.xlsx"
    return f, download_name


def determine_potential_cut(student_row):
    is_in_school = student_row["in_school?"]

    if is_in_school == False:
        return False

    attendance_type = student_row["Type"]
    period = student_row["Pd"]
    first_period_present = student_row["first_period_present"]
    if attendance_type == "unexcused" and period >= first_period_present:
        return True

    return False
