import glob
import pandas as pd
import re
import os

from dotenv import load_dotenv

load_dotenv()

import pygsheets

gc = pygsheets.authorize(service_account_env_var="GDRIVE_API_CREDENTIALS")


from flask import current_app
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


period_regex = re.compile(r"\d{1,2}")

StudentID_Regex = r"\d{9}"
StudentIDRegex = re.compile(StudentID_Regex)


DBN_Regex = r"\d{2}[A-Z]\d{3}"
DBN_Regex = re.compile(DBN_Regex)


def return_dataframe_of_gsheets():
    # gsheet_urls_csv_filepath = os.path.join(
    #     current_app.root_path, f"data/gsheet_urls.csv"
    #     )
    gsheet_urls_csv_filepath = f"app/data/gsheet_urls.csv"
    gsheet_urls_df = pd.read_csv(gsheet_urls_csv_filepath)
    return gsheet_urls_df


def return_dataframe_of_photos():
    lst = []
    file_lst = glob.glob("app/data/StudentPhotos/**/*.*")
    for filename in file_lst:
        mo = StudentIDRegex.search(filename)
        StudentID = mo.group()

        mo = DBN_Regex.search(filename)
        DBN = mo.group()

        file_dict = {
            "photo_filename": filename,
            "StudentID": int(StudentID),
            "DBN": DBN,
        }

        lst.append(file_dict)

    files_df = pd.DataFrame(lst)
    return files_df


def return_dataframe_of_files():
    lst = []
    file_lst = glob.glob("app/data/**/**/*.*")
    file_lst = [file for file in file_lst if not file.endswith(".jpg")]
    for filename in file_lst:

        # file = filename.split("/")[4]s
        file = os.path.basename(filename)

        year_and_semester, download_date, report = file.split("_")
        school_year, semester = year_and_semester.split("-")
        report = report.split(".")[0].replace("-", "_")
        file_dict = {
            "filename": filename,
            "download_date": download_date,
            "report": report,
            "year_and_semester": year_and_semester,
            "school_year": school_year,
            "semester": semester,
        }

        lst.append(file_dict)

    files_df = pd.DataFrame(lst)

    return files_df

def return_most_recent_report_per_semester(files_df, report):
    files_df = return_dataframe_of_files()
    files_df = files_df[files_df["report"] == report]
    files_df = files_df.sort_values(by=["download_date"])
    files_df = files_df.drop_duplicates(subset='year_and_semester')
    return files_df['filename'].to_list()


def return_most_recent_report(files_df, report):
    files_df = return_dataframe_of_files()
    files_df = files_df[files_df["report"] == report]
    files_df = files_df.sort_values(by=["download_date"])
    filename = files_df.iloc[-1, :]["filename"]
    return filename


def return_most_recent_report_by_semester(files_df, report, year_and_semester):
    files_df = return_dataframe_of_files()
    files_df = files_df[files_df["year_and_semester"] == year_and_semester]
    files_df = files_df[files_df["report"] == report]
    files_df = files_df.sort_values(by=["download_date"])
    filename = files_df.iloc[-1, :]["filename"]
    return filename


def return_gsheet_url_by_title(gsheet_df, title, year_and_semester=None):
    gsheet_df = gsheet_df[gsheet_df["year_and_semester"] == year_and_semester]
    gsheet_df = gsheet_df[gsheet_df["gsheet_category"] == title]
    gsheet_url = gsheet_df.iloc[-1, :]["gsheet_url"]
    return gsheet_url


def return_file_as_df(filename, **kwargs):
    if "xlsx" in filename:
        return pd.read_excel(filename, **kwargs)
    if "csv" in filename:
        return pd.read_csv(filename, **kwargs)
    if "CSV" in filename:
        return pd.read_csv(filename, **kwargs)


def return_cohort_year(GEC):
    GEC_dict = {
        "6": 2026,
        "5": 2025,
        "4": 2024,
        "3": 2023,
        "2": 2022,
        "1": 2021,
        "Z": 2020,
        "Y": 2019,
        "X": 2018,
        "W": 2017,
        "V": 2016,
    }
    return GEC_dict.get(str(GEC))


def return_year_in_hs(GEC, school_year):
    return school_year - return_cohort_year(GEC) + 1


def return_hs_graduation_year(GEC):
    return return_cohort_year(GEC) + 4


def return_hs_graduation_month(GEC):
    return f"June {return_hs_graduation_year(GEC)}"


def return_CTE_major_by_course(course):
    major = ""
    if course[0:2] == "AF":
        return "FD"
    return major


def return_pd(period):
    mo = period_regex.search(period)
    return int(mo.group())


def convert_percentage_to_ratio(percentage):
    if percentage >= 0.99:
        return "Every Day"
    if percentage >= 0.95 - 0.025:
        return "Almost Every Day"
    if percentage >= 0.90 - 0.025:
        return "About 9 out of 10 days"
    if percentage >= 0.80 - 0.025:
        return "About 4 out of 5 days"
    if percentage >= 0.70 - 0.025:
        return "About 7 out of 10 days"
    if percentage >= 0.60 - 0.025:
        return "About 3 out of 5 days"
    if percentage >= 0.50 - 0.025:
        return "About every other day"
    if percentage >= 0.40 - 0.025:
        return "About 2 out of 5 days"
    if percentage >= 0.30 - 0.025:
        return "About 3 out of 10 days"
    if percentage >= 0.20 - 0.025:
        return "About 1 out of 5 days"
    if percentage >= 0.10 - 0.025:
        return "About 1 out of 10 days"
    if percentage >= 0.05 - 0.025:
        return "About 1 day per month"
    if percentage == 0:
        return "Never"
    return "Almost Never"


def return_df_as_table(df, cols=None, colWidths=None, rowHeights=None, fontsize=8):
    if cols:
        table_data = df[cols].values.tolist()
    else:
        cols = df.columns
        table_data = df.values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), fontsize),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t


def save_report_to_file(f, report_name, year, term):
    year_and_semester = f"{year}-{term}"

    filename = f"{year_and_semester}_9999-12-31_{report_name}"

    path = os.path.join(
        current_app.root_path, f"data/{year_and_semester}/{report_name}"
    )
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)

    f.save(os.path.join(path, filename))

    return True


def return_google_sheet_as_dataframe(spreadsheet_id, sheet="Sheet1"):
    if "https" in spreadsheet_id:
        sh = gc.open_by_url(spreadsheet_id)
    else:
        sh = gc.open_by_key(spreadsheet_id)
    try:
        wks = sh.worksheet_by_title(sheet)
    except pygsheets.exceptions.WorksheetNotFound:
        wks = sh.sheet1
    df = wks.get_as_df(include_tailing_empty=False)
    if "Student ID" in df.columns:
        df = df.rename(columns={"Student ID": "StudentID"})
    return df


def set_df_to_dataframe(output_df, spreadsheet_id, sheet="Output"):
    if "https" in spreadsheet_id:
        sh = gc.open_by_url(spreadsheet_id)
    else:
        sh = gc.open_by_key(spreadsheet_id)
    try:
        wks = sh.worksheet_by_title(sheet)
    except:
        wks = sh.add_worksheet(sheet)
    wks.clear()
    wks.set_dataframe(output_df.fillna(""), "A1")
    return True


def return_home_lang_code_table(files_df):
    filename = return_most_recent_report(files_df, "TBLD150")
    df = return_file_as_df(filename, skiprows=3)   
    df = df.rename(columns={'Code':'HomeLangCode','Description':'HomeLang'})
    
    return df[['HomeLangCode','HomeLang']] 