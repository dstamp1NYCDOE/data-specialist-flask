import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
from flask import session

from reportlab.graphics import shapes

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    student_info_df = utils.return_file_as_df(filename).fillna("")
    student_info_df["Zip"] = student_info_df["Zip"].apply(lambda x: str(x).zfill(5))

    filename = utils.return_most_recent_report(files_df, "rosters_and_grades")
    rosters_df = utils.return_file_as_df(filename)
    rosters_df = rosters_df[["StudentID", "Course", "Section"]].drop_duplicates()

    filename = utils.return_most_recent_report(files_df, "jupiter_master_schedule")
    master_schedule = utils.return_file_as_df(filename).fillna("")
    master_schedule = master_schedule[
        ["Course", "Section", "Room", "Teacher1", "Teacher2", "Period"]
    ]

    df = rosters_df.merge(master_schedule, on=["Course", "Section"], how="left").fillna(
        ""
    )
    df = df.merge(student_info_df, on="StudentID", how="left")

    df = df.dropna(subset=["Zip"])

    ## periods
    periods = form.periods.data
    if "ALL" in periods:
        pass
    else:
        periods = [x for x in periods if x != "ALL"]
        period_regex_match = "".join(periods)
        df = df[df["Period"].str.contains(f"[{period_regex_match}]")]

    f = BytesIO()

    teachers_lst = pd.unique(df[["Teacher1"]].values.ravel("K"))

    teachers_lst.sort()

    labels_to_make = []
    for teacher in teachers_lst:
        students_df = df[df["Teacher1"] == teacher]
        teacher_label = {"Teacher": teacher}
        labels_to_make.append(teacher_label)
        labels_to_make.extend(students_df.to_dict("records"))

        num_of_students = len(students_df)

        if num_of_students <= 29:
            num_of_blank_labels = 29 - num_of_students
        else:
            num_of_blank_labels = 30 - (num_of_students - 29)

        for i in range(num_of_blank_labels):
            blank_label = {}
            labels_to_make.append(blank_label)

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)
    f.seek(0)

    # return ""
    return f


import labels

PADDING = 0
specs = labels.Specification(
    215.9,
    279.4,
    3,
    10,
    66.6,
    25.2,
    corner_radius=2,
    left_margin=5,
    right_margin=5,
    top_margin=12.25,
    # bottom_margin=13,
    left_padding=PADDING,
    right_padding=PADDING,
    top_padding=PADDING,
    bottom_padding=PADDING,
    row_gap=0,
)


def draw_label(label, width, height, obj):
    if obj.get("Teacher"):
        teacher_name = f"{obj['Teacher']}"
        label.add(
            shapes.String(
                5,
                40,
                teacher_name,
                fontName="Helvetica",
                fontSize=24,
            )
        )

    elif obj.get("LastName"):
        student_name = f"Parent of: {obj['LastName']}, {obj['FirstName']}"

        label.add(
            shapes.String(
                5,
                50,
                student_name,
                fontName="Helvetica",
                fontSize=10,
            )
        )

        AptNum = obj["AptNum"]
        street = obj["Street"]
        city = obj["City"]
        state = obj["State"]
        zipcode = obj["Zip"]

        if AptNum != "":
            street_address = f"{street}, {AptNum}"
        else:
            street_address = f"{street}"

        label.add(
            shapes.String(
                5,
                30,
                street_address,
                fontName="Helvetica",
                fontSize=10,
            )
        )

        label.add(
            shapes.String(
                5,
                15,
                f"{city}, {state} {zipcode}",
                fontName="Helvetica",
                fontSize=10,
            )
        )

    else:
        pass
