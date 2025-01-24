import pandas as pd
from io import BytesIO

import app.scripts.testing.regents.proctoring.process_proctors_needed as process_proctors_needed
import app.scripts.testing.regents.proctoring.assign_proctors as assign_proctors
import app.scripts.testing.regents.proctoring.proctor_schedule as proctor_schedule

import app.scripts.testing.regents.proctoring.utils as utils


def main(form, request):
    exam_book_filename = request.files[form.exam_book.name]
    exam_book_df = pd.read_csv(exam_book_filename)

    proctor_assignments_df = process_proctors_needed.main(exam_book_df)

    proctor_availability_filename = request.files[form.proctor_availability.name]
    proctor_availability_df = pd.read_csv(proctor_availability_filename).dropna()
    proctor_availability_df = proctor_availability_df.set_index("Name", drop=False)

    proctor_assignments_df = assign_proctors.main(
        proctor_assignments_df, proctor_availability_df
    )
    proctor_schedule_df = proctor_schedule.main(
        proctor_assignments_df, proctor_availability_df
    )

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    proctor_assignments_df.to_excel(
        writer, sheet_name="ProctorAssignments", index=False
    )
    proctor_schedule_df.to_excel(writer, sheet_name="ProctorSchedule", index=False)

    # return ""
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 0)
        worksheet.autofit()

    writer.close()

    f.seek(0)
    return f
