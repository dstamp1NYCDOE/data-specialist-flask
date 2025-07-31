import pandas as pd
from sklearn.linear_model import LinearRegression

import random
from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils

from itertools import pairwise

from flask import session


def main(RATR_df):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    

    calendar_filename = "app/data/SchoolCalendar.xlsx"
    calendar_df = pd.read_excel(calendar_filename, sheet_name=f"{school_year}")
    calendar_df["Holiday?"] = calendar_df["Holiday?"].astype("bool")
    calendar_df["HalfDay?"] = calendar_df["HalfDay?"].astype("bool")
    calendar_df = calendar_df[calendar_df["SchoolDay?"]]

    RATR_df = clean(RATR_df)
    RATR_df["Attd"] = RATR_df["ATTD"].apply(lambda x: 1 if x == "A" else 0)

    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07", year_and_semester=year_and_semester)
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )
    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]
    enrolled_students = cr_3_07_df["StudentID"]

    RATR_df = RATR_df[RATR_df["StudentID"].isin(enrolled_students)]

    RATR_df = RATR_df.merge(calendar_df, on="Date", how="left")

    MONTHS_lst = RATR_df["Month"].unique().tolist()
    MONTHS_lst.pop(0)
    MONTHS_lst.insert(0, "ytd")

    output_dict = {}
    for month in MONTHS_lst:
        if month != "ytd":
            RATR_dff = RATR_df[RATR_df["Month"] <= month]
        else:
            RATR_dff = RATR_df

        student_attd_df = return_student_attd(RATR_dff)
        student_rolling_attd_df = return_student_rolling_attd(RATR_dff)
        

        student_attd_by_month_df = return_student_pvt_by_subcolumn(RATR_dff, "Month")

        student_attd_by_term_df = return_student_pvt_by_subcolumn(RATR_dff, "Term")

        student_attd_by_day_of_week_df = return_student_pvt_by_subcolumn(
            RATR_dff, "Weekday"
        )
        student_attd_by_days_before_break_df = return_student_pvt_by_subcolumn(
            RATR_dff, "DaysBeforeBreak"
        )
        
        
        student_attd_by_days_after_break = return_student_pvt_by_subcolumn(
            RATR_dff, "DaysAfterBreak"
        )
        

        multiple_day_df = return_multiple_day_df(RATR_dff)

        output_df = students_df
        
        student_attd_df = student_attd_df[["StudentID", "ytd_absence_%"]]
        
        month_df = student_attd_by_month_df.pivot(
            index="StudentID", columns="Month", values="absence_%"
        )
        month_df["MonthlySparkline"] = month_df.apply(return_sparkline_formula, axis=1)
        monthly_trend_df = return_trend_df(student_attd_by_month_df)
        month_df = month_df.merge(monthly_trend_df, on=["StudentID"], how="left")

        term_df = student_attd_by_term_df.pivot(
            index="StudentID", columns="Term", values="absence_%"
        )
        term_df["MarkingPeriodSparkline"] = term_df.apply(
            return_sparkline_formula, axis=1
        )
        term_trend_df = return_trend_df(student_attd_by_term_df)
        term_df = term_df.merge(term_trend_df, on=["StudentID"], how="left")

        vacation_extender_df = return_vacation_extender_df(
            student_attd_by_days_before_break_df, student_attd_by_days_after_break
        )

        day_of_week_df = return_day_of_week_df(student_attd_by_day_of_week_df)

        student_attd_correl_df = return_student_correlation_to_overall(RATR_df)

        output_df = output_df.merge(student_attd_df, on="StudentID")
        output_df = output_df.merge(student_rolling_attd_df, on="StudentID")
        output_df = output_df.merge(student_attd_correl_df, on="StudentID")
        
        
        output_df = output_df.merge(month_df, on="StudentID")
        
        output_df = output_df.merge(term_df, on="StudentID")
        
        output_df = output_df.merge(vacation_extender_df, on="StudentID")
        
        output_df = output_df.merge(day_of_week_df, on="StudentID")
        output_df = output_df.merge(multiple_day_df, on="StudentID")

        output_df["AttdTier"] = output_df["ytd_absence_%"].apply(return_attd_tier)
        output_df["AttdMetric"] = output_df["ytd_absence_%"].apply(return_attd_multiplier)
        output_df = output_df.sort_values(by=["year_in_hs", "LastName", "FirstName"])
        
        output_dict[month] = output_df.copy()


    ## run stats on ytd
    ytd_df = output_dict['ytd']
    attendance_metric_by_cohort = pd.pivot_table(ytd_df, index='year_in_hs', values='AttdMetric',aggfunc='mean')
    attendance_metric_by_cohort = attendance_metric_by_cohort.reset_index()
    output_dict['attd_metric_by_cohort'] = attendance_metric_by_cohort         

    return output_dict


def return_trend_df(student_attd_by_month_df):
    metric = "absence_%"
    df = (
        student_attd_by_month_df.groupby(["StudentID"])[metric]
        .apply(determine_weighted_slope)
        .reset_index()
        .rename(columns={metric: f"{metric}_trend"})
    )

    df[f"{metric}_trend_direction"] = df[f"{metric}_trend"].apply(
        lambda x: "Trending Less Absent" if x < 0 else "Trending More Absent"
    )

    return df


def determine_weighted_slope(data):
    df = pd.DataFrame(list(data), columns=["absence_%"])
    df["X"] = df.index + 1
    df["sample_weights"] = df.index + 1

    regr = LinearRegression()
    regr.fit(df[["X"]], df[["absence_%"]], df["sample_weights"])

    return regr.coef_[0][0]


def return_multiple_day_df(RATR_df):
    df = RATR_df[["StudentID", "Date", "ATTD"]]
    df = df[df["ATTD"] != "I"]

    output_lst = []
    for StudentID, student_attd_df in df.groupby("StudentID"):
        consecutive_days_absent = 0
        possible_pairs = 0
        attd_list = student_attd_df["ATTD"].to_list()
        total_days_absent = attd_list.count("A")
        for i, j in list(pairwise(attd_list)):
            possible_pairs += 1
            if i == "A" and j == "A":
                if consecutive_days_absent == 0:
                    consecutive_days_absent += 2
                else:
                    consecutive_days_absent += 1

        if total_days_absent == 0:
            consecutive_days_absent_metric = 0
        else:
            consecutive_days_absent_metric = consecutive_days_absent / total_days_absent

        temp_dict = {
            "StudentID": StudentID,
            "consecutive_day_pattern": return_consecutive_days_absent_flag(
                consecutive_days_absent_metric
            ),
        }
        output_lst.append(temp_dict)



    return pd.DataFrame(output_lst)

def return_attd_multiplier(absence_rate):
    if absence_rate <= 0.05:
        return 2.5
    if absence_rate <= 0.10:
        return 2
    if absence_rate <= 0.15:
        return 1
    if absence_rate <= 0.2:
        return 0
    return 0

def return_attd_tier(absence_rate):
    if absence_rate <= 0.05:
        return "Tier0-Satisfactory"
    if absence_rate <= 0.10:
        return "Tier1-At Risk"

    if absence_rate <= 0.15:
        return "Tier2-Early"
    if absence_rate <= 0.2:
        return "Tier2-High"

    return "Tier3"


def return_consecutive_days_absent_flag(consecutive_days_absent_metric):
    if consecutive_days_absent_metric <= 0:
        return "Single"

    if consecutive_days_absent_metric <= 0.25:
        return "None"

    return "Multiple"


def return_day_of_week_df(student_attd_by_day_of_week_df):

    dff = pd.pivot_table(
        student_attd_by_day_of_week_df,
        index="StudentID",
        columns="Weekday",
        values="absence_%",
        aggfunc="max",
    )
    dff = dff[
        [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
    ]
    dff["WeekdaySparkline"] = dff.apply(return_sparkline_formula, axis=1)
    dff = dff.reset_index()

    df = student_attd_by_day_of_week_df.sort_values("z_score")
    df = df.drop_duplicates(subset=["StudentID"], keep="last")

    df = df.fillna(0)
    df["WeekdayFlag"] = df.apply(return_day_of_week_flag, axis=1)
    df = df[["StudentID", "WeekdayFlag"]]
    df = dff.merge(df, on=["StudentID"], how="left")
    return df


def return_day_of_week_flag(student_row):
    weekday = student_row["Weekday"]
    z_score = student_row["z_score"]
    for threshold, flag in [(1, "High"), (0.75, "Medium"), (0.5, "Low")]:
        if z_score >= threshold:
            return f"{weekday}-{flag}"

    return "No"


def return_vacation_extender_df(
    student_attd_by_days_before_break_df, student_attd_by_days_after_break
):
    day_before_df = student_attd_by_days_before_break_df[
        student_attd_by_days_before_break_df["DaysBeforeBreak"] == 1
    ]
    
    
    day_after_df = student_attd_by_days_after_break[
        student_attd_by_days_after_break["DaysAfterBreak"] == 1
    ]
    df = day_after_df.merge(day_before_df, on=["StudentID"], how='left')
    df["Holiday Pattern"] = df.apply(return_vacation_extender_flag, axis=1)
    df["Holiday Pattern %"] = df.apply(return_vacation_extender_pct, axis=1)

    df = df[["StudentID", "Holiday Pattern","Holiday Pattern %"]]
    return df

def return_vacation_extender_pct(student_row):
    before_z_score = student_row["absence_%_x"]
    after_z_score = student_row["absence_%_y"]
    return 0.5*before_z_score+0.5*after_z_score
    
def return_vacation_extender_flag(student_row):
    
    before_z_score = student_row["z_score_x"]
    after_z_score = student_row["z_score_y"]

    if before_z_score < 0.25 and after_z_score < 0.25:
        return "No"

    if before_z_score > 1.25 and after_z_score > 1.25:
        return "Yes-High"
    if before_z_score > 0.75 and after_z_score > 0.75:
        return "Yes-Medium"
    if before_z_score > 0.25 and after_z_score > 0.25:
        return "Yes-Low"

    if before_z_score > 0.25:
        return "Yes-Before"
    if after_z_score > 0.25:
        return "Yes-After"


def return_overall_attd_by_date(RATR_df):
    pvt_tbl = pd.pivot_table(
        RATR_df,
        index="Date",
        columns="ATTD",
        values="StudentID",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["actual_total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["actual_absences"] = pvt_tbl["A"]
    pvt_tbl["overall_daily_absence_%"] = pvt_tbl["A"] / pvt_tbl["actual_total"]

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl[["Date", "overall_daily_absence_%"]]


def return_student_correlation_to_overall(RATR_df):
    overall_attd_by_date_df = return_overall_attd_by_date(RATR_df)
    RATR_df["Attd"] = RATR_df["ATTD"].apply(lambda x: 1 if x == "A" else 0)

    df = RATR_df[["StudentID", "Date", "Attd"]].merge(
        overall_attd_by_date_df, on="Date", how="left"
    )

    output_df = (
        df.groupby("StudentID")[["Attd", "overall_daily_absence_%"]]
        .corr()
        .iloc[0::2, -1]
    )
    output_df = output_df.reset_index()
    output_df.columns = ["StudentID", "", "Overall_Daily_Absence_Corr"]
    
    return output_df[["StudentID", "Overall_Daily_Absence_Corr"]]


def return_student_attd(RATR_df):
    pvt_tbl = pd.pivot_table(
        RATR_df,
        index="StudentID",
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["actual_total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["actual_absences"] = pvt_tbl["A"]
    pvt_tbl["ytd_absence_%"] = pvt_tbl["A"] / pvt_tbl["actual_total"]

    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl


def return_sparkline_formula(lst):
    lst = lst.dropna()
    lst = [str(x) for x in lst]
    data_lst = ", ".join(lst)
    data_lst = "{" + data_lst + "}"
    options = '{"charttype","column";"ymin",0;"ymax",1;"color","red"}'
    return f"=sparkline({data_lst},{options})"


def return_student_pvt_by_subcolumn(RATR_df, subcolumn):

    pvt_tbl = pd.pivot_table(
        RATR_df,
        index=["StudentID", subcolumn],
        columns="ATTD",
        values="Date",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl["total"] = pvt_tbl.sum(axis=1)
    pvt_tbl["late_%"] = pvt_tbl["L"] / (pvt_tbl["P"] + pvt_tbl["L"])
    pvt_tbl["absence_%"] = pvt_tbl["A"] / pvt_tbl["total"]

    pvt_tbl = pvt_tbl.reset_index()

    student_avg_and_std_dev = pd.pivot_table(
        pvt_tbl,
        index="StudentID",
        values="absence_%",
        aggfunc=["mean", "std"],
    ).reset_index()
    
    
    if len(student_avg_and_std_dev.columns) == 2:
        student_avg_and_std_dev['Std'] = 0        

    student_avg_and_std_dev.columns = ["StudentID", "Avg", "Std"]

    output_df = pvt_tbl[["StudentID", subcolumn, "absence_%"]].merge(
        student_avg_and_std_dev, on=["StudentID"], how="left"
    )

    output_df[f"z_score"] = (output_df["absence_%"] - output_df["Avg"]) / output_df[
        "Std"
    ]

    output_df = output_df.drop(columns=["Avg", "Std"])
 
    return output_df


from app.scripts.date_to_marking_period import return_mp_from_date


def clean(RATR_df):
    school_year = session["school_year"]

    RATR_df["StudentID"] = RATR_df["STUDENT ID"].str.extract("(\d{9})")
    RATR_df["StudentID"] = RATR_df["StudentID"].astype(int)
    RATR_df["Date"] = RATR_df["SCHOOL DAY"].str.extract("(\d{2}/\d{2}/\d{2})")
    RATR_df["Date"] = pd.to_datetime(RATR_df["Date"])
    RATR_df["Weekday"] = RATR_df["Date"].dt.day_name()
    RATR_df["Month"] = RATR_df["Date"].apply(lambda x: x.strftime("%Y-%m"))
    RATR_df["Term"] = RATR_df["Date"].apply(return_mp_from_date, args=(school_year,))
    return RATR_df


def return_student_rolling_attd(df):
    
    df = df[['StudentID','Date','Attd']]
    df = df.sort_values(by=['StudentID','Date'])

    df['rolling_20d_avg'] = (df.groupby('StudentID')['Attd']
                            .transform(lambda x: x.rolling(window=20, min_periods=1).mean()))

    wide_df = df.groupby('StudentID').agg({
            'rolling_20d_avg': list,           
        }).reset_index()  

    def return_sparkline_formula(lst):
        lst = [str(x) for x in lst]
        data_lst = ", ".join(lst)
        data_lst = "{" + data_lst + "}"
        options = '{"charttype","line";"ymin",0;"ymax",1;"color","red"}'
        return f"=sparkline({data_lst},{options})"    
    
    wide_df["rolling_20d_avg"] = wide_df['rolling_20d_avg'].apply(return_sparkline_formula)    
    return wide_df  