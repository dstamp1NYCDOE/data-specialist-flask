from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

def return_hub_location(section_row):
    Room = int(section_row["Room"])
    Time = section_row["Time"]
    exam_num = section_row["exam_num"]
    Section = section_row["Section"]

    if Room == 329:
        return 329
    if Room > 800:
        return {1: 919, 2: 823}.get(exam_num, 823)
    return {1: 727, 2: 519}.get(exam_num, 519)


def return_processed_registrations():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"

    filename = utils.return_most_recent_report(files_df, "1_08")
    cr_1_08_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df[cr_1_08_df["Status"] == True]
    cr_1_08_df = cr_1_08_df.fillna({"Room": 202})
    cr_1_08_df["Room"] = cr_1_08_df["Room"].astype(int)

    cr_1_08_df["ExamAdministration"] = f"{month} {school_year+1}"

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")
    section_properties_df = pd.read_excel(
        path, sheet_name="SummerSectionProperties"
    )

    cr_1_08_df = cr_1_08_df.merge(
        regents_calendar_df, left_on=["Course"], right_on=["CourseCode"], how="left"
    )
    cr_1_08_df = cr_1_08_df.merge(section_properties_df[['Section','Type']], on=["Section"], how="left")

    cr_1_08_df["Date"] = cr_1_08_df["Day"].dt.strftime("%A, %B %e")
    cr_1_08_df["Day"] = cr_1_08_df["Day"].dt.strftime("%m/%d")
    
    cr_1_08_df["Exam Title"] = cr_1_08_df["ExamTitle"].apply(return_full_exam_title)
    cr_1_08_df['hub_location'] = cr_1_08_df.apply(return_hub_location, axis=1)
    cr_1_08_df["Flag"] = "Student"

    ## attach home lang from 3.07
    filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_1_08_df = cr_1_08_df.merge(cr_3_07_df[['StudentID','HomeLangCode']], on=["StudentID"], how="left")

    home_lang_codes_df = utils.return_home_lang_code_table(files_df)
    cr_1_08_df = cr_1_08_df.merge(home_lang_codes_df[['HomeLang','HomeLangCode']], on=["HomeLangCode"], how="left")
    

    ## attach DBN
    filename = utils.return_most_recent_report_by_semester(
        files_df, "s_01", year_and_semester
    )
    cr_s_01_df = utils.return_file_as_df(filename)
    cr_s_01_df = cr_s_01_df[["StudentID", "Sending school"]]

    cr_1_08_df = cr_1_08_df.merge(cr_s_01_df, on=["StudentID"], how="left").fillna({"Sending school":'X'})

    ## attach photos
    cr_1_08_df = cr_1_08_df.merge(photos_df[['StudentID','photo_filename']], on=["StudentID"], how="left")

    cr_1_08_df = cr_1_08_df.drop_duplicates(subset=['StudentID','Course'])
    return cr_1_08_df

def return_exam_book():
    cr_1_08_df = return_processed_registrations()
    cols = ['Course','Section','Day','Date','Time','Exam Title','exam_num','ExamTitle','hub_location','Type','Room']
    exam_book_df = pd.pivot_table(
        cr_1_08_df,
        index=cols,
        values=['StudentID'],
        aggfunc='count'
    )
    exam_book_df.columns = ['NumOfStudents']
    exam_book_df = exam_book_df.reset_index()
    exam_book_df['accommodations_bubbles'] = exam_book_df['Type'].apply(return_accommodations_bubbles)
    return exam_book_df

def return_proctor_df():
    exam_book_df = return_exam_book()
 ## keep relevant columns
    cols = [
        "Day",
        "Time",
        "ExamTitle",
        "exam_num",
        "Course",
        "Section",
        "Type",
        "Room",
        "NumOfStudents",
        "hub_location",
    ]
    exam_book_df = exam_book_df[cols]
    TESTING_TIME_COL_NAME = "TestingTime (hours)"
    exam_book_df[TESTING_TIME_COL_NAME] = exam_book_df["Type"].apply(
        return_max_section_time
    )

    ## determine_proctor_needs
    PROCTOR_NUM = 0
    PROCTOR_LST = []
    for (day, room), sections_in_room_df in exam_book_df[
        exam_book_df["Section"] > 1
    ].groupby(["Day", "Room"]):
        section_type_lst = sections_in_room_df["Type"].to_list()
        time_lst = sections_in_room_df["Time"].unique().tolist()

        is_conflict_room = return_is_conflict_room(section_type_lst)

        is_am_room = return_if_am_room(time_lst)
        is_pm_room = return_if_pm_room(time_lst)
        is_am_pm_room = return_if_am_pm_room(time_lst)

        testing_sessions_df = sections_in_room_df.drop_duplicates(
            subset=["Time", "ExamTitle", TESTING_TIME_COL_NAME]
        )

        hours_in_room = testing_sessions_df[TESTING_TIME_COL_NAME].sum()

        if hours_in_room < 8:
            PROCTOR_NUM += 1
            proctor_type = "_".join(time_lst)
            proctor_dict = {
                "Day": day,
                "ProctorAssignment": PROCTOR_NUM,
                "Room": room,
                "proctor_type": proctor_type,
                "HoursOfAssignment": hours_in_room,
            }
            PROCTOR_LST.append(proctor_dict)
        else:
            for proctor_type in ["AM", "PM"]:
                PROCTOR_NUM += 1
                if hours_in_room < 6:
                    hours_in_room = 4.5
                else:
                    hours_in_room = 6

                proctor_dict = {
                    "Day": day,
                    "ProctorAssignment": PROCTOR_NUM,
                    "Room": room,
                    "proctor_type": proctor_type,
                    "HoursOfAssignment": hours_in_room,
                }
                PROCTOR_LST.append(proctor_dict)

    proctor_df = pd.DataFrame(PROCTOR_LST)


    proctor_df = exam_book_df.merge(
        proctor_df, on=["Day", "Room"], how="left"
    ).sort_values(by=["Day", "ExamTitle", "Room"])

    proctors_pvt_tbl = (
        pd.pivot_table(
            proctor_df,
            index=["Day", "Time", "Room", "ExamTitle", "hub_location"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        .reset_index()
        .sort_values(by=["Day", "Room", "Time"])
    )    

 ## generate hub pvt
    hub_pvt = pd.pivot_table(
        exam_book_df,
        index=["Day", "Time", "hub_location", "ExamTitle"],
        # columns=["ExamTitle"],
        values="NumOfStudents",
        aggfunc="sum",
    ).fillna(0)

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    proctors_pvt_tbl.to_excel(writer, sheet_name="ProctorNumbers")
    hub_pvt.to_excel(writer, sheet_name="HubNumbers")
    ##folders_to_prep_per_hub
    for hub_location, hub_sections_list in exam_book_df.groupby(["hub_location"]):
        sheet_name = f"Hub{hub_location[0]}"
        hub_rooms_pvt = pd.pivot_table(
            hub_sections_list,
            index=["Day", "Time", "Room", "ExamTitle"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        hub_rooms_pvt.to_excel(writer, sheet_name=sheet_name)

    ## day/time/hub sections_list
    for (day, time, hub_location), hub_sections_list in exam_book_df.groupby(
        ["Day", "Time", "hub_location"]
    ):
        sheet_name = f"{day}_{time}_Hub{hub_location}".replace("/", "-")
        hub_rooms_pvt = pd.pivot_table(
            hub_sections_list,
            index=["Room", "ExamTitle"],
            values=["NumOfStudents", "Type", "Section"],
            aggfunc={
                "Section": combine_lst_of_section_properties,
                "Type": combine_lst_of_section_properties,
                "NumOfStudents": "sum",
            },
        )
        hub_rooms_pvt.to_excel(writer, sheet_name=sheet_name)

    writer.close()
    f.seek(0)

    filename = f"Proctors_and_Exambook.xlsx"
    return f, filename

def return_max_section_time(section_type):
    default_time = 3
    if "enl" in section_type:
        default_time = 4.5
    if "2x" in section_type:
        default_time = 6
    if "1.5x" in section_type:
        default_time = 4.5
    return default_time    

def return_if_am_room(time_lst):
    if "AM" in time_lst:
        return True
    return False


def return_if_pm_room(time_lst):
    if "PM" in time_lst:
        return True
    return False


def return_if_am_pm_room(time_lst):
    return return_if_am_room(time_lst) and return_if_pm_room(time_lst)


def return_is_conflict_room(section_type_lst):
    for section_type in section_type_lst:
        if "conflict" in section_type:
            return True
    return False

def combine_lst_of_section_properties(x):
    x = x.unique()
    output = "\n".join(str(v) for v in x)
    return output

def return_accommodations_bubbles(section_type):
    bubbles = []
    if '1.5x' in section_type or '2x' in section_type:
        bubbles.append('1')
    if 'scribe' in section_type:
        bubbles.append('4')        
    if 'QR' in section_type:
        bubbles.append('10')
    if 'enl' in section_type:
        bubbles.append('12')
        bubbles.append('13')
        bubbles.append('14')

    return ', '.join(bubbles)

def return_full_exam_title(ExamTitle):

    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trig",
        "LE": "Liv Environ",
        "ES": "Earth Science",
        "Chem": "Chemistry",
        "Phys": "Physics",
        "Bio": "Biology",
        "ESS": "Earth & SS",
    }
    return exam_title_dict.get(ExamTitle)


PADDING = 0

import labels
label_specs = labels.Specification(
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

def return_blank_labels_needed_to_start_new_page(labels_to_make):
    remainder = len(labels_to_make) % 30
    temp_lst = []
    if remainder == 0:
        return temp_lst
    for i in range(30 - remainder):
        temp_lst.append({})
    return temp_lst


def return_blank_labels_needed_to_start_new_row(labels_to_make):
    remainder = len(labels_to_make) % 3
    temp_lst = []
    for i in range(3 - remainder):
        temp_lst.append({})
    return temp_lst


def draw_label(label, width, height, obj):

    if obj.get("Flag") == "Student":
        draw_student_label(label, width, height, obj)
    if obj.get("Flag") in ["Folder Label"]:
        draw_folder_label(label, width, height, obj)
    if obj.get("Flag") in ["Part 1", "Part 2"]:
        draw_section_label(label, width, height, obj)        
    if obj.get("Flag") in ["Section Label"]:
        draw_section_label(label, width, height, obj)
    if obj.get("Flag") in ["Scoring Certificate Label"]:
        draw_scoring_certificate_label(label, width, height, obj)        


from reportlab.graphics import shapes
from reportlab.lib import colors

 
def draw_section_label(label,width,height,obj):
    if obj:
        exam_title = obj.get("Exam Title")
        type = obj.get("Type")
        room = obj.get("Room")
        Day = obj.get("Day")
        Time = obj.get("Time")
        Part = obj.get("Flag")
        num_of_students = obj.get('NumOfStudents')

        label.add(shapes.String(4, 52, f"{exam_title}", fontName="Helvetica", fontSize=18))
        label.add(
            shapes.String(125, 38, f"{Day}-{Time}", fontName="Helvetica", fontSize=10)
        )

        label.add(shapes.String(125, 52, f"{Part}", fontName="Helvetica", fontSize=18))

        label.add(shapes.String(4, 4, f"{room}", fontName="Helvetica", fontSize=40))
        label.add(shapes.String(110, 10, f"{type}", fontName="Helvetica", fontSize=7))
        if num_of_students:
            label.add(shapes.String(125, 25, f"{num_of_students} Students", fontName="Helvetica", fontSize=7))



        label.add(
            shapes.String(
                4, 38, f"Section: {obj.get('Section')}", fontName="Helvetica", fontSize=11
            )
        )


def draw_part_1_labels(label, width, height, obj):
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["Exam Title"]} Regents - {obj["Flag"]}',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(
        shapes.String(
            4, 45, f'{obj["Day"]} - {obj["Time"]}', fontName="Helvetica", fontSize=10
        )
    )

    l = obj["Sections_lst"]
    n = 4
    section_lst_of_lst = [l[i : i + n] for i in range(0, len(l), n)]
    for j, section_lst in enumerate(section_lst_of_lst):
        for i, section_dict in enumerate(section_lst):
            section_num = section_dict["Section"]
            section_room = section_dict["Room"]
            label.add(
                shapes.String(
                    4 + 38 * j,
                    11 + 7 * i,
                    f"{section_room} ",
                    fontName="Helvetica",
                    fontSize=8,
                )
            )



def draw_folder_label(label, width, height, obj):
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["Exam Title"]}',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(
        shapes.String(
            4, 45, f'{obj["Day"]} - {obj["Time"]} | Hub: {obj["hub_location"]}', fontName="Helvetica", fontSize=10
        )
    )

    label.add(
        shapes.String(
            150, 45, f"{obj['NumOfStudents']} ", fontName="Helvetica", fontSize=22
        )
    )

    label.add(
        shapes.String(4, 11, f"{obj['Room']} ", fontName="Helvetica", fontSize=36)
    )

    for i, section_dict in enumerate(obj["Sections_lst"]):
        section_num = section_dict["Section"]
        section_type = section_dict["Type"]
        label.add(
            shapes.String(
                75,
                11 + 7 * i,
                f"/{section_num} - {section_type} ",
                fontName="Helvetica",
                fontSize=8,
            )
        )


def draw_student_label(label, width, height, obj):

    student_name = f"{obj['LastName'].upper()}, {obj['FirstName'].upper()}"

    course_section = f"{obj['Course']}/{obj['Section']}"

    label.add(shapes.Line(0, 70, 0, 54, strokeColor=colors.grey, strokeWidth=2))
    label.add(
        shapes.String(
            4,
            57,
            f'{obj["ExamAdministration"]} {obj["Exam Title"]} Regents',
            fontName="Helvetica",
            fontSize=10,
        )
    )
    label.add(shapes.Line(0, 53, 300, 53, strokeColor=colors.grey, strokeWidth=1))
    label.add(
        shapes.String(
            4, 42, f'School: {obj["Sending school"]}', fontName="Helvetica", fontSize=10
        )
    )
    label.add(shapes.Line(85, 54, 85, 44, strokeColor=colors.grey, strokeWidth=1))
    label.add(
        shapes.String(
            93, 42, f"Course: {course_section}", fontName="Helvetica", fontSize=10
        )
    )

    label.add(shapes.String(4, 25, student_name, fontSize=12))

    label.add(
        shapes.String(
            4, 11, f"ID: {obj['StudentID']}", fontName="Helvetica", fontSize=9
        )
    )

    label.add(
        shapes.String(
            130, 11, f"Room: {obj['Room']} ", fontName="Helvetica", fontSize=9
        )
    )


def draw_scoring_certificate_label(label, width, height, obj):

    label.add(
        shapes.String(
            4,
            50,
            f'{obj["Exam Title"]}',
            fontName="Helvetica",
            fontSize=17,
        )
    )

    label.add(
        shapes.String(
            4,
            30,
            f'{obj["Flag"]}',
            fontName="Helvetica",
            fontSize=13,
        )
    )

    label.add(
        shapes.String(
            4, 10, f'{obj["Day"]} - {obj["Time"]}', fontName="Helvetica", fontSize=13
        )
    )