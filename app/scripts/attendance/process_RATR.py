import pandas as pd

def clean(RATR_df):
    RATR_df["StudentID"] = RATR_df["STUDENT ID"].str.extract("(\d{9})")
    RATR_df["Date"] = RATR_df["SCHOOL DAY"].str.extract("(\d{2}/\d{2}/\d{2})")
    RATR_df["Date"] = pd.to_datetime(RATR_df["Date"])
    RATR_df['Weekday'] = RATR_df["Date"].dt.weekday
    RATR_df["is_monday?"] = RATR_df["Date"].dt.weekday == 0
    RATR_df["Month"] = RATR_df["Date"].apply(lambda x: x.strftime('%Y-%m'))
    return RATR_df


def overall_attd_by_weekday(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["Weekday"],
        columns="ATTD",
        values="StudentID",
        aggfunc="count",
        margins=True,
        margins_name='total'
    ).fillna(0)

    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl

def overall_attd_by_month(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["Month"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()
    
    return pvt_tbl

def student_attd_by_month(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", "Month"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()
    
    return pvt_tbl


def student_attd_by_weekday(RATR_df):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", "is_monday?"],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl['total'] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])

    pvt_tbl = pvt_tbl.reset_index()

    temp_lst = []
    for StudentID, df in pvt_tbl.groupby('StudentID'):
        try:
            monday_late_pct = df[df['is_monday?']==True]["late_%"].tolist()[0]
        except IndexError:
            monday_late_pct = 0

        try:
            non_monday_late_pct = df[df["is_monday?"] == False]["late_%"].tolist()[0]
        except IndexError:
            non_monday_late_pct = 0

        temp_dict = {
            "StudentID": StudentID,
            "monday_late_pct": monday_late_pct,
            "non_monday_late_pct": non_monday_late_pct,
            "monday_to_non_monday_ratio": return_lateness_ratio(
                monday_late_pct, non_monday_late_pct
            ),
        }
        temp_lst.append(temp_dict)
    return pd.DataFrame(temp_lst)

def return_lateness_ratio(monday_late_pct,non_monday_late_pct):
    if non_monday_late_pct == 0:
        return monday_late_pct
    return monday_late_pct / non_monday_late_pct
