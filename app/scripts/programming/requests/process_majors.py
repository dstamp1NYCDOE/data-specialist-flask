import pandas as pd
import numpy as np

import app.scripts.cte_data as cte_data


def main(programs_df):
    cte_courses_dict = cte_data.CTE_COURSE_TO_MAJOR

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
