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

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_folder_labels.pdf"
    else:
        exam_to_merge = form.exam_title.data
        print(exam_to_merge)
        filename = f"{month}_{school_year+1}_{exam_to_merge}_folder_labels.pdf"
        exam_book_df = exam_book_df[exam_book_df["ExamTitle"] == exam_to_merge]

    labels_to_make = []
    for (course,day,time), sections_df in exam_book_df.groupby(["Course","Day","Time"]):
        exam_title = sections_df.iloc[0, :]["Exam Title"]

        ## scoring certificate label
        temp_dict = {
            "Flag": "Scoring Certificate Label",
            "Exam Title": exam_title,
            "Day":day,
            "Time":time,
        }
        labels_to_make.append(temp_dict)
        labels_to_make.append(temp_dict) 
        labels_to_make.append(temp_dict)   

        ## section 99 labels
        for part in ["Part 1", "Part 2"]:
            section_99_dict = {
                "Flag": part,
                "Section": "99",
                "Exam Title": exam_title,
                "Room": "Walkins",
                "Day": day,
                "Time": time,
                "Type": "",
            }
            labels_to_make.append(section_99_dict)
        
        ## section labels
        for part in ["Part 1", "Part 2"]:
            sections_df["Flag"] = part
            labels_to_make.extend(sections_df.to_dict("records"))
            # labels_to_make.extend(return_blank_labels_needed_to_start_new_row(labels_to_make))

        ## room folder labels
        for room, room_df in sections_df.groupby("Room"):
            for label_type in ["Folder Label"]:
                section_lst = room_df.sort_values(by="Section").to_dict("records")
                hub_location = room_df.iloc[0, :]["hub_location"]
                bag_label = {
                        "Day": day,
                        "Time": time,
                        "Exam Title": exam_title,
                        "Room": room,
                        "hub_location":hub_location,
                        "Flag": label_type,
                        "NumOfStudents": room_df["NumOfStudents"].sum(),
                        "ExamAdministration": f"{month} {school_year+1}",
                        "Sections_lst": section_lst,
                    }
                if len(section_lst) <= 4:
                    labels_to_make.append(bag_label)
                else:
                    bag_label["Sections_lst"] = section_lst[:4]
                    labels_to_make.append(bag_label) 
                    bag_label = bag_label.copy()   
                    bag_label["Sections_lst"] = section_lst[4:]
                    bag_label["NumOfStudents"] = ""
                    labels_to_make.append(bag_label)

        # labels_to_make.extend(
        #     return_blank_labels_needed_to_start_new_row(labels_to_make)
        # )

    f = BytesIO()
    sheet = labels.Sheet(specs, regents_organization_utils.draw_label, border=True)
    sheet.add_labels(labels_to_make)
    sheet.save(f)

    f.seek(0)
    
    return f, filename
