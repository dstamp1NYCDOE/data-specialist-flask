from flask import session

import pandas as pd 
from sklearn.linear_model import LinearRegression

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session['school_year']
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(utils.return_year_in_hs, args=(school_year,))

    students_df = cr_3_07_df[['StudentID','LastName','FirstName','year_in_hs']]

    ## jupiter grades for semester 1 and 2
    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    grades_df = utils.return_file_as_df(filename)

    ## keep S1 and S2
    grades_df = grades_df[grades_df['Term'].isin(['S1','S2'])]
    grades_df['Curriculum'] = grades_df['Course'].apply(return_curriculum)

    #calculate average + standard deviation by curriculum by semester

    stats_df = pd.pivot_table( 
        grades_df, index=['Term','Curriculum'], values='Pct', aggfunc=('mean','std')
    ).fillna(0).reset_index()

    ## attach stats to student grades
    grades_df = grades_df.merge( 
        stats_df, on=['Term','Curriculum'], how='left')
    
    grades_df['z-score'] = grades_df.apply(calculate_z_score, axis=1)
    
    ## student avg z-score by semester 

    student_stats_by_term = pd.pivot_table( 
        grades_df, index=['StudentID','Term'], values='z-score',aggfunc='mean'
    ).reset_index()


    student_stats_by_term_pvt = pd.pivot_table(
        student_stats_by_term, index='StudentID', columns='Term', values='z-score',aggfunc='max'
    ).reset_index()
    

    overall_stats = pd.pivot_table( 
        grades_df, index=['StudentID'], values='z-score',aggfunc='mean'
    ).reset_index()
    overall_stats.columns=['StudentID','z-score_total']

    student_stats_by_term_lst = student_stats_by_term.groupby('StudentID')['z-score'].apply(list).reset_index()
    student_stats_by_term_lst.columns=['StudentID','z-score_lst']
    student_stats_by_term_lst['most_recent_term'] = student_stats_by_term_lst['z-score_lst'].apply(lambda x: x[-1] if len(x)>0 else 0)
    student_stats_by_term_lst['sparkline'] = student_stats_by_term_lst['z-score_lst'].apply(return_sparkline_formula)

    metric = 'z-score'
    grade_point_trajectory_df = (
        student_stats_by_term.groupby(["StudentID"])[metric]
        .apply(determine_weighted_slope)
        .reset_index()
        .rename(columns={metric: f"{metric}_net_gain"})
    )

    grade_point_trajectory_df = grade_point_trajectory_df.merge(student_stats_by_term_lst, on='StudentID', how='left')
    grade_point_trajectory_df = grade_point_trajectory_df.merge(student_stats_by_term_pvt, on='StudentID', how='left')
    grade_point_trajectory_df = grade_point_trajectory_df.merge(overall_stats, on='StudentID', how='left')
    grade_point_trajectory_df = students_df.merge(grade_point_trajectory_df, on='StudentID', how='left')
    grade_point_trajectory_df = grade_point_trajectory_df.sort_values(by=['z-score_net_gain'], ascending=False)
    
    grade_point_trajectory_df = grade_point_trajectory_df.dropna()
    output_cols = [
        'StudentID','LastName','FirstName',"year_in_hs",
        'S1','S2',"z-score_total",'z-score_net_gain','sparkline'
    ]
    
    return grade_point_trajectory_df[output_cols]

def determine_weighted_slope(data):
    df = pd.DataFrame(list(data), columns=["Metric"])
    df["X"] = df.index + 1
    df["sample_weights"] = df.index + 1

    regr = LinearRegression()
    regr.fit(df[["X"]], df[["Metric"]], df["sample_weights"])

    return regr.coef_[0][0]

def calculate_z_score(student_row):
    class_mean = student_row['mean']
    class_std = student_row['std']
    student_grade = student_row['Pct']

    if class_std == 0:
        return 0 
    else:
        return (student_grade - class_mean)/class_std

def return_sparkline_formula(lst):
    lst = [str(x) for x in lst]
    data_lst = ", ".join(lst)
    data_lst = "{" + data_lst + "}"
    options = '{"charttype","column";"ymin",-3;"ymax",3;"color","green";"negcolor","red"}'
    return f"=sparkline({data_lst},{options})"

def return_curriculum(Course):
    if Course[0] == 'F':
        return 'LOTE'
    
    if Course[0] == 'E':
        return Course[0:5]

    return Course[0:5]