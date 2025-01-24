import pandas as pd
import numpy as np

import app.scripts.testing.regents.proctoring.utils as utils


def main(exam_book_df):
    ## drop empty sections
    exam_book_df = exam_book_df[exam_book_df["Active"] > 0]
    ## drop lab ineligible holding
    exam_book_df = exam_book_df[exam_book_df["Section"] != 88]

    exam_book_df["assignment_difficulty"] = exam_book_df.apply(
        utils.return_assignment_difficulty, axis=1
    )
    exam_book_df = exam_book_df.sort_values(by=["assignment_difficulty"])

    rooms_df = exam_book_df.drop_duplicates(
        subset=["Day", "Time", "Course", "Room"], keep="last"
    )

    rooms_df["number_of_proctors_needed"] = rooms_df.apply(
        utils.return_number_of_proctors_needed, axis=1
    )

    list_of_proctoring_assignments = []

    hall_proctors_lst = return_hall_proctor_need(rooms_df)
    list_of_proctoring_assignments.extend(hall_proctors_lst)

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


def return_hall_proctor_need(rooms_df):
    rooms_df = rooms_df.copy()
    rooms_df["Room"] = rooms_df["Room"].apply(lambda x: str(x)[0] + "th Floor")
    rooms_df = rooms_df.sort_values(by=["assignment_difficulty"])

    floors_df = rooms_df.drop_duplicates(subset=["Day", "Time", "Room"], keep="last")
    floors_df = floors_df.sort_values(by=["Day", "Time", "Room"])
    floors_df = floors_df[floors_df["Type"] != "SCRIBE"]

    hall_proctors_lst = []
    for (day, TIME), df in floors_df.groupby(["Day", "Time"]):
        for floor in df["Room"].to_list():
            for i, j in [(1, "StudentSide"), (2, "StaffSide")]:
                temp_dict = {
                    "ExamTitle": "HallProctor",
                    "Course": j,
                    "Day": day,
                    "Time": TIME,
                    "Room": floor,
                    "assignment_difficulty": 1.25,
                    "proctor#": i,
                }
                hall_proctors_lst.append(temp_dict)
        ## pull in extended time AM floors
        dff = df[df["assignment_difficulty"] > 1]
        for floor in dff["Room"].to_list():
            for i, j in [(1, "StudentSide"), (2, "StaffSide")]:
                temp_dict = {
                    "ExamTitle": "HallProctor",
                    "Course": j,
                    "Day": day,
                    "Time": "PM",
                    "Room": floor,
                    "assignment_difficulty": 1.25,
                    "proctor#": i,
                }
                hall_proctors_lst.append(temp_dict)
    ## remove duplicates
    hall_proctors_df = pd.DataFrame(hall_proctors_lst)
    hall_proctors_df = hall_proctors_df.drop_duplicates()

    hall_proctors_lst = hall_proctors_df.to_dict("records")
    return hall_proctors_lst
