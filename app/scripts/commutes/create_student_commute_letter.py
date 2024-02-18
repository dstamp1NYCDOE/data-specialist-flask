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


import datetime as dt

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
    Paragraph("Derek Stampone", styles["Normal_RIGHT"]),
    Paragraph("Assistant Principal, Attendance", styles["Normal_RIGHT"]),
]


def main(
    student_row,
):
    flowables = []

    StudentID = student_row["StudentID"]
    first_name = student_row["FirstName"]
    last_name = student_row["LastName"]
    address_str = student_row["address_str"]
    duration = student_row["duration"]
    starting_station = student_row["starting_station"]
    num_of_other_students = student_row["#_of_other_students"]
    steps = student_row["steps"]
    API_Response = student_row["API_Response"]
    student_steps = student_row["student_steps"]
    durationTime = student_row["durationTime"]

    today = dt.date.today()

    travel_time_with_cushion = durationTime * 1.15 + 10
    school_report_time = dt.time(hour=8, minute=10)

    time_to_leave = dt.datetime.combine(today, school_report_time) - dt.timedelta(
        minutes=travel_time_with_cushion
    )
    time_to_leave = time_to_leave.time().strftime("%-I:%M %p")

    wake_up_time = dt.datetime.combine(today, school_report_time) - dt.timedelta(
        minutes=travel_time_with_cushion + 45
    )
    wake_up_time = wake_up_time.time().strftime("%-I:%M %p")

    go_to_bed_time = dt.datetime.combine(today, school_report_time) - dt.timedelta(
        minutes=travel_time_with_cushion + 60 + 8 * 60
    )
    go_to_bed_time = go_to_bed_time.time().strftime("%-I:%M %p")

    flowables.extend(letter_head)
    paragraph = Paragraph(
        f"Dear {first_name.title()} {last_name.title()} ({StudentID})",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Students who get to school on time ever day are set up for success in high school and beyond! Hundreds of HSFI students are on time to school every day and so can you. Getting to school on time starts with a plan and taking into account possible MTA delays.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"According to the emergency contact card information your family submitted, you're commuting to HSFI from:",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"<b>{address_str}</b>",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"The fastest weekday commute according to Google Maps is <b>{duration}</b> door to door -- of course don't forget you should budget 5-10 minutes to get from the front door to your first class of the day.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"To get to school by <b>8:00 AM</b> so you could make it to Period 1 on time, you should:",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    times_lst = ListFlowable(
        [
            Paragraph(
                f"Leave home by <b>{time_to_leave}</b>; includes extra time for delays + 10 minutes to get upstairs.",
                styles["Normal"],
            ),
            Paragraph(
                f"Wake up at <b>{wake_up_time}</b>; gives you 45 minutes to get ready.",
                styles["Normal"],
            ),
            Paragraph(
                f"Go to bed by <b>{go_to_bed_time}</b>; students who get 8-10 hours of sleep do better in school.",
                styles["Normal"],
            ),
        ],
        bulletType="bullet",
        start="-",
    )
    flowables.append(times_lst)

    if num_of_other_students > 1:
        paragraph = Paragraph(
            f"Google recommends you start at <b>{starting_station}</b> and there are <b>{int(num_of_other_students-1)}</b> other HSFI students that use this station too! If you're interested in a travel buddy, connect with your counselor.",
            styles["BodyText"],
        )
    else:
        paragraph = Paragraph(
            f"Google recommends you start at <b>{starting_station}</b>",
            styles["BodyText"],
        )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"Directions:",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    directions_lst = [
        Paragraph(
            f"{direction}",
            styles["Normal"],
        )
        for direction in student_steps
    ]

    directions_lst = ListFlowable(
        directions_lst,
        bulletType="bullet",
        start="-",
    )
    flowables.append(directions_lst)

    paragraph = Paragraph(
        f"For many students, attending the High School of Fashion Industries means a signficant commute from home, but we know it's worth it! Thousands of students have made the trek to HSFI since 1926 to get an incredible education. The key to getting to school on time every day is to have a plan with clear steps and directions -- knowing exactly your commute, budgeting extra time for delays or errands, and setting alarms to remind you when to go to bed, when to wake up, and when to leave your home.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    paragraph = Paragraph(
        f"We're here to help; you can always visit your Wellness Center's Attendance Teacher to help you make a plan to get to school on time every day.",
        styles["BodyText"],
    )
    flowables.append(paragraph)

    flowables.extend(closing)
    flowables.append(PageBreak())
    return flowables
