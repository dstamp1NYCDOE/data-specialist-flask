import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df


def main(form, request):
    student_subset_title = form.subset_title.data

    student_lst_str = form.subset_lst.data
    student_lst = student_lst_str.split("\r\n")
    student_lst = [int(x) for x in student_lst]

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()
    rosters_df[student_subset_title] = rosters_df["StudentID"].apply(
        lambda x: x in student_lst
    )

    filename = utils.return_most_recent_report(files_df, "jupiter_master_schedule")
    master_schedule = utils.return_file_as_df(filename)
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1", "Period"]
    ]

    df = rosters_df.merge(master_schedule, on=["Course", "Section"])

    pvt_tbl = pd.pivot_table(
        df,
        index=["Teacher1", "Room", "Period"],
        columns=student_subset_title,
        values="StudentID",
        aggfunc="count",
    ).fillna(0)
    pvt_tbl = pvt_tbl.reset_index()

    return pvt_tbl
