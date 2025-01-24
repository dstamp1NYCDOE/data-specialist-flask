import pandas as pd
import numpy as np


def main(proctor_assignments_df, proctor_availability_df):
    assignments_days_in_order = (
        proctor_assignments_df["Day"].value_counts().index.to_list()
    )

    proctor_availability_df["dept_code"] = proctor_availability_df["Dept"].apply(
        convert_dept_to_code
    )

    proctors_dict = {}
    assigned_proctors_by_day = {}
    proctor_assignments_list = []

    for day in assignments_days_in_order:

        assignments_to_make = proctor_assignments_df[
            proctor_assignments_df["Day"] == day
        ]

        assignments_to_make = assignments_to_make.sort_values(
            by=["Time", "proctor#", "assignment_difficulty"],
            ascending=[False, True, False],
        )

        if len(assignments_to_make) == 0:
            continue

        assigned_proctors_by_day[day] = []
        possible_proctors = proctor_availability_df[
            proctor_availability_df[day] == "Proctor"
        ]
        possible_proctors = possible_proctors.sort_values(
            by=["total_difficulty", "#_of_proctor_days"]
        )

        AM_possible_proctors = possible_proctors[
            possible_proctors["Session"] == "Early"
        ]["Name"].to_list()

        PM_possible_proctors = possible_proctors[
            possible_proctors["Session"] == "Late"
        ]["Name"].to_list()

        proctors_by_assignment_type = {
            "AM": {
                1: AM_possible_proctors + PM_possible_proctors,
                2: AM_possible_proctors + PM_possible_proctors,
                3: AM_possible_proctors + PM_possible_proctors,
                4: AM_possible_proctors + PM_possible_proctors,
                5: AM_possible_proctors + PM_possible_proctors,
                6: AM_possible_proctors + PM_possible_proctors,
                7: AM_possible_proctors + PM_possible_proctors,
                8: AM_possible_proctors + PM_possible_proctors,
                9: AM_possible_proctors + PM_possible_proctors,
            },
            "PM": {
                1: PM_possible_proctors + AM_possible_proctors,
                2: PM_possible_proctors + AM_possible_proctors,
                3: PM_possible_proctors + AM_possible_proctors,
                4: PM_possible_proctors,
                5: PM_possible_proctors,
                6: PM_possible_proctors,
                7: PM_possible_proctors,
                8: PM_possible_proctors,
                9: PM_possible_proctors,
            },
        }

        for index, proctor_assignment in assignments_to_make.iterrows():
            time = proctor_assignment["Time"]

            proctor_type = proctor_assignment["proctor#"]
            assignment_difficulty = proctor_assignment["assignment_difficulty"]
            proctors_to_pick_from = proctors_by_assignment_type[time][proctor_type]

            proctors_to_pick_from = [
                teacher
                for teacher in proctors_to_pick_from
                if teacher not in assigned_proctors_by_day[day]
            ]

            assigned_proctor = return_proctor(proctors_to_pick_from, proctors_dict)

            cumulative_difficulty = 0
            if proctors_dict.get(assigned_proctor) is None:
                proctors_dict[assigned_proctor] = assignment_difficulty
                cumulative_difficulty += assignment_difficulty
            else:
                cumulative_difficulty = (
                    proctors_dict[assigned_proctor] + assignment_difficulty
                )
                proctors_dict[assigned_proctor] = (
                    proctors_dict[assigned_proctor] + assignment_difficulty
                )

            assigned_proctors_by_day[day].append(assigned_proctor)

            temp_dict = {
                "Course": proctor_assignment["Course"],
                "Time": proctor_assignment["Time"],
                "Day": proctor_assignment["Day"],
                "Room": proctor_assignment["Room"],
                "proctor#": proctor_type,
                "Proctor": assigned_proctor,
                "assignment_difficulty": assignment_difficulty,
            }
            proctor_assignments_list.append(temp_dict)
            proctor_availability_df.at[assigned_proctor, "total_difficulty"] = (
                cumulative_difficulty
            )

    proctor_assignments_dff = pd.DataFrame(proctor_assignments_list)
    total_assignment_difficulty_df = pd.DataFrame(
        proctors_dict.items(), columns=["Proctor", "total_assignment_difficulty"]
    )

    proctor_assignments_dff = proctor_assignments_dff.merge(
        total_assignment_difficulty_df, on=["Proctor"], how="left"
    )
    proctor_assignments_dff = proctor_assignments_dff.sort_values(
        by=["Day", "Time", "Course", "Room", "proctor#"]
    )
    return proctor_assignments_dff


def convert_dept_to_code(dept):
    dept_to_code_dict = {
        "admin": "X",
        "administration": "X",
        "CTE": "CTE",
        "cte": "cte",
        "D75": "X",
        "ELA": "E",
        "math": "M",
        "PE": "P",
        "science": "S",
        "social studies": "H",
        "spanish": "F",
        "speech": "X",
    }
    return dept_to_code_dict[dept]


def return_proctor(proctors_to_pick_from, proctors_dict):
    for num_of_assignments in np.arange(0, 1000, 0.25):
        for proctor in proctors_to_pick_from:
            if proctors_dict.get(proctor, -1) < num_of_assignments:
                return proctor
