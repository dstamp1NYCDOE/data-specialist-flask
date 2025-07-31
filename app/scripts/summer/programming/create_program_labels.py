import pandas as pd
import numpy as np
import os
from io import BytesIO
from zipfile import ZipFile

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df, photos_df

from flask import current_app, session

import pandas as pd
import numpy as np
import datetime as dt
import os


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


def main():
    flowables_dict = {}

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    flowables_dict["school_year"] = int(school_year)

    filename = utils.return_most_recent_report_by_semester(
        files_df, "MasterSchedule", year_and_semester
    )
    master_schedule_df = utils.return_file_as_df(filename)
    master_schedule_df = master_schedule_df.rename(columns={"Course Code": "Course"})
    master_schedule_df["Cycle"] = master_schedule_df["Days"].apply(
        convert_days_to_cycle
    )
    code_deck = master_schedule_df[["Course", "Course Name"]].drop_duplicates()
    master_schedule_df = master_schedule_df[["Course", "Section", "Cycle"]]

    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester
    )

    cr_1_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(
        path, sheet_name=f"{school_year}-{term}"
    ).dropna()
    regents_calendar_df["Date"] = regents_calendar_df["Day"].apply(
        lambda x: x.strftime("%A, %B %e, %Y")
    )

    cr_1_01_df = cr_1_01_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )

    cr_1_01_df = cr_1_01_df.merge(
        master_schedule_df, on=["Course", "Section"], how="left"
    )
    cr_1_01_df = cr_1_01_df.merge(code_deck, on=["Course"], how="left")

    for schedule_col, schedule_dict in [
        ("Start", {1: "7:45AM", 2: "9:49AM", 3: "12:24PM"}),
        ("End", {1: "9:48AM", 2: "11:52AM", 3: "2:27PM"}),
        ("Latest Admit", {1: "8:10AM", 2: "10:14AM", 3: "12:49PM"}),
    ]:
        cr_1_01_df[schedule_col] = cr_1_01_df["Period"].apply(
            lambda x: schedule_dict.get(x)
        )

    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school", "school_name"]]

    student_classes_df = cr_1_01_df.merge(cr_s_01_df, on=["StudentID"], how="left")
    student_classes_df = student_classes_df.merge(
        photos_df, on=["StudentID"], how="left"
    )
    group_by_cols = ["LastName", "FirstName", "StudentID"]

    student_classes_df = student_classes_df.drop_duplicates(
        subset=["StudentID", "Course"]
    )
    student_classes_df = student_classes_df[student_classes_df["Course"].str[0] != "Z"]
    student_classes_df = student_classes_df.fillna({"Room": 0})
    student_classes_df["Room"] = student_classes_df["Room"].apply(lambda x: int(x))
    student_classes_df = student_classes_df[student_classes_df["Period"].isin([1, 2, 3])]

    labels_to_make = []
    for school_name, student_classes_dff in student_classes_df.groupby("school_name"):
        for (LastName, FirstName, StudentID), class_schedule_df in student_classes_dff.groupby(
            group_by_cols
        ):
            student_dict = {
                "school_name": school_name,
                "LastName": LastName,
                "FirstName": FirstName,
                "StudentID": StudentID,
                "P1": class_schedule_df[class_schedule_df["Period"] == 1].to_dict('records'),
                "P2": class_schedule_df[class_schedule_df["Period"] == 2].to_dict('records'),
                "P3": class_schedule_df[class_schedule_df["Period"] == 3].to_dict('records'),
            }

            labels_to_make.append(student_dict)

        next_remainder = len(labels_to_make) % 30

        blanks_to_add = 0
        if next_remainder == 0:
            blanks_to_add += 0
        else:
            if len(labels_to_make) % 3 == 0:
                blanks_to_add += 0
            elif len(labels_to_make) % 3 == 1:
                blanks_to_add += 2
            elif len(labels_to_make) % 3 == 2:
                blanks_to_add += 1
            if (len(labels_to_make) + blanks_to_add) % 30 != 0:
                blanks_to_add += 3
        for i in range(blanks_to_add):
            labels_to_make.append({})

    f = BytesIO()
    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    
    return f

from reportlab.graphics import shapes
from reportlab.lib import colors
def draw_label(label, width, height, obj):
    if obj:
        label.add(shapes.String(4,55,f'{obj['LastName']}, {obj["FirstName"]} ({obj['StudentID']})',fontName="Helvetica",fontSize=9,))
        label.add(shapes.String(4,45,f'{obj['school_name']}',fontName="Helvetica",fontSize=7,))

        spacing = 70
        if obj['P1']:
            label.add(shapes.String(4,25,f'P1',fontName="Helvetica-Bold",fontSize=10,))
            for i, course in enumerate(obj['P1']):
                label.add(shapes.String(4,15,f'{course["Course"]}',fontName="Helvetica",fontSize=7,))
                label.add(shapes.String(4,5,f'Room: {course["Room"]}',fontName="Helvetica",fontSize=7,))

        if obj['P2']:
            label.add(shapes.String(4+spacing,25,f'P2',fontName="Helvetica-Bold",fontSize=10,))
            for i, course in enumerate(obj['P2']):
                label.add(shapes.String(4+spacing,15,f'{course["Course"]}',fontName="Helvetica",fontSize=7,))
                label.add(shapes.String(4+spacing,5,f'Room: {course["Room"]}',fontName="Helvetica",fontSize=7,))
    
        if obj['P3']:
            label.add(shapes.String(4+2*spacing,25,f'P3',fontName="Helvetica-Bold",fontSize=10,))
            for i, course in enumerate(obj['P3']):
                label.add(shapes.String(4+2*spacing,15,f'{course["Course"]}',fontName="Helvetica",fontSize=7,))
                label.add(shapes.String(4+2*spacing,5,f'Room: {course["Room"]}',fontName="Helvetica",fontSize=7,))
                    
        



def convert_days_to_cycle(days):
    days = str(days)
    conversion_list = [
        ("1", "M"),
        ("2", "T"),
        ("3", "W"),
        ("4", "Th"),
        ("5", "F"),
        ("5", "Sa"),
        ("-6", "-T-Th"),
    ]

    for cycle, day in conversion_list:
        days = days.replace(cycle, day)

    return days
