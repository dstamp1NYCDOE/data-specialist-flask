import pandas as pd
import numpy as np

import app.scripts.programming.requests.process_transcript as process_transcript


from app.scripts.testing.regents import process_regents_max

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main():
    cr_1_14_filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    student_credits_by_curriculum_df = process_transcript(cr_1_14_df)

    eligible_administrations = [
        "2021-2",
        "2021-7",
        "2022-1",
        "2022-2",
        "2022-7",
    ]

    dfs_lst = []
    for administration in eligible_administrations:
        filename = utils.return_most_recent_report_by_semester(
            files_df, "1_08", administration
        )
        df = utils.return_file_as_df(filename)
        df["administration"] = administration
        dfs_lst.append(df)

    regents_df = pd.concat(dfs_lst)
    regents_df["is_eligible_score"] = regents_df["Final Exam"].apply(
        return_if_eligible_score
    )

    eligible_scores_df = regents_df[regents_df["is_eligible_score"]]
    eligible_scores_df["CourseCode"] = eligible_scores_df["Course"].apply(
        lambda x: x[0:4]
    )

    regents_max_df = process_regents_max.main()

    combined_scores_df = eligible_scores_df.merge(
        regents_max_df, on=["StudentID", "CourseCode"], how="inner"
    )
    combined_scores_df = combined_scores_df[combined_scores_df["passed?"] == False]
    combined_scores_df = combined_scores_df.drop_duplicates(
        subset=["StudentID", "CourseCode"]
    )
    combined_scores_df["curriculum"] = combined_scores_df["CourseCode"].apply(
        attach_curriculum_to_exam
    )

    combined_scores_df = combined_scores_df.merge(
        student_credits_by_curriculum_df, on=["StudentID", "curriculum"]
    ).fillna(0)
    # combined_scores_df = combined_scores_df[combined_scores_df["credits_earned"] >= 2]

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "administration",
        "Exam",
        "Mark",
        "curriculum",
        "credits_earned",
    ]

    combined_scores_df = combined_scores_df[cols]

    cr_1_49_filename = utils.return_most_recent_report(files_df, "1_49")
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor"]]

    combined_scores_df = combined_scores_df.merge(
        cr_1_49_df, on=["StudentID"], how="left"
    )

    combined_scores_df = combined_scores_df.sort_values(
        by=["Counselor", "LastName", "FirstName"]
    )

    return combined_scores_df


def attach_curriculum_to_exam(CourseCode):
    course_code_dict = {
        "MXRC": "ME",
        "MXRN": "MR",
        "MXRK": "MG",
        "EXRC": "EE",
        "HXRC": "HG",
        "HXRK": "HU",
        "SXRK": "SL",
        "SXRX": "SC",
        "SXRU": "SE",
    }
    return course_code_dict.get(CourseCode)


def return_reg_mark(marks):
    return marks.to_list()[0]


def return_if_eligible_score(mark):
    try:
        return int(mark) >= 50 and int(mark) < 65
    except:
        return False


from app.scripts.programming.requests.marks import marks_dict


def process_transcript(transcript_raw_df):
    # transcript_raw_df = transcript_raw_df[transcript_raw_df['Credits']>0]
    transcript_raw_df = transcript_raw_df[~transcript_raw_df["Mark"].isna()]

    transcript_raw_df["passed?"] = transcript_raw_df["Mark"].apply(passed_course)

    transcript_raw_df["dept"] = transcript_raw_df["Course"].apply(lambda x: x[0])

    transcript_raw_df["curriculum"] = transcript_raw_df["Course"].apply(
        lambda x: x[0:2]
    )

    transcript_raw_df["credits_earned"] = transcript_raw_df.apply(
        credits_earned, axis=1
    )

    student_credits_by_curriculum = pd.pivot_table(
        transcript_raw_df,
        index=["StudentID", "curriculum"],
        values="credits_earned",
        aggfunc="sum",
    ).reset_index()
    print(student_credits_by_curriculum)
    return student_credits_by_curriculum


def credits_earned(student_row):
    course_passed = student_row["passed?"]

    if course_passed:
        return student_row["Credits"]
    else:
        return 0


def passed_course(mark):
    mark = str(mark).upper()
    if mark in marks_dict.keys():
        return marks_dict.get(mark)
    else:
        return int(mark) >= 65
