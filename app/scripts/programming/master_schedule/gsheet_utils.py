from dotenv import load_dotenv
load_dotenv()

import pygsheets

gc = pygsheets.authorize(service_account_env_var = "GDRIVE_API_CREDENTIALS")

def return_google_sheet_as_dataframe(spreadsheet_id,sheet="Sheet1"):
    if 'https' in spreadsheet_id:
        sh = gc.open_by_url(spreadsheet_id)
    else:
        sh = gc.open_by_key(spreadsheet_id)
    try:
        wks = sh.worksheet_by_title(sheet)
    except pygsheets.exceptions.WorksheetNotFound:
        wks = sh.sheet1
    df = wks.get_as_df(include_tailing_empty=False)
    if 'Student ID' in df.columns:
        df = df.rename(columns={"Student ID": "StudentID"})
    return df


def set_df_to_dataframe(output_df,spreadsheet_id,sheet="Output"):
    if 'https' in spreadsheet_id:
        sh = gc.open_by_url(spreadsheet_id)
    else:
        sh = gc.open_by_key(spreadsheet_id)

    wks = sh.worksheet_by_title(sheet)
    wks.clear()
    wks.set_dataframe(output_df.fillna(""),"A1")
    return True
