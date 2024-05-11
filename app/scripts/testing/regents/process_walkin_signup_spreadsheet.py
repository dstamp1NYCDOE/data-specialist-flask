import pandas as pd
import numpy as np

from app.scripts.testing.regents import create_walkin_signup_spreadsheet


def main(form, request):
    walkin_spreadsheet_file = request.files[form.walkin_spreadsheet_file.name]

    updated_df = pd.read_excel(walkin_spreadsheet_file, sheet_name=0, skiprows=1)
    updated_df = updated_df.melt(
        id_vars=["StudentID", "LastName", "FirstName", "Counselor"],
        var_name="Course",
        value_name="final_signup?",
    )

    original_df = create_walkin_signup_spreadsheet.main()

    original_df = original_df.melt(
        id_vars=["StudentID", "LastName", "FirstName", "Counselor"],
        var_name="Course",
        value_name="current_registration?",
    )

    merged_df = pd.merge(
        updated_df,
        original_df,
        on=["StudentID", "LastName", "FirstName", "Counselor", "Course"],
        how="left",
    ).fillna(False)

    changes_df = merged_df[
        merged_df["final_signup?"] != merged_df["current_registration?"]
    ]

    changes_df["Action"] = merged_df["final_signup?"].apply(
        lambda x: "Add" if x else "Drop"
    )

    cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "GradeLevel",
        "OfficialClass",
        "Course",
        "Section",
        "Action",
    ]
    changes_df["GradeLevel"] = ""
    changes_df["OfficialClass"] = ""
    changes_df["Section"] = 1

    changes_df = changes_df[cols]

    return changes_df
