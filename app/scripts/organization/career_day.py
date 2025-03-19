import pandas as pd
import app.scripts.utils as utils
from app.scripts import scripts, files_df

from io import BytesIO
import urllib.parse


def process_spreadsheet(form, request):
    locations = request.files[form.locations_file.name]
    locations_df = pd.read_csv(locations)

    cols = ["Presenter", "Room", "Final Session Title"]
    locations_df = locations_df[cols]

    survey_responses = request.files[form.survey_responses.name]
    surveys_dict = pd.read_excel(survey_responses, sheet_name=None)


    surveys_df = pd.concat(surveys_dict.values())

    canceled_presentations = ['Ashley Masse: Fashion & Lifestyle Blogger']

    surveys_df = surveys_df[~surveys_df['Which Career Day presenter are you signing up for?'].isin(canceled_presentations)]

    filename = utils.return_most_recent_report(files_df, "3_07")
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]

    students_with_invalid_student_ids = surveys_df[
        ~surveys_df["StudentID"].isin(student_info_df["StudentID"])
    ]["StudentID"].unique()
    

    surveys_df = surveys_df.drop_duplicates(
        subset=["StudentID", "Which Career Day presenter are you signing up for?"]
    )

    session_rosters = {}

    sessions = surveys_df["Which Career Day presenter are you signing up for?"].unique()
    for session in sessions:
        if session not in [
            "Session 1: Student working Career Day Event",
            "Session 2: Student working Career Day Event",
        ]:
            session_rosters[session] = {"Session1": [], "Session2": []}

    session_one_only = [
        "Jordie McFarquhar : Fashion Designer",
        "Musa Jackson: Model, Writer, and Producer",
    ]
    
    for session in session_one_only:
        session_rosters[session]["Session2"] = [x for x in range(999)]

    session_two_only = ["Ty-Ron Mayes: Celebrity Stylist"]
    session_two_only = []
    for session in session_two_only:
        session_rosters[session]["Session1"] = [x for x in range(999)]

    surveys_df["Session1_only?"] = surveys_df[
        "Which Career Day presenter are you signing up for?"
    ].apply(lambda x: x in session_one_only)
    surveys_df["Session2_only?"] = surveys_df[
        "Which Career Day presenter are you signing up for?"
    ].apply(lambda x: x in session_two_only)

    surveys_df = surveys_df.sort_values(
        by=["Session1_only?", "Session2_only?"], ascending=[False, True]
    )

    student_lst = []
    for StudentID, sessions_df in surveys_df.groupby("StudentID"):
        student_sessions = sessions_df[
            "Which Career Day presenter are you signing up for?"
        ].to_list()

        if "Session 1: Student working Career Day Event" in student_sessions:
            SESSION1 = "Session 1: Student working Career Day Event"
            student_sessions.remove(SESSION1)

        if "Session 2: Student working Career Day Event" in student_sessions:
            SESSION2 = "Session 2: Student working Career Day Event"
            student_sessions.remove(SESSION2)

        if len(student_sessions) >= 2:
            CHOICE_A = student_sessions[0]
            CHOICE_B = student_sessions[1]

            if CHOICE_A == CHOICE_B:
                try:
                    CHOICE_B = student_sessions[2]
                except:
                    CHOICE_B = sorted(
                        session_rosters, key=lambda k: len(session_rosters[k]["Session2"])
                    )[0]

            CHOICE_A_SESSION1_NUM = len(session_rosters[CHOICE_A]["Session1"])
            CHOICE_A_SESSION2_NUM = len(session_rosters[CHOICE_A]["Session2"])

            if CHOICE_A_SESSION1_NUM <= CHOICE_A_SESSION2_NUM:
                SESSION1 = CHOICE_A
                SESSION2 = CHOICE_B
            else:
                SESSION1 = CHOICE_B
                SESSION2 = CHOICE_A

            if SESSION1 in session_two_only:
                SESSION1, SESSION2 = SESSION2, SESSION1
            session_rosters[SESSION1]["Session1"].append(StudentID)
            session_rosters[SESSION2]["Session2"].append(StudentID)

        if len(student_sessions) == 1:

            CHOICE_A = student_sessions[0]

            CHOICE_A_SESSION1_NUM = len(session_rosters[CHOICE_A]["Session1"])
            CHOICE_A_SESSION2_NUM = len(session_rosters[CHOICE_A]["Session2"])

            if CHOICE_A_SESSION1_NUM <= CHOICE_A_SESSION2_NUM:
                SESSION1 = CHOICE_A
                session_rosters[CHOICE_A]["Session1"].append(StudentID)

                SESSION2 = sorted(
                    session_rosters, key=lambda k: len(session_rosters[k]["Session2"])
                )[0]
                session_rosters[SESSION2]["Session2"].append(StudentID)
            else:
                SESSION2 = CHOICE_A
                session_rosters[CHOICE_A]["Session2"].append(StudentID)

                SESSION1 = sorted(
                    session_rosters, key=lambda k: len(session_rosters[k]["Session1"])
                )[0]
                session_rosters[SESSION1]["Session1"].append(StudentID)

        temp_dict = {
            "StudentID": StudentID,
            "Session": "Session1",
            "Presenter": SESSION1,
        }
        student_lst.append(temp_dict)
        temp_dict = {
            "StudentID": StudentID,
            "Session": "Session2",
            "Presenter": SESSION2,
        }
        student_lst.append(temp_dict)

    assignments_df = pd.DataFrame(student_lst)

    students_df = student_info_df.merge(
        assignments_df, on="StudentID", how="outer"
    ).fillna({"Session": "NoSurvey", "LastName": ""})

    students_with_no_survey = students_df[students_df["Session"] == "NoSurvey"][
        "StudentID"
    ].unique()

    for StudentID in students_with_no_survey:
        SESSION1 = sorted(
            session_rosters, key=lambda k: len(session_rosters[k]["Session1"])
        )[0]
        SESSION2 = sorted(
            session_rosters, key=lambda k: len(session_rosters[k]["Session2"])
        )[0]

        if SESSION1 == SESSION2:
            if StudentID % 2 == 0:
                SESSION2 = sorted(
                    session_rosters, key=lambda k: len(session_rosters[k]["Session2"])
                )[1]
            else:
                SESSION1 = sorted(
                    session_rosters, key=lambda k: len(session_rosters[k]["Session1"])
                )[1]                            

        session_rosters[SESSION1]["Session1"].append(StudentID)
        session_rosters[SESSION2]["Session2"].append(StudentID)

        temp_dict = {
            "StudentID": StudentID,
            "Session": "Session1",
            "Presenter": SESSION1,
        }
        student_lst.append(temp_dict)
        temp_dict = {
            "StudentID": StudentID,
            "Session": "Session2",
            "Presenter": SESSION2,
        }
        student_lst.append(temp_dict)

    assignments_df = pd.DataFrame(student_lst)
    students_df = student_info_df.merge(
        assignments_df, on="StudentID", how="left"
    ).fillna({"Session": "NoSurvey"})

    counts_df = pd.pivot_table(
        assignments_df,
        index="Presenter",
        columns="Session",
        values="StudentID",
        aggfunc="count",
    )
    

    assignments_df = assignments_df.merge(
        locations_df[['Room','Final Session Title']], left_on=["Presenter"], right_on=['Final Session Title'], how="left"
    ).fillna({"Room": 829, "Final Session Title": "Working Career Day"})

    assignments_df["Room"] = assignments_df["Room"].astype(int)

    return assignments_df


def return_assignments_as_spreadsheet(assignments_df):
    f = BytesIO()
    writer = pd.ExcelWriter(f)

    assignments_df = assignments_df.pivot(
        index="StudentID", columns="Session", values=["Final Session Title", "Room"]
    ).reset_index()
    assignments_df.columns = [
        "StudentID",
        "Session1",
        "Session2",
        "Session1Location",
        "Session2Location",
    ]

    filename = utils.return_most_recent_report(files_df, "3_07")
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]

    assignments_df = assignments_df.merge(
        student_info_df, on=["StudentID"], how="left"
    ).fillna("")

    assignments_df.to_excel(writer)

    writer.close()
    f.seek(0)

    return f


from reportlab.graphics import shapes
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    Paragraph,
    PageBreak,
    Spacer,
    Image,
    Table,
    TableStyle,
    ListFlowable,
)
from reportlab.platypus import SimpleDocTemplate
from reportlab_qrcode import QRCodeImage

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

letter_head = [
    Paragraph("High School of Fashion Industries", styles["Normal"]),
    Paragraph("225 W 24th St", styles["Normal"]),
    Paragraph("New York, NY 10011", styles["Normal"]),
    Paragraph("Principal, Daryl Blank", styles["Normal"]),
]

closing = [
    Spacer(width=0, height=0.25 * inch),
    Paragraph("Warmly,", styles["Normal_RIGHT"]),
    Paragraph("Kate Boulamaali", styles["Normal_RIGHT"]),
    Paragraph("Assistant Principal, CTE", styles["Normal_RIGHT"]),
]

feedback_url = f"https://docs.google.com/forms/d/e/1FAIpQLSfYEug9GL8X_8BRAP5rMMVvPrzrXMDeDeJmBTgwuy1SGSV1sw/viewform"
qr_flowable = QRCodeImage(feedback_url, size=2.2 * inch)


def return_student_flowables(student_row):
    
    StudentID = student_row["StudentID"]
    FirstName = student_row["FirstName"]
    LastName = student_row["LastName"]
    Session1_feedback_url = student_row["Session1_feedback_url"]
    Session2_feedback_url = student_row["Session2_feedback_url"]

    flowables = []

    flowables.extend(letter_head)
    paragraph = Paragraph(
        f"Dear {FirstName.title()} {LastName.title()} ({StudentID})",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    Session1 = student_row["Session1"]
    Session1Location = student_row["Session1Location"]
    Session2 = student_row["Session2"]
    Session2Location = student_row["Session2Location"]

    paragraph = Paragraph(
        f"You have been assigned to the following sessions for Career Day 2024. Please be on time! Show this letter at the door as your admission ticket",
    )

    flowables.append(paragraph)

    flowables.append(Spacer(width=0, height=0.25 * inch))
    paragraph = Paragraph(f"Session #1 (9:50am - 10:40am): {Session1}")
    flowables.append(paragraph)
    paragraph = Paragraph(f"Room: {Session1Location}")
    flowables.append(paragraph)
    # paragraph = Paragraph(
    #     f"At the end of the session, scan the QR code below to provide feedback on the session and reflect on what you learned. Your responses will be shared with your CTE teacher."
    # )
    # flowables.append(paragraph)

    # qr_flowable = QRCodeImage(Session1_feedback_url, size=2.2 * inch)
    # flowables.append(qr_flowable)

    flowables.append(Spacer(width=0, height=0.25 * inch))
    paragraph = Paragraph(f"Session #2 (10:45am - 11:30am): {Session2}")
    flowables.append(paragraph)
    paragraph = Paragraph(f"Room: {Session2Location}")
    flowables.append(paragraph)
    # paragraph = Paragraph(
    #     f"At the end of the session, scan the QR code below to provide feedback on the session and reflect on what you learned. Your responses will be shared with your CTE teacher."
    # )
    # flowables.append(paragraph)
    # qr_flowable = QRCodeImage(Session2_feedback_url, size=2.2 * inch)
    # flowables.append(qr_flowable)

    flowables.extend(closing)
    flowables.append(PageBreak())
    return flowables


def return_student_letters(assignments_df):

    assignments_df = assignments_df.pivot(
        index="StudentID", columns="Session", values=["Final Session Title", "Room"]
    ).reset_index()
    assignments_df.columns = [
        "StudentID",
        "Session1",
        "Session2",
        "Session1Location",
        "Session2Location",
    ]

    filename = utils.return_most_recent_report(files_df, "3_07")
    student_info_df = utils.return_file_as_df(filename)
    student_info_df = student_info_df[
        ["StudentID", "LastName", "FirstName", "Student DOE Email"]
    ]

    assignments_df = assignments_df.merge(
        student_info_df, on=["StudentID"], how="left"
    ).fillna("")

    for session_num in ["Session1", "Session2"]:
        assignments_df[f"{session_num}_feedback_url"] = assignments_df.apply(
            return_feedback_form_url, axis=1, args=(session_num,)
        )

    assignments_df = assignments_df.sort_values(by=["LastName", "FirstName"])
    assignments_df["flowables"] = assignments_df.apply(return_student_flowables, axis=1)
    flowables = assignments_df["flowables"].explode().to_list()

    f = BytesIO()
    my_doc = SimpleDocTemplate(
        f,
        pagesize=letter,
        topMargin=1 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        bottomMargin=1 * inch,
    )
    my_doc.build(flowables)

    f.seek(0)

    return f


def return_feedback_form_url(student_row, session_number):
    StudentID = student_row["StudentID"]
    FirstName = urllib.parse.quote_plus(student_row["FirstName"])
    LastName = urllib.parse.quote_plus(student_row["LastName"])

    session_title = urllib.parse.quote_plus(student_row[session_number])

    url = f"https://docs.google.com/forms/d/e/1FAIpQLScK0h8W89yB4CYqo8itBpu3qsxdVYRAOTIlCgnrR4vw-qviXQ/viewform?usp=pp_url&entry.2082149014={StudentID}&entry.1924172135={FirstName}&entry.1958685972={LastName}&entry.80708674={session_title}&entry.934957950={session_number}"
    return url
