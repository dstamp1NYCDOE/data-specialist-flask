import pandas as pd  #
from io import BytesIO

import app.scripts.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session

from app.scripts.graduation.certification import cte


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_68", year_and_semester
    )
    cr_1_68_df = utils.return_file_as_df(filename)
    cr_1_68_df = cr_1_68_df.fillna("")
    cr_1_68_df["year_in_hs"] = cr_1_68_df["Cohort"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )

    ## keep seniors or 4th year+ students
    cr_1_68_df = cr_1_68_df[
        ((cr_1_68_df["Grade"] == 12) | (cr_1_68_df["year_in_hs"] >= 4))
        & (cr_1_68_df["Grade"] != "ST")
    ]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_49", year_and_semester
    )
    cr_1_49_df = utils.return_file_as_df(filename)
    cr_1_49_df = cr_1_49_df[["StudentID", "Counselor", "OffClass"]]
    cr_1_68_df = cr_1_68_df.merge(cr_1_49_df, on="StudentID", how="left")

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df = cr_3_07_df[["StudentID", "IEPFlag"]]
    cr_3_07_df["IEP"] = cr_3_07_df["IEPFlag"].apply(lambda x: x == "Y")
    cr_3_07_df = cr_3_07_df[["StudentID", "IEP"]]
    cr_1_68_df = cr_1_68_df.merge(cr_3_07_df, on="StudentID", how="left")

    cte_df = cte.main()
    cr_1_68_df = cr_1_68_df.merge(
        cte_df.drop(columns=["LastName", "FirstName"]), on="StudentID", how="left"
    )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_27", year_and_semester
    )
    cr_1_27_df = utils.return_file_as_df(filename)
    cr_1_27_df["With Merit (GPA)?"] = cr_1_27_df["GradeAverage"].apply(
        lambda x: x >= 85 and x < 90
    )
    cr_1_27_df["With Honors (GPA)?"] = cr_1_27_df["GradeAverage"].apply(
        lambda x: x >= 90
    )
    cr_1_27_df = cr_1_27_df[
        ["StudentID", "With Merit (GPA)?", "With Honors (GPA)?", "GradeAverage"]
    ]
    cr_1_68_df = cr_1_68_df.merge(cr_1_27_df, on="StudentID", how="left")

    grad_list_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "OffClass",
        "Counselor",
        "IEP",
        "Counselor Certification (Final)",
        "June Grad?",
        "Aug Grad?",
        "Transcript Finalized?",
        "Diploma Type",
        "With Honors (Regents)?",
        "CTE Endorsed?",
        "Math Endorsed?",
        "Science Endorsed?",
        "Arts Endorsed?",
        "With Merit (GPA)?",
        "With Honors (GPA)?",
        "NHS?",
        "Seal of Civic Readiness?",
        "Discharge Code",
        "Diploma Code",
        "Credit Overide Code",
        "Exam Override Code",
        "Post Secondary",
    ]

    for col in grad_list_cols:
        if col not in cr_1_68_df.columns:
            cr_1_68_df[col] = ""
    df = cr_1_68_df[grad_list_cols]
    df = df.sort_values(by=["Counselor", "LastName", "FirstName"])

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    df.to_excel(writer, index=False, sheet_name="StudentsByCounselor")

    cr_1_68_df.to_excel(writer, index=False, sheet_name="Processed_1_68")

    cte_df = cte_df[cte_df["StudentID"].isin(df["StudentID"])]
    cte_df = cte_df.drop_duplicates(subset=["StudentID"])
    cte_df["CTE_Exam_Passed?"] = ""
    cte_df["CTE_Endorsement?"] = ""
    cte_df = cte_df.sort_values(by=["Major", "LastName", "FirstName"])
    cte_df.to_excel(writer, index=False, sheet_name="CTE")

    ## format StudentsByCounselor
    workbook = writer.book
    worksheet = writer.sheets["StudentsByCounselor"]
    worksheet.data_validation(
        1, 7, 1000, 8, {"validate": "list", "source": ["Y", "N", "Maybe", ""]}
    )
    worksheet.data_validation(
        1, 10, 1000, 10, {"validate": "list", "source": ["AR", "R", "L", ""]}
    )

    worksheet.data_validation(
        1, 9, 1000, 9, {"validate": "list", "source": [True, False]}
    )

    worksheet.data_validation(
        1, 11, 1000, 19, {"validate": "list", "source": [True, False]}
    )

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()

    writer.close()
    f.seek(0)

    return f, df
