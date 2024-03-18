import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df


def process_spreadsheet(form, request):
    survey_responses = request.files[form.survey_responses.name]
    surveys_dict = pd.read_excel(survey_responses, sheet_name=None)

    surveys_df = pd.concat(surveys_dict.values())

    filename = utils.return_most_recent_report(files_df, "3_07")
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]

    surveys_df = surveys_df.merge(student_info_df, on=["StudentID"]).dropna()
    surveys_df = surveys_df.drop_duplicates(
        subset=["StudentID", "Which Career Day presenter are you signing up for?"]
    )
    surveys_df = surveys_df.sort_values(
        by=["Which Career Day presenter are you signing up for?"]
    )

    student_lst = []
    groupby_cols = ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    for (StudentID, LastName, FirstName, Email), sessions_df in surveys_df.groupby(
        groupby_cols
    ):
        for i, selection in enumerate(
            sessions_df["Which Career Day presenter are you signing up for?"]
        ):
            if i == 0:
                temp_dict = {
                    "StudentID": StudentID,
                    "LastName": LastName,
                    "FirstName": FirstName,
                }
                if StudentID % 2 == 0:
                    temp_dict["Session"] = 1
                    temp_dict["Presenter"] = selection
                else:
                    temp_dict["Session"] = 2
                    temp_dict["Presenter"] = selection
            if i == 1:
                temp_dict = {
                    "StudentID": StudentID,
                    "LastName": LastName,
                    "FirstName": FirstName,
                }
                if StudentID % 2 == 0:
                    temp_dict["Session"] = 2
                    temp_dict["Presenter"] = selection
                else:
                    temp_dict["Session"] = 1
                    temp_dict["Presenter"] = selection

            student_lst.append(temp_dict)

    assignments_df = pd.DataFrame(student_lst)

    counts_df = pd.pivot_table(
        assignments_df,
        index="Presenter",
        columns="Session",
        values="StudentID",
        aggfunc="count",
    )

    return counts_df
