import pandas as pd
import numpy as np

import app.scripts.testing.regents.proctoring.utils as utils


def main(exam_book_df):
    ## drop empty sections
    exam_book_df = exam_book_df[exam_book_df['Active']>0]
    ## drop lab ineligible holding
    exam_book_df = exam_book_df[exam_book_df['Section']!=88]

    exam_book_df["assignment_difficulty"] = exam_book_df.apply(
        utils.return_assignment_difficulty, axis=1
    )
    exam_book_df = exam_book_df.sort_values(by=["assignment_difficulty"])

    rooms_df = exam_book_df.drop_duplicates(subset=["Day", "Time", "Room"], keep="last")

    rooms_df["number_of_proctors_needed"] = rooms_df.apply(
        utils.return_number_of_proctors_needed, axis=1
    )

    proctors_needed_by_day_by_session = pd.pivot_table(
        rooms_df,
        index="Day",
        columns="Time",
        values="number_of_proctors_needed",
        aggfunc="sum",
        margins=True,
    )
    

    list_of_proctoring_assignments = []

    for index, room in rooms_df.iterrows():
        number_of_proctors_needed = room["number_of_proctors_needed"]
        for i in range(1, number_of_proctors_needed + 1):
            temp_dict = {
                "ExamTitle": room["ExamTitle"],
                "Course": room["Course Code"],
                "Day": room["Day"],
                "Time": room["Time"],
                "Room": room["Room"],
                "assignment_difficulty": room["assignment_difficulty"],
                "proctor#": i,
            }
            list_of_proctoring_assignments.append(temp_dict)

    proctors_needed_df = pd.DataFrame(list_of_proctoring_assignments)
    
    return proctors_needed_df
