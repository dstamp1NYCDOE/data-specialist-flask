from flask import session, current_app
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

import labels
from reportlab.graphics import shapes
from reportlab.lib import colors

from app.scripts.summer.testing.regents_organization import (
    utils as regents_organization_utils,
)

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


def main(form, request):
    filename = "ProctorTimeCardLabels.pdf"
    proctor_assignments_csv = request.files[form.proctor_assignments_csv.name]
    proctor_assignments_df = pd.read_csv(proctor_assignments_csv)
    proctor_assignments_df = proctor_assignments_df.sort_values(by=["Day", "Time"])

    proctor_assignments_pvt_df = pd.pivot_table(
        proctor_assignments_df.drop_duplicates(subset=["Name", "File#", "Day"]),
        index=["Name", "File#"],
        columns=["Day"],
        values="Hours",
        aggfunc=lambda x: x,
    ).reset_index()
    print(proctor_assignments_pvt_df)

    proctors_df = proctor_assignments_df.drop_duplicates(
        subset=["Name", "File#"], keep="first"
    )
    proctors_df = proctors_df.sort_values(by=["Name"])
    proctors_df = proctors_df.merge(
        proctor_assignments_pvt_df, on=["Name", "File#"], how="left"
    ).fillna("")

    proctors_df = proctors_df.sort_values(by=["Name"])

    labels_to_make = []
    # for (day, time), proctors_dff in proctors_df.groupby(["Day", "Time"]):
    #     labels_to_make.extend(proctors_dff.to_dict("records"))
    #     remainder = len(labels_to_make) % 30
    #     for i in range(30 - remainder):
    #         labels_to_make.append({})

    labels_to_make.extend(proctors_df.to_dict("records"))

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    return f, filename


def draw_label(label, width, height, obj):
    if obj:
        label.add(
            shapes.String(
                4,
                52,
                f'{obj["Name"]}',
                fontName="Helvetica",
                fontSize=17,
            )
        )
        label.add(
            shapes.String(
                4,
                40,
                f'File#: {obj["File#"]}',
                fontName="Helvetica",
                fontSize=12,
            )
        )

        label.add(
            shapes.String(
                4,
                30,
                f'Check-In: {obj["Day"]} - {obj["Time"]}',
                fontName="Helvetica",
                fontSize=10,
            )
        )

        label.add(
            shapes.String(
                4,
                18,
                f"8/19/2024",
                fontName="Helvetica",
                fontSize=9,
            )
        )
        label.add(
            shapes.String(
                4,
                10,
                f"{obj['8/19/2024']}",
                fontName="Helvetica",
                fontSize=7,
            )
        )

        label.add(
            shapes.String(
                55,
                18,
                f"8/20/2024",
                fontName="Helvetica",
                fontSize=9,
            )
        )
        label.add(
            shapes.String(
                55,
                10,
                f"{obj['8/20/2024']}",
                fontName="Helvetica",
                fontSize=7,
            )
        )

        label.add(
            shapes.String(
                110,
                18,
                f"8/21/2024",
                fontName="Helvetica",
                fontSize=9,
            )
        )
        label.add(
            shapes.String(
                110,
                10,
                f"{obj['8/21/2024']}",
                fontName="Helvetica",
                fontSize=7,
            )
        )
