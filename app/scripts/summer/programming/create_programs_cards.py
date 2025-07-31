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


from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.flowables import BalancedColumns


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_RIGHT",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )
)
styles.add(
    ParagraphStyle(
        name="Body_Justify",
        parent=styles["BodyText"],
        alignment=TA_JUSTIFY,
    )
)
styles.add(
    ParagraphStyle(
        name="TITLE", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=150
    )
)



def main(lst_of_students=[]):
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

    timestamp = os.path.getctime(filename)
    cr_1_01_date = dt.date.fromtimestamp(timestamp)
    generated_string = f"Program generated: {cr_1_01_date}"
    flowables_dict["generated_string"] = generated_string

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
    group_by_cols = ["Sending school", "LastName", "FirstName", "StudentID"]

    student_classes_df = student_classes_df.drop_duplicates(
        subset=["StudentID", "Course"]
    )
    student_classes_df = student_classes_df[student_classes_df["Course"].str[0] != "Z"]
    student_classes_df = student_classes_df.fillna({"Room": 0})
    student_classes_df["Room"] = student_classes_df["Room"].apply(lambda x: int(x))

    if lst_of_students:
        student_classes_df = student_classes_df[
            student_classes_df["StudentID"].isin(lst_of_students)
        ]

    flowables_lst = []
    for (dbn, LastName, FirstName, StudentID), classes_df in student_classes_df.groupby(
        group_by_cols
    ):
        class_schedule_df = classes_df[classes_df["Period"].isin([1, 2, 3])]
        class_schedule_df = class_schedule_df[class_schedule_df["Course"].str[0] != "Z"]

        student_flowables_dict = {
            "StudentID": StudentID,
            "LastNameInitial": LastName[0],
            "LastName": LastName,
            "FirstName": FirstName,
            "DBN": dbn,
            "flowables": return_student_program_flowables(classes_df, flowables_dict),
            "taking_classes?": len(class_schedule_df) > 0,
        }
        flowables_lst.append(student_flowables_dict)

    flowables_df = pd.DataFrame(flowables_lst)

    
    # ## create alpha list
    # flowables_df = flowables_df[flowables_df["taking_classes?"]]
    # flowables_df = flowables_df.sort_values(by=["LastName", "FirstName"])

    # flowables = []
    # for last_name_initial, students_df in flowables_df.groupby("LastNameInitial"):
    #     folder_flowables = return_students_in_folder_flowables(students_df)
    #     flowables.extend(folder_flowables)

    #     temp_student_flowables = students_df["flowables"].explode().to_list()
    #     flowables.extend(temp_student_flowables)
    
    flowables = flowables_df["flowables"].explode().to_list()
    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=landscape(letter),
        topMargin=0.50 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    # list_of_files.append(f)

    # stream = BytesIO()
    # with ZipFile(stream, "w") as zf:
    #     for file in list_of_files:
    #         zf.write(file)
    # stream.seek(0)
    return f


def return_students_in_folder_flowables(students_df):
    flowables = []
    cols = ["StudentID", "LastName", "FirstName"]

    n = 25
    list_df = [students_df[i : i + n] for i in range(0, len(students_df), n)]

    lst_of_T = []
    for df in list_df:
        T = return_df_as_table(df, cols=cols)
        lst_of_T.append(T)

    B = BalancedColumns(
        lst_of_T,  # the flowables we are balancing
        nCols=2,  # the number of columns
        # needed=72,  # the minimum space needed by the flowable
    )
    flowables.append(B)
    flowables.append(PageBreak())
    return flowables


def return_student_program_flowables(classes_df, flowables_dict):

    flowables = []
    student_info = classes_df.to_dict("records")[0]
    photo_path = student_info["photo_filename"]

    StudentID = student_info["StudentID"]
    LastName = student_info["LastName"]
    FirstName = student_info["FirstName"]
    school_name = student_info["school_name"]
    school_year = flowables_dict["school_year"]

    paragraph = Paragraph(
        f"Summer School {school_year+1} Class Schedule",
        styles["Title"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{LastName}, {FirstName} ({StudentID})",
        styles["Heading1"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"{school_name}",
        styles["Heading2"],
    )
    flowables.append(paragraph)

    try:
        I = Image(photo_path)
        I.drawHeight = 2.75 * inch
        I.drawWidth = 2.75 * inch
        I.hAlign = "CENTER"

    except:
        I = ""
        pass

    class_schedule_df = classes_df[classes_df["Period"].isin([1, 2, 3])]
    class_schedule_df = class_schedule_df.sort_values(by=["Period"])
    cols = [
        "Course Name",
        # "Course",
        # "Section",
        "Teacher1",
        "Period",
        "Cycle",
        "Room",
        "Start",
        "End",
        "Latest Admit",
    ]
    class_schedule_T = return_df_as_table(class_schedule_df, cols=cols)
    # flowables.append(T)

    exams_df = classes_df[classes_df["Course"].str[1:3] == "XR"]

    exams_df = exams_df.sort_values(by=["Day", "Time"])
    cols = ["Course Name", "Date", "Time"]
    exams_T = return_df_as_table(exams_df, cols=cols)

    chart_style = TableStyle(
        [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    )

    class_table_paragraph = Paragraph(f"Class Schedule", styles["Heading4"])
    regents_exams_paragraph = Paragraph(f"Regents Exams Schedule", styles["Heading4"])

    lunch_string = "Lunch: 11:53AM - 12:23 PM"
    lunch_paragraph = Paragraph(lunch_string, styles["Heading5"])

    flowables.append(
        Table(
            [
                [
                    I,
                    [
                        class_table_paragraph,
                        class_schedule_T,
                        lunch_paragraph,
                        regents_exams_paragraph,
                        exams_T,
                    ],
                ]
            ],
            colWidths=[3 * inch, 6.75 * inch],
            rowHeights=[3 * inch],
            style=chart_style,
        )
    )

    first_period = class_schedule_df["Period"].min()
    paragraph = Paragraph(f"{first_period}", styles["TITLE"])
    flowables.append(paragraph)

    generated_string = flowables_dict["generated_string"]
    paragraph = Paragraph(generated_string, styles["Heading3"])
    flowables.append(paragraph)

    flowables.append(PageBreak())
    return flowables


def return_df_as_table(df, cols=None, colWidths=None, rowHeights=None):
    if cols:
        table_data = df[cols].values.tolist()
    else:
        cols = df.columns
        table_data = df.values.tolist()
    table_data.insert(0, cols)
    t = Table(table_data, colWidths=colWidths, repeatRows=1, rowHeights=rowHeights)
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (100, 100), "CENTER"),
                ("VALIGN", (0, 0), (100, 100), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), (0xD0D0FF, None)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    return t


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
