import glob
import pandas as pd
import re

period_regex = re.compile(r"\d{1,2}")

def return_dataframe_of_files():
    lst = []
    for filename in glob.glob("app/data/**/**/*.*"):
        
        file = filename.split("/")[4]
        year_and_semester, download_date, report = file.split('_')
        school_year, semester = year_and_semester.split('-')
        report = report.split('.')[0].replace('-','_')
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

def return_most_recent_report(files_df,report):
    files_df = return_dataframe_of_files()
    files_df = files_df[files_df['report']==report]
    files_df = files_df.sort_values(by=['download_date'])
    filename = files_df.iloc[-1,:]['filename']
    return filename

def return_most_recent_report_by_semester(files_df,report,year_and_semester):
    files_df = return_dataframe_of_files()
    files_df = files_df[files_df['year_and_semester']==year_and_semester]
    files_df = files_df[files_df['report']==report]
    files_df = files_df.sort_values(by=['download_date'])
    filename = files_df.iloc[-1,:]['filename']
    return filename

def return_file_as_df(filename):
    if 'xlsx' in filename:
        return pd.read_excel(filename)
    if 'csv' in filename:
        return pd.read_csv(filename)
    if "CSV" in filename:
        return pd.read_csv(filename)


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
    }
    return GEC_dict.get(str(GEC))

def return_year_in_hs(GEC,school_year):
    return school_year - return_cohort_year(GEC) + 1

def return_hs_graduation_year(GEC):
    return return_cohort_year(GEC) + 4


def return_hs_graduation_month(GEC):
    return f"June {return_hs_graduation_year(GEC)}"


def return_CTE_major_by_course(course):
    major = ''
    if course[0:2] == 'AF':
        return 'FD'
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
