from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO

from reportlab.graphics import shapes
from reportlab.lib import colors

import labels

import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils


specs = regents_organization_utils.label_specs
return_blank_labels_needed_to_start_new_page = regents_organization_utils.return_blank_labels_needed_to_start_new_page
return_blank_labels_needed_to_start_new_row = regents_organization_utils.return_blank_labels_needed_to_start_new_row

def main(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        month = "January"
    if term == 2:
        month = "June"
    if term == 7:
        month = "August"


    exam_book_df = regents_organization_utils.return_exam_book()
    registrations_df = regents_organization_utils.return_processed_registrations()

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_exam_labels.pdf"
    else:
        exam_to_merge = form.exam_title.data
        
        filename = f"{month}_{school_year+1}_{exam_to_merge}_exam_labels.pdf"
        exam_book_df = exam_book_df[exam_book_df["ExamTitle"] == exam_to_merge]

    labels_to_make = []
    for (course,day,time), sections_df in exam_book_df.groupby(["Course","Day","Time"]):
        exam_title = sections_df.iloc[0, :]["Exam Title"]
        for room, sections_by_room_df in sections_df.groupby("Room"):
            students_df = registrations_df[(registrations_df["Room"] == room) & (registrations_df["Course"] == course)]
            course = students_df.iloc[0]["Course"]
            num_of_labels = 1
            if course[0] in ["M"]:
                labels_to_make.extend(students_df.to_dict("records"))
            elif course[0] in ["E"]:
                labels_to_make.extend(students_df.to_dict("records"))                
            elif course[0:4] in ["SXRK","SXR2","SXR3"]:
                labels_to_make.extend(students_df.to_dict("records"))
            else:
               num_of_labels = 2
               for student in students_df.to_dict("records"):
                    for i in range(num_of_labels):
                        labels_to_make.append(student)

            # add 6 blank labels that can be used as replacements or for walkins
            for i in range(num_of_labels * 6):
                temp_dict = {
                    "Flag": "Student",
                    "LastName": "_________________",
                    "FirstName": "_____________",
                    "Course": f"{course}",
                    "Section": "____",
                    "ExamAdministration": f"{month} {school_year+1}",
                    "Exam Title": exam_title,
                    "Sending school": "________",
                    "StudentID": "________________",
                    "Room": f"{room}",
                }
                labels_to_make.append(temp_dict)

            if len(labels_to_make) % 30 == 0:
                num_of_blank_rows = 0
            elif len(labels_to_make) % 3 == 0:
                num_of_blank_rows = 1
            else:
                if len(labels_to_make) % 30 > 27:
                    num_of_blank_rows = 1
                else:
                    num_of_blank_rows = 2
            
            for _ in range(num_of_blank_rows):
                labels_to_make.extend(
                    return_blank_labels_needed_to_start_new_row(labels_to_make)
                )
        labels_to_make.extend(
            return_blank_labels_needed_to_start_new_page(labels_to_make)
        )  
        # attend a full sheet of "blank" labels that can be used as replacements or walkins
        for i in range(1 * 30):
            temp_dict = {
                "Flag": "Student",
                "LastName": "_________________",
                "FirstName": "_____________",
                "Course": f"{course}",
                "Section": "____",
                "ExamAdministration": f"{month} {school_year+1}",
                "Exam Title": exam_title,
                "Sending school": "________",
                "StudentID": "________________",
                "Room": "_____",
            }
            labels_to_make.append(temp_dict)            
        labels_to_make.extend(
            return_blank_labels_needed_to_start_new_page(labels_to_make)
        )        

    f = BytesIO()
    sheet = labels.Sheet(specs, regents_organization_utils.draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    
    return f, filename
