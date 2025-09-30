from flask import session, current_app
import app.scripts.utils as utils
from app.scripts import scripts, files_df, photos_df

import pandas as pd
import os
from io import BytesIO


from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

from reportlab.platypus.flowables import BalancedColumns
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle
from reportlab.platypus import PageTemplate
from reportlab.platypus.frames import Frame

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Normal_small",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=7,
        leading=7,
    )
)
styles.add(
    ParagraphStyle(
        name="Normal_medium",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=9,
        leading=9,
    )
)



import app.scripts.summer.testing.regents_organization.utils as regents_organization_utils



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
    
    import app.scripts.summer.testing.proctor_directions.return_proctor_direction_flowables as return_proctor_direction_flowables
    
    proctor_directions_df = exam_book_df.drop_duplicates(subset=["Course", "Room"])
    proctor_directions_df["flowables"] = proctor_directions_df.apply(return_proctor_direction_flowables.main, args=(exam_book_df,), axis=1)
    

    if form.exam_title.data == "ALL":
        filename = f"{month}_{school_year+1}_folder_pages.pdf"
    else:
        exam_to_merge = form.exam_title.data
        filename = f"{month}_{school_year+1}_{exam_to_merge}_folder_pages.pdf"
        exam_book_df = exam_book_df[exam_book_df["ExamTitle"] == exam_to_merge]

    flowables = []
    for (course,day,time), sections_df in exam_book_df.groupby(["Course","Day","Time"]):
        exam_title = sections_df.iloc[0, :]["Exam Title"]
        ## materials by section
        for _, section in sections_df.iterrows():
            students_df = registrations_df[(registrations_df["Section"] == section["Section"]) & (registrations_df["Course"] == section["Course"])]

        ## materials by room
        for room, sections_by_room_df in sections_df.groupby("Room"):
            students_df = registrations_df[(registrations_df["Room"] == room) & (registrations_df["Course"] == course)]
            ## create proctor directions
            proctor_flowables = proctor_directions_df[(proctor_directions_df["Room"] == room) & (proctor_directions_df["Course"] == course)]['flowables']
            flowables.extend(proctor_flowables.iloc[0])
            ## create roster for the room
            flowables.extend(return_photo_roster(students_df))
            ## create ENL roster
            enl_students_df = students_df[students_df["Type"].str.contains('enl')]
            if len(enl_students_df) > 0:
                flowables.extend(return_enl_roster(enl_students_df))

            ##

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=0.25 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        bottomMargin=0.25 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)
    return f, filename


def return_photo_roster(students_df):
    flowables = []
    cols = ["StudentID", "LastName", "FirstName", "photo_filename", "Type"]
    cols_header = ["StudentID", "Last Name", "First Name", "Photo", "Type"]
    colwidths = [1 * inch, 1.5 * inch, 1.5 * inch, 0.75 * inch, 2.25 * inch]

    exam_title = students_df.iloc[0, :]["Exam Title"]
    course = students_df.iloc[0, :]["Course"]
    Room = students_df.iloc[0, :]["Room"]
    day = students_df.iloc[0, :]["Day"]
    time = students_df.iloc[0, :]["Time"]
    section = students_df.iloc[0, :]["Section"]


    paragraph = Paragraph(
        f"{exam_title} | {course} | Room {Room} | {day} - {time}",
        styles["Title"],
    )
    flowables.append(paragraph)
    header_info = {
        'exam_title':exam_title,
        'room':Room,
        'day':day,
        'time':time,
        'course':course,
    }
    B = return_balanced_grid_of_class_list(students_df,header_info)


    flowables.extend(B)
    flowables.append(PageBreak())
    return flowables

def return_enl_roster(students_df):
    exam_title = students_df.iloc[0, :]["Exam Title"]
    course = students_df.iloc[0, :]["Course"]
    Room = students_df.iloc[0, :]["Room"]
    day = students_df.iloc[0, :]["Day"]
    time = students_df.iloc[0, :]["Time"]

    flowables = []
    summary_pvt = pd.pivot_table(
                students_df,
                index="HomeLang",
                values="StudentID",
                aggfunc="count",
            ).reset_index()
    summary_pvt.columns = ["HomeLang", "#"]

    paragraph = Paragraph(
                f"{exam_title} - {Room} - ENL Info",
                styles["Title"],
            )
    flowables.append(paragraph)

    paragraph = Paragraph(
                f"Each student shall receive access to a language glossery and home language exam when applicable. These materials are in the room or provided in the testing bag. For exams other than ELA, they may write their responses in their home language. Answers should all appear in one book. Students receive a minimum of 1.5x time accommodation - Their IEP may indicate other testing accommodations.",
                styles["Normal"],
            )
 
    chart_style = TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )

    pvt_T = return_df_as_table(summary_pvt)
    roster_T_cols = ["StudentID", "LastName", "FirstName", "HomeLang", "Type"]
    roster_T = return_df_as_table(
                students_df, cols=roster_T_cols
            )
    flowables.append(
                Table(
                    [[paragraph, pvt_T]],
                    colWidths=[5 * inch, 2 * inch],
                    style=chart_style,
                
                )
            )
        
    flowables.append(roster_T)

    flowables.append(PageBreak())    
    return flowables



def return_balanced_grid_of_class_list(class_list_df,header_info):
    flowables = []
    
    # Process students in chunks to control page breaks
    chunk_size = 27  # Adjust based on your page layout
    total_students = len(class_list_df)
    
    for chunk_start in range(0, total_students, chunk_size):
        chunk_end = min(chunk_start + chunk_size, total_students)
        chunk_df = class_list_df.iloc[chunk_start:chunk_end]
        
        # Add continuation header for subsequent chunks
        if chunk_start > 0 and header_info:
            flowables.append(PageBreak())
            cont_header = Paragraph(
                f"{header_info['exam_title']} | {header_info['course']} | Room {header_info['room']} | {header_info['day']} - {header_info['time']} (continued)",
                styles["Heading2"]
            )
            flowables.append(cont_header)
            flowables.append(Spacer(1, 6))
        
        # Create student tables for this chunk
        chunk_flowables = []
        for index, student in chunk_df.iterrows():
            # Your existing student processing code
            photo_path = student["photo_filename"]
            section_Type = student["Type"]
            section = student["Section"]
            FirstName = student["FirstName"]
            LastName = student["LastName"]
            StudentID = student["StudentID"]
            sending_school = student['Sending school']

            try:
                I = Image(photo_path)
                I.drawHeight = 1 * inch
                I.drawWidth = 1 * inch
                I.hAlign = "CENTER"
            except:
                I = ""

            chart_style = TableStyle(
                [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
            )
            chunk_flowables.append(
                Table(
                    [
                        [
                            I,
                            [
                                Paragraph(f"{FirstName} {LastName}", styles["Normal_medium"]),
                                Paragraph(f"{StudentID}", styles["Normal_small"]),
                                Paragraph(f"{sending_school}", styles["Normal_small"]),
                                Paragraph(f"/{section}", styles["Normal_small"]),
                                Paragraph(str(section_Type), styles["Normal_small"]),
                            ],
                        ]
                    ],
                    colWidths=[1 * inch, 1 * inch],
                    rowHeights=[1 * inch],
                    style=chart_style,
                )
            )

        # Create balanced columns for this chunk
        B = BalancedColumns(chunk_flowables, nCols=3)
        flowables.append(B)
    
    # Return all flowables instead of just one BalancedColumns
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
                ("FONTSIZE", (0, 0), (-1, -1), 11),
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


class PhotoRosterBalancedColumns(BalancedColumns):
    def __init__(self, content, header_info, **kwargs):
        super().__init__(content, **kwargs)
        self.header_info = header_info
        self._page_count = 0
        
    def wrap(self, availWidth, availHeight):
        # Call parent wrap and track if we're likely to split
        w, h = super().wrap(availWidth, availHeight)
        if h > availHeight:
            self._page_count += 1
        return w, h
        
    def split(self, availWidth, availHeight):
        # When splitting occurs, mark subsequent parts as continuations
        splits = super().split(availWidth, availHeight)
        if splits and len(splits) > 1:
            # Create continuation headers for split parts
            from reportlab.platypus import Paragraph
            continuation_header = Paragraph(
                f"{self.header_info['exam_title']} | {self.header_info['course']} | Room {self.header_info['room']} (continued)",
                styles["Heading2"]
            )
            
            # Insert continuation header at the beginning of continuation splits
            for i in range(1, len(splits)):
                if hasattr(splits[i], '_content'):
                    splits[i]._content.insert(0, continuation_header)
                    
        return splits