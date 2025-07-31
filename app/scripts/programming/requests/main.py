import pandas as pd
import numpy as np

import app.scripts.programming.requests.process_transcript as process_transcript
import app.scripts.programming.requests.process_register as process_register
import app.scripts.programming.requests.process_ieps as process_ieps
import app.scripts.programming.requests.process_majors as process_majors


import app.scripts.programming.requests.ELA_request as ELA_request
import app.scripts.programming.requests.SS_request as SS_request
import app.scripts.programming.requests.Sci_request as Sci_request
import app.scripts.programming.requests.math_request as math_request
import app.scripts.programming.requests.PE_request as PE_request
import app.scripts.programming.requests.CTE_request as CTE_request
import app.scripts.programming.requests.spanish_request as spanish_request
import app.scripts.programming.requests.session_request as session_request
import app.scripts.programming.requests.finalize_requests as finalize_requests

from app.scripts.attendance.process_RATR import student_lateness_overall

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO

def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"    
    cr_1_14_filename = utils.return_most_recent_report_by_semester(files_df, "1_14",year_and_semester=year_and_semester)
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)

    ## attach numeric equivalent
    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent","PassFailEquivalent"]], on=["Mark"], how="left"
    )




    transcript_df = process_transcript.main(cr_1_14_df)

    students_with_transcripts = cr_1_14_df["StudentID"].unique()
    

    cr_3_07_filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    register_df = utils.return_file_as_df(cr_3_07_filename)
    register_df = process_register.main(register_df)

    register_df = register_df[register_df["StudentID"].isin(students_with_transcripts)]

    recommended_programs_filename = utils.return_most_recent_report_by_semester(
        files_df, "Recommended_Programs",year_and_semester=year_and_semester
    )
    iep_df = utils.return_file_as_df(recommended_programs_filename, skiprows=1)
    iep_dict = process_ieps.main(iep_df)

    cr_1_01_filename = utils.return_most_recent_report_by_semester(files_df, "1_01",year_and_semester=year_and_semester)
    programs_df = utils.return_file_as_df(cr_1_01_filename)
    majors_dict = process_majors.main(programs_df)

    RATR_filename = utils.return_most_recent_report_by_semester(files_df, "RATR",year_and_semester=year_and_semester)
    RATR_df = utils.return_file_as_df(RATR_filename)
    student_lateness_df = student_lateness_overall(RATR_df)
    

    student_lateness_df = student_lateness_df.merge(register_df, on=['StudentID'], how='right')
    
    best_on_time_students_by_year_in_hs = student_lateness_df.sort_values(by=["ytd_lateness_%"]).groupby('year_in_hs').head(150).reset_index(drop=True)['StudentID'].to_list()
    


    output_list = []

    for index, student in register_df.iterrows():
        year_in_hs = student["year_in_hs"]
        StudentID = student["StudentID"]
        student_transcript = transcript_df.loc[StudentID]
        student_iep = iep_dict.get(StudentID)

        student_courses = []

        if year_in_hs > 4:
            student_courses.append("ZA")
        else:
            student_courses.extend(
                ELA_request.main(student, student_transcript, student_iep)
            )
            student_courses.extend(
                SS_request.main(student, student_transcript, student_iep)
            )
            student_courses.extend(
                Sci_request.main(student, student_transcript, student_iep)
            )
            student_courses.extend(
                math_request.main(student, student_transcript, student_iep)
            )
            student_courses.extend(
                PE_request.main(student, student_transcript, student_iep)
            )

            student_courses.extend(
                CTE_request.main(student, student_transcript, majors_dict)
            )

            student_courses.extend(spanish_request.main(student, student_transcript))

            
            student_courses.extend(
                session_request.main(
                    student, student_transcript, best_on_time_students_by_year_in_hs)
            )

            student_courses.extend(["ZL"])

            student_courses = [course for course in student_courses if course != ""]

            student_courses = finalize_requests.finalize_student_requests(
                student, student_courses, student_transcript, student_iep
            )

        student_dict = {
            "StudentID": StudentID,
            "year_in_hs": year_in_hs,
            "student_courses": student_courses,
        }

        output_list.append(student_dict)

    wide_format = []
    long_format = []

    for student in output_list:
        StudentID = student["StudentID"]
        year_in_hs = student["year_in_hs"]
        wide_format_dict = {"StudentID": StudentID, "year_in_hs": year_in_hs}
        long_format_dict = {"StudentID": StudentID, "year_in_hs": year_in_hs}

        i = 0
        for course in student["student_courses"]:
            i += 1
            long_format_dict["Course"] = course
            if course != "":
                long_format.append(long_format_dict.copy())

            wide_format_dict[f"Course{i}"] = course

        wide_format.append(wide_format_dict)

    wide_format_df = pd.DataFrame(wide_format)
    long_format_df = pd.DataFrame(long_format)

    requests_pivot_tbl = pd.pivot_table(
        long_format_df,
        values="StudentID",
        columns="year_in_hs",
        index="Course",
        aggfunc="count",
        margins=True,
    ).fillna(0)

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    wide_format_df.to_excel(writer, sheet_name="WideFormat", index=False)
    long_format_df.to_excel(writer, sheet_name="LongFormat", index=False)
    requests_pivot_tbl.to_excel(
        writer,
        sheet_name="counts",
    )

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.autofit()

    writer.close()

    f.seek(0)
    download_name = f"Fall_{school_year+1}_course_requests.xlsx"
    return f, download_name


if __name__ == "__main__":
    main()
