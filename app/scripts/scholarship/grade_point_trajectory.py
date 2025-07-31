from flask import session

import pandas as pd
from sklearn.linear_model import LinearRegression

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    cr_1_14_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_14", year_and_semester=year_and_semester
    )
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)

    ## student_info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    school_year = session["school_year"]
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    students_df = cr_3_07_df[["StudentID", "LastName", "FirstName", "year_in_hs"]]

    cr_1_30_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_30", year_and_semester=year_and_semester
    )
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)

    ## drop zero credit classes
    cr_1_14_df = cr_1_14_df[cr_1_14_df["Credits"] > 0]

    ## change to "curriculum"
    cr_1_14_df["Curriculum"] = cr_1_14_df["Course"].apply(return_curriculum)

    ## drop non_fall or spring courses
    cr_1_14_df = cr_1_14_df[cr_1_14_df["Term"].isin([1, 2])]

    ## attach numeric equivalent
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left"
    ).dropna()

    # calculate average + standard deviation by curriculum by semester

    stats_df = (
        pd.pivot_table(
            cr_1_14_df,
            index=["Year", "Term", "Curriculum"],
            values="NumericEquivalent",
            aggfunc=("mean", "std"),
        )
        .fillna(0)
        .reset_index()
    )

    ## attach stats to student grades
    cr_1_14_df = cr_1_14_df.merge(
        stats_df, on=["Year", "Term", "Curriculum"], how="left"
    )

    cr_1_14_df["z-score"] = cr_1_14_df.apply(calculate_z_score, axis=1)

    ## student avg z-score by semester

    student_stats_by_term = pd.pivot_table(
        cr_1_14_df,
        index=["StudentID", "Year", "Term"],
        values="z-score",
        aggfunc="mean",
    ).reset_index()

    overall_stats = pd.pivot_table(
        cr_1_14_df, index=["StudentID"], values="z-score", aggfunc="mean"
    ).reset_index()
    overall_stats.columns = ["StudentID", "z-score_total"]

    student_stats_by_term_lst = (
        student_stats_by_term.groupby("StudentID")["z-score"].apply(list).reset_index()
    )
    student_stats_by_term_lst.columns = ["StudentID", "z-score_lst"]
    student_stats_by_term_lst["most_recent_term"] = student_stats_by_term_lst[
        "z-score_lst"
    ].apply(lambda x: x[-1] if len(x) > 0 else 0)
    student_stats_by_term_lst["sparkline"] = student_stats_by_term_lst[
        "z-score_lst"
    ].apply(return_sparkline_formula)

    metric = "z-score"
    grade_point_trajectory_df = (
        student_stats_by_term.groupby(["StudentID"])[metric]
        .apply(determine_weighted_slope)
        .reset_index()
        .rename(columns={metric: f"{metric}_net_gain"})
    )

    grade_point_trajectory_df = grade_point_trajectory_df.merge(
        student_stats_by_term_lst, on="StudentID", how="left"
    )
    grade_point_trajectory_df = grade_point_trajectory_df.merge(
        overall_stats, on="StudentID", how="left"
    )
    grade_point_trajectory_df = students_df.merge(
        grade_point_trajectory_df, on="StudentID", how="left"
    )
    grade_point_trajectory_df = grade_point_trajectory_df.sort_values(
        by=["z-score_net_gain"], ascending=False
    )
    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "year_in_hs",
        "most_recent_term",
        "z-score_net_gain",
        "z-score_total",
        "sparkline",
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
    class_mean = student_row["mean"]
    class_std = student_row["std"]
    student_grade = student_row["NumericEquivalent"]

    if class_std == 0:
        return 0
    else:
        return (student_grade - class_mean) / class_std


def return_sparkline_formula(lst):
    lst = [str(x) for x in lst]
    data_lst = ", ".join(lst)
    data_lst = "{" + data_lst + "}"
    options = (
        '{"charttype","column";"ymin",-3;"ymax",3;"color","green";"negcolor","red"}'
    )
    return f"=sparkline({data_lst},{options})"


def return_curriculum(Course):
    if Course[0] == "F":
        return "LOTE"

    if Course[0] == "E":
        return Course[0:5]

    return Course[0:5]
