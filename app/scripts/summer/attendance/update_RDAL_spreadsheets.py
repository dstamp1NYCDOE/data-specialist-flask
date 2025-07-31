from app.scripts import scripts, files_df, photos_df, gsheets_df
from dotenv import load_dotenv
from flask import current_app, session
from io import BytesIO
import app.scripts.utils as utils
from app.scripts.summer.programming import programming_utils
import numpy as np
import os
import pandas as pd
import pygsheets


load_dotenv()
gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


def main():

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    RDAL_files = files_df[
        (files_df["report"] == "RDAL")
        & (files_df["year_and_semester"] == year_and_semester)
    ]

    

    lst_of_dfs = []
    for filename in RDAL_files["filename"]:
        df = utils.return_file_as_df(filename)
        lst_of_dfs.append(df)

    combined_rdal_df = pd.concat(lst_of_dfs)
    combined_rdal_df["num_of_days_absent"] = 1

    rdal_pvt = (
        pd.pivot_table(
            combined_rdal_df,
            index="StudentID",
            columns="Date",
            values="num_of_days_absent",
            aggfunc="sum",
        )
        .fillna(0)
        .reset_index()
    )

    df = pd.melt(rdal_pvt, id_vars="StudentID")

    students_lst = []
    for StudentID, absences_df in df.groupby("StudentID"):
        absences_df = absences_df.sort_values("Date", ascending=False)
        absences_lst = [int(x) for x in absences_df["value"]]
        consecutive_absences = return_consective_absences(absences_lst)
        student_dict = {
            "StudentID": StudentID,
            "consecutive_absences": consecutive_absences,
            "total_absences": sum(absences_lst),
        }
        students_lst.append(student_dict)

    consecutive_absences_df = pd.DataFrame(students_lst)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)
    ## drop z codes
    cr_1_01_df = cr_1_01_df[cr_1_01_df["Course"].str[0] != "Z"]
    ## drop courses not in period 1, 2, 3
    cr_1_01_df = cr_1_01_df[cr_1_01_df["Period"].isin([1, 2, 3])]
    ## students in course list
    students_taking_courses = cr_1_01_df["StudentID"].unique()

    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)

    students_df = cr_s_01_df[cr_s_01_df["StudentID"].isin(students_taking_courses)]

    cols = ["StudentID", "LastName", "FirstName", "Sending school"]
    students_df = students_df[cols]

    students_by_sending_school_pvt = pd.pivot_table(
        students_df, index="Sending school", values="StudentID", aggfunc="count"
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)

    students_df = students_df.merge(
        cr_3_07_df[["StudentID", "Student DOE Email", "ParentLN", "ParentFN", "Phone"]],
        on=["StudentID"],
        how="left",
    )

    students_df = students_df.merge(
        consecutive_absences_df, on=["StudentID"], how="left"
    ).fillna({'consecutive_absences':0,'total_absences':0})


    rdal_pvt = rdal_pvt.replace(1, "A")
    rdal_pvt = rdal_pvt.replace(0, "P")
    rdal_pvt = rdal_pvt[rdal_pvt.columns[::-1]]
    rdal_pvt.columns = [
        x.strftime("%m/%d") if x != "StudentID" else x for x in rdal_pvt.columns
    ]
    print(rdal_pvt)
    list_of_dates = rdal_pvt.columns[:-1]

    students_df = students_df.merge(rdal_pvt, on=["StudentID"], how="left").fillna("P")

    summer_school_attendance_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_attendance_hub", year_and_semester
    )

    sh = gc.open_by_url(summer_school_attendance_hub_url)
    df = students_df.sort_values(
        by=["consecutive_absences", "total_absences"], ascending=[False, False]
    )
    sheet_name = "Overall"
    try:
        wks = sh.worksheet_by_title(sheet_name)
    except:
        wks = sh.add_worksheet(sheet_name)
    wks.clear()
    wks.set_dataframe(df, "A1")
    wks.frozen_rows = 1
    wks.frozen_cols = 3
    wks.adjust_column_width(1, 14)

    summer_school_attendance_hub_df = utils.return_google_sheet_as_dataframe(
        summer_school_attendance_hub_url
    )

    for index, sending_school in summer_school_attendance_hub_df.iterrows():
        gsheet_url = sending_school["URL"]
        sh = gc.open_by_url(gsheet_url)
        sending_school = sending_school["Sending school"]

        df = students_df[students_df["Sending school"] == sending_school]
        
        df = df.sort_values(
            by=["consecutive_absences", "total_absences"], ascending=[False, False]
        )
        sheet_name = "Overall"
        try:
            wks = sh.worksheet_by_title(sheet_name)
        except:
            wks = sh.add_worksheet(sheet_name)
        wks.clear()
        wks.set_dataframe(df, "A1")
        wks.frozen_rows = 1
        wks.frozen_cols = 3
        wks.adjust_column_width(1, 14)

        for attd_date in list_of_dates:
            sheet_name = attd_date
            cols = [
                "StudentID",
                "LastName",
                "FirstName",
                "Sending school",
                "Student DOE Email",
                "ParentLN",
                "ParentFN",
                "Phone",
                "total_absences",
                attd_date,
            ]
            dff = df[cols]
            dff = dff[dff[attd_date] == "A"]
            dff = dff.sort_values(by="total_absences", ascending=False)
            try:
                wks = sh.worksheet_by_title(sheet_name)
            except:
                wks = sh.add_worksheet(sheet_name)
            wks.clear()
            wks.set_dataframe(dff.fillna(""), "A1")
            wks.frozen_rows = 1
            wks.frozen_cols = 3
            wks.adjust_column_width(1, 10)

    ## put updated attendance on each teacher's spreadsheet

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)
    master_schedule_df = master_schedule_df.rename(columns={"Course Code": "Course"})
    master_schedule_df["Cycle"] = master_schedule_df["Days"].apply(
        programming_utils.convert_days_to_cycle
    )
    code_deck = master_schedule_df[["Course", "Course Name"]].drop_duplicates()
    master_schedule_df = master_schedule_df[["Course", "Section", "Cycle"]]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )
    cr_1_01_df = utils.return_file_as_df(filename)
    cr_1_01_df = cr_1_01_df.merge(
        master_schedule_df, on=["Course", "Section"], how="left"
    )
    cr_1_01_df = cr_1_01_df.merge(code_deck, on=["Course"], how="left")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df = cr_3_07_df[
        ["StudentID", "Student DOE Email", "ParentLN", "ParentFN", "Phone"]
    ]
    cr_1_01_df = cr_1_01_df.merge(cr_3_07_df, on=["StudentID"], how="left")

    filename = utils.return_most_recent_report(files_df, "s_01")
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_1_01_df = cr_1_01_df.merge(
        cr_s_01_df[["StudentID", "school_name"]], on=["StudentID"], how="left"
    )

    summer_school_gradebooks_hub_url = utils.return_gsheet_url_by_title(
        gsheets_df, "summer_school_gradebooks_hub", year_and_semester
    )
    summer_school_gradebooks_hub_df = utils.return_google_sheet_as_dataframe(
        summer_school_gradebooks_hub_url
    )

    teacher_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Course",
        "Section",
        "Period",
        "Course Name",
        "Cycle",
        "school_name",
        "Student DOE Email",
        "ParentLN",
        "ParentFN",
        "Phone",
    ]

    sheet_name = "OverallAttendance"
    for index, gradebook in summer_school_gradebooks_hub_df.iterrows():
        gradebook_url = gradebook["Gradebook URL"]
        teacher_name = gradebook["TeacherName"]

        students_by_teacher_df = cr_1_01_df[cr_1_01_df["Teacher1"] == teacher_name][
            teacher_cols
        ]

        students_by_teacher_df = students_by_teacher_df.merge(
            students_df,
            on=[
                "StudentID",
                "LastName",
                "FirstName",
                "Student DOE Email",
                "ParentLN",
                "ParentFN",
            ],
        )
        students_by_teacher_df = students_by_teacher_df.sort_values(by=["Period", "Cycle", "LastName", "FirstName"])

        sh = gc.open_by_url(gradebook_url)
        try:
            wks = sh.worksheet_by_title(sheet_name)
        except:
            wks = sh.add_worksheet(sheet_name)
        wks.clear()
        wks.set_dataframe(students_by_teacher_df, "A1")
        wks.frozen_rows = 1
        wks.frozen_cols = 3
        wks.adjust_column_width(1, 14)

    return True


def return_consective_absences(absences_lst):
    consecutive_absences = 0
    for absence in absences_lst:
        if absence == 0:
            return consecutive_absences
        else:
            consecutive_absences += 1
    return consecutive_absences
