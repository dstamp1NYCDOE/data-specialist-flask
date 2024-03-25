import pandas as pd
import numpy as np
import app.scripts.utils as utils
from app.scripts import scripts, files_df


def main():
    filename = utils.return_most_recent_report(files_df, "1_42")
    cr_1_42_df = utils.return_file_as_df(filename)
    df = cr_1_42_df.set_index("StudentID")
    df1 = pd.DataFrame(
        {
            "Exam": np.tile(df.columns, len(df)),
            "StudentID": df.index.repeat(df.shape[1]),
            "Score": df.values.ravel(),
        }
    )
    df1 = df1[df1["Exam"].str.contains("REG")]
    df1 = df1.dropna()
    df1["Mark"] = df1["Score"].str[6:]

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    df1 = df1.merge(cr_1_30_df[["Mark", "NumericEquivalent"]], on=["Mark"], how="left")

    df1["passed?"] = df1.apply(determine_if_passed, axis=1)
    df1["CourseCode"] = df1["Score"].str[0:4]
    print(df1)

    return df1


def determine_if_passed(student_row):
    mark = student_row["Mark"]
    NumericEquivalent = student_row["NumericEquivalent"]

    if mark in ["WA", "WG"]:
        return True
    elif mark in ["ABS", "INV"]:
        return False
    else:
        return NumericEquivalent >= 65
