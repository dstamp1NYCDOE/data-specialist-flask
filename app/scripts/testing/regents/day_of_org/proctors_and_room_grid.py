from app.scripts import scripts, files_df, gsheets_df
from flask import render_template, request, send_file, session, current_app

from io import BytesIO
from reportlab.graphics import shapes
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
import app.scripts.utils.utils as utils
import datetime as dt

import labels

import pandas as pd

PADDING = 1
specs = labels.Specification(
    215.9,
    279.4,
    3,
    10,
    66.675,
    25.2,
    corner_radius=2,
    left_margin=5,
    right_margin=5,
    top_margin=12.75,
    # bottom_margin=13,
    left_padding=PADDING,
    right_padding=PADDING,
    top_padding=PADDING,
    bottom_padding=PADDING,
    row_gap=0.05,
)


def main(course, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        administration = f"January {school_year+1}"
    elif term == 2:
        administration = f"June {school_year+1}"

    gsheet_url = utils.return_gsheet_url_by_title(
        gsheets_df, "regents_exam_book", year_and_semester
    )

    exam_book_df = utils.return_google_sheet_as_dataframe(gsheet_url, sheet="ExamBook")
    proctor_assignments_df = utils.return_google_sheet_as_dataframe(
        gsheet_url, sheet="ProctorAssignments"
    )
    proctor_schedule_df = utils.return_google_sheet_as_dataframe(
        gsheet_url, sheet="ProctorSchedule"
    )

    proctor_assignments_df = proctor_assignments_df.sort_values(by=["proctor#"])
    hall_proctors_df = proctor_assignments_df[
        proctor_assignments_df["Course"].str.contains("Side")
    ]
    hall_proctors_df["Type"] = "Hall Proctor"

    proctor_assignments_df = proctor_assignments_df.merge(
        exam_book_df[["Day", "Time", "Room", "Type"]], on=["Day", "Time", "Room"]
    ).drop_duplicates(subset=["Day", "Time", "Room", "Proctor"])

    document_type = "ProctorLabelsAndGrid"
    if course != "All":
        proctor_assignments_df = proctor_assignments_df[
            proctor_assignments_df["Course"] == course
        ]
        filename = f"{administration}_{course}_{document_type}.pdf"
    else:
        filename = f"{administration}_All_{document_type}.pdf"

    labels_to_make = []
    for (day, time, course), proctors_df in proctor_assignments_df.groupby(
        ["Day", "Time", "Course"]
    ):
        hall_proctors_dff = hall_proctors_df[
            (hall_proctors_df["Day"] == day) & (hall_proctors_df["Time"] == time)
        ]

        for (room, room_type), proctors_dff in proctors_df.groupby(["Room", "Type"]):
            room_dict = {
                "Course": course,
                "Time": time,
                "Day": day,
                "Room": room,
                "Type": room_type,
                "Flag": True,
            }
            labels_to_make.append(room_dict)
            proctors_lst = proctors_dff.to_dict("records")
            if len(proctors_lst) == 0:
                proctors_lst.append({})
                proctors_lst.append({})

            if len(proctors_lst) == 3:
                proctors_lst.insert(2, {})
                proctors_lst.append({})

            if len(proctors_lst) == 6:
                proctors_lst.append({})
                proctors_lst.append({})

            labels_to_make.extend(proctors_lst)

        labels_to_make.extend(hall_proctors_dff.to_dict("records"))

        blank_labels = return_blank_labels(labels_to_make)
        labels_to_make.extend(blank_labels)

        proctors_df = pd.concat([proctors_df, hall_proctors_dff])
        proctors_lst = proctors_df.sort_values(by=["Proctor"]).to_dict("records")
        sub_proctors_df = proctor_schedule_df[
            (proctor_schedule_df["Day"] == day)
            & (proctor_schedule_df["Assignment"].str.contains("SUB"))
        ]
        sub_proctors_df["Type"] = "Sub Proctor"
        sub_proctors_lst = sub_proctors_df.to_dict("records")

        proctors_lst.extend(sub_proctors_lst)

        labels_to_make.extend(proctors_lst)

        blank_labels = return_blank_labels(labels_to_make)
        labels_to_make.extend(blank_labels)

    sheet = labels.Sheet(specs, draw_room_label, border=True)
    sheet.add_labels(labels_to_make)

    f = BytesIO()
    sheet.save(f)
    f.seek(0)
    return f, filename


def return_blank_labels(labels_to_make):
    blank_labels = []
    for i in range(30 - len(labels_to_make) % 30):
        blank_labels.append({})
    return blank_labels


def draw_room_label(label, width, height, obj):
    course_code = obj.get("Course","")
    type = obj.get("Type","")
    room = obj.get("Room","")
    Day = obj.get("Day","")
    Time = obj.get("Time","")

    Proctor = obj.get("Proctor","")
    Flag = obj.get("Flag","")

    if Flag:
        label.add(
            shapes.String(4, 55, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
        )

        label.add(
            shapes.String(4, 30, f"{course_code}", fontName="Helvetica", fontSize=18)
        )

        label.add(
            shapes.String(4, 10, f"{room} - {type}", fontName="Helvetica", fontSize=10)
        )
    if Proctor:
        label.add(
            shapes.String(4, 55, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
        )

        label.add(shapes.String(4, 30, f"{Proctor}", fontName="Helvetica", fontSize=18))

        label.add(
            shapes.String(4, 10, f"{room} - {type}", fontName="Helvetica", fontSize=10)
        )


def draw_proctor_label(label, width, height, obj):
    Type = obj.get("Type", "SUB PROCTOR")
    nickname = obj.get("Proctor","")
    Time = obj.get("Time","")
    Day = obj.get("Day","")
    Room = obj.get("Room", "","")

    label.add(shapes.String(4, 55, f"{Day}-{Time}", fontName="Helvetica", fontSize=10))

    label.add(shapes.String(4, 30, f"{nickname}", fontName="Helvetica", fontSize=18))

    label.add(shapes.String(4, 10, f"{Type} {Room}", fontName="Helvetica", fontSize=10))
