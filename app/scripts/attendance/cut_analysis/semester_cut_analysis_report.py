from io import BytesIO
import pandas as pd

from flask import session

from app.scripts.attendance.jupiter.process import process_local_file as process_jupiter


def main():

    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"

    student_period_attendance_df = process_jupiter()

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    cuts_df = student_period_attendance_df[student_period_attendance_df["cutting?"]]
    cuts_df.to_excel(writer, sheet_name="cuts_raw", index=False)

    cuts_pvt = pd.pivot_table(
        cuts_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc='count',
    ).fillna("")
    cuts_pvt.columns = [f"Pd_{col}_cuts" for col in cuts_pvt.columns] 
    cuts_pvt = cuts_pvt.reset_index()

    class_grades_pvt = pd.pivot_table(
        student_period_attendance_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="ClassGrade",
        aggfunc="max",
    ).fillna("")
    class_grades_pvt.columns = [f"Pd_{col}_Grade" for col in class_grades_pvt.columns] 
    class_grades_pvt = class_grades_pvt.reset_index()

    teacher_pvt = pd.pivot_table(
        student_period_attendance_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc="max",
    ).fillna("")
    teacher_pvt.columns = [f"Pd_{col}_Teacher" for col in teacher_pvt.columns] 
    teacher_pvt = teacher_pvt.reset_index()

    cuts_pvt = cuts_pvt.merge(class_grades_pvt, on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"], how="right")
    cuts_pvt = cuts_pvt.merge(teacher_pvt, on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"], how="right")

    num_of_cuts_df = student_period_attendance_df[
        ["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs", "num_of_cuts"]
    ].drop_duplicates()
    cuts_pvt = num_of_cuts_df.merge(
        cuts_pvt,
        on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        how="right",
    )
    cuts_pvt = cuts_pvt.sort_values(by=["num_of_cuts"], ascending=[False])
    cuts_pvt.to_excel(writer, sheet_name="cuts", index=False)

    attendance_errors_df = student_period_attendance_df[
        student_period_attendance_df["attd_error"]
    ]
    cols = [
        "Teacher",
        "Date",
        "Course",
        "Section",
        "Pd",
        "Type",
        "LastName",
        "FirstName",
    ]
    attendance_errors_df = attendance_errors_df[cols].sort_values(
        by=["Teacher", "Pd", "Course", "Section"]
    )
    attendance_errors_df.to_excel(writer, sheet_name="attd_errors", index=False)

    cutting_by_teacher_by_class_pvt = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Teacher", "Course", "Section", "Pd"],
            columns=["Type", "cutting?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    cutting_by_teacher_by_class_pvt.to_excel(
        writer, sheet_name="attd_by_teacher_and_course"
    )

    attd_by_day_and_pd = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Date", "Pd"],
            columns=["Type", "cutting?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    attd_by_day_and_pd.to_excel(writer, sheet_name="attd_by_date_and_period")

    attd_by_date = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Date"],
            columns=["Type", "cutting?","late_to_school?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    attd_by_date.to_excel(writer, sheet_name="attd_by_date")

    ## late to school
    late_to_school_df = student_period_attendance_df[
        student_period_attendance_df["late_to_school?"]
        & (~student_period_attendance_df["Type"].isin(["tardy"]))
    ]
    late_to_school_pvt = pd.pivot_table(
        late_to_school_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc="count",
    ).fillna("")
    late_to_school_pvt = late_to_school_pvt.reset_index()

    num_of_late_to_school_df = student_period_attendance_df[
        [
            "StudentID",
            "LastName",
            "FirstName",
            "Counselor",
            "year_in_hs",
            "num_of_late_to_school",
        ]
    ].drop_duplicates()
    late_to_school_pvt = num_of_late_to_school_df.merge(
        late_to_school_pvt,
        on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        how="right",
    )
    late_to_school_pvt = late_to_school_pvt.sort_values(
        by=["num_of_late_to_school"], ascending=[False]
    )
    late_to_school_pvt.to_excel(writer, sheet_name="late_to_school", index=False)



    writer.close()
    f.seek(0)

    download_name = f"JupiterCutReport-{year_and_semester}.xlsx"
    return f, download_name
