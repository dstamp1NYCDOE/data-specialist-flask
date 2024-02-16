import glob
import pandas as pd


def return_dataframe_of_files():
    lst = []
    for filename in glob.glob("data/**/**/*.*"):
        file = filename.split("/")[3]
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
    files_df = files_df[files_df['report']==report]
    files_df = files_df.sort_values(by=['download_date'])
    filename = files_df.iloc[-1,:]['filename']
    return filename

def return_file_as_df(filename):
    if 'xlsx' in filename:
        return pd.read_excel(filename)
    if 'csv' in filename:
        return pd.read_csv(filename)
