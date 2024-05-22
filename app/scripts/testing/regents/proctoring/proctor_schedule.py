import pandas as pd  #


def main(proctor_assignments_df, proctor_availability_df):
    proctor_schedule_df = proctor_assignments_df[["Day", "Time", "Proctor"]]
    proctor_schedule_df["Assignment"] = "Proctor"

    non_proctor_assignment_list = []
    for day in proctor_assignments_df["Day"].value_counts().index.to_list():
        non_proctors = proctor_availability_df[
            ~proctor_availability_df[day].isin(["Proctor"])
        ]
        
        for index, non_proctor_assignment in non_proctors.iterrows():
            temp_dict = {
                "Day": day,
                "Assignment": non_proctor_assignment[day],
                "Proctor": non_proctor_assignment["Name"],
            }
            if non_proctor_assignment[day] == "SUB PROCTOR":
                temp_dict["Time"] = (
                    "AM" if non_proctor_assignment["Session"] == "Early" else "Late"
                )
            if "SCORING" not in non_proctor_assignment[day]:
                temp_dict["Time"] = (
                    "AM" if non_proctor_assignment["Session"] == "Early" else "Late"
                )
            non_proctor_assignment_list.append(temp_dict)

    non_proctor_assignment_df = pd.DataFrame(non_proctor_assignment_list)
    proctor_schedule_df = pd.concat(
        [proctor_schedule_df, non_proctor_assignment_df]
    ).fillna("")
    return proctor_schedule_df
