import pandas as pd
import numpy as np


def main(programs_df):
    cte_courses_dict = {
        "ACS11TD": "A&D",
        "AES11TE": "A&D",
        "ANS11": "A&D",
        "AGS11": "A&D",
        "ALS22": "A&D",
        "APS11T": "A&D",
        "AUS11TA": "A&D",
        "AFS62TF": "FD",
        "AFS64TD": "FD",
        "AFS64TDB": "FD",
        "AFS64TDC": "FD",
        "AFS66QC": "FD",
        "AFS66QCH": "FD",
        "AUS11": "FD",
        "AWS11": "FD",
        "AYS11": "FMM",
        "ABS11": "FMM",
        "BKS11TE": "FMM",
        "BNS22QV": "FMM",
        "BQS11QQI": "FMM",
        "BRS11TF": "FMM",
        "BQS11T": "FMM",
        "ACS21TD": "Photo",
        "ACS22TD": "Photo",
        "ALS22QP": "Photo",
        "BMS62TD": "VP",
        "BMS64TP": "VP",
        "BMS66QW": "VP",
        "SKS22X": "WD",
        "TQS22TQW": "WD",
    }

    programs_df = programs_df[programs_df["Course"].isin(cte_courses_dict.keys())]

    programs_df["major"] = programs_df["Course"].apply(
        lambda x: cte_courses_dict.get(x)
    )

    programs_df = programs_df[["StudentID", "major"]]
    programs_df = programs_df.drop_duplicates(subset=["StudentID"])
    programs_df = programs_df.set_index("StudentID")

    majors_dict = programs_df.to_dict("index")

    majors_dict = {StudentID: v["major"] for (StudentID, v) in majors_dict.items()}

    return majors_dict


if __name__ == "__main__":
    programs_df = pd.read_excel("data/1_01.xlsx")
    main(programs_df)
