import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

from flask import session


def main(dept_name):
    df = utils.return_master_schedule_by_sheet(dept_name)

    output_list = []
    for index, teacher_row in df.iterrows():
        for period in range(1, 10):
            period_col = f"Period{period}"
            course_code = teacher_row[period_col]
            if course_code and course_code[0] != "_":
                if course_code not in ["GQS11", "GAS81", "RZS42"]:
                    output_list.extend(create_courses(teacher_row, period))

    return output_list


def create_courses(teacher_row, period):
    period_col = f"Period{period}"
    course_code = teacher_row[period_col]
    single_period_courses = [
        "AUS11",
        "ABS11",
        "ANS11",
        "AWS11",
        "AGS11",
        "AYS11",
        "AFS11QE",
        "AFS11QET",
        "APS21X",
        "BMS11QE",
        "AUS11QE",
        "BNS11QCA",
        "TQS11QE",
        "MKS21H",
        "MKS21X",
        "MKS21",
        "RZS41",
        "RZS42",
        "RZS43",
        "RZS44",
        "RQS43TY",
        "RQS41TY",
    ]
    mapped_course = ["ABS11"]
    if course_code in mapped_course:
        return create_mapped_course(teacher_row, period)
    elif course_code in single_period_courses:
        return [create_master_course(teacher_row, period)]
    else:
        return [
            create_master_course(teacher_row, period),
            create_cte_double_period(teacher_row, period),
        ]


def create_mapped_course(teacher_row, period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = "02M600"
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_course_code(course_code),
        "SectionID": f"{return_section_number(teacher_row,period)}",
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code),
        "Remaining Capacity": return_capacity(course_code),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": "",
        "Mapped Section": "",
        "Bell Schedule": "A",
    }
    mapped_dict = temp_dict.copy()
    mapped_dict["CourseCode"] = "ANS11"
    mapped_dict["SectionID"] = f"{return_section_number(teacher_row,period)+1}"
    mapped_dict["Mapped Course"] = return_course_code(course_code)
    mapped_dict["Mapped Section"] = f"{return_section_number(teacher_row,period)}"
    return [temp_dict, mapped_dict]


def create_master_course(teacher_row, period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = "02M600"
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_course_code(course_code),
        "SectionID": f"{return_section_number(teacher_row,period)}",
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code),
        "Remaining Capacity": return_capacity(course_code),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": "",
        "Mapped Section": "",
        "Bell Schedule": "A",
    }
    return temp_dict


def create_cte_double_period(teacher_row, period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = "02M600"
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_course_code(course_code),
        "SectionID": f"{return_section_number(teacher_row,period)}",
        "Course Name": "",
        "PeriodID": period + 1,
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code),
        "Remaining Capacity": return_capacity(course_code),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": "",
        "Mapped Section": "",
        "Bell Schedule": "A",
    }
    return temp_dict


def return_capacity(course_code):
    sequence_dict = {"RZS42": 25}
    default_seats = sequence_dict.get(course_code, 25)
    adjusted_seats = adjust_seat_capcity(course_code, default_seats)
    return adjusted_seats


def adjust_seat_capcity(course_code, default_seats):
    adjustment_dict = {
        "ACS11TD": -2,
        "ACS21T": -2,
        "AFS63TD": -4,

        "ANS11": +5,
        "ALS21T": +1,
        "TUS21TA": +1,
        "ABS11": +5,
        "ACS22T": +1,
        "AUS11QE": +4,
        "AFS65TC": +3,
        "AFS11QET": +3,
        "APS11T": +3,
        "BKS11TE": +4,
        "BRS11TF": +4,
        "BNS21TV": +0,
        "MKS21": +5 + 4,
    }
    return default_seats
    return default_seats + adjustment_dict.get(course_code, 0)


def return_course_code(course_code):
    return course_code


def return_teacher_name(teacher_row):
    first_name = str(teacher_row["first_name"])

    last_name = str(teacher_row["last_name"])
    if len(first_name) > 0:
        return (
            last_name.replace(" ", "").replace("-", "").upper()
            + " "
            + first_name[0].upper()
        )
    else:
        return last_name.replace(" ", "").replace("-", "").upper()


def return_section_number(teacher_row, period, cycle=None):
    TeacherID = teacher_row["TeacherID"]
    section = TeacherID * 10 + period
    course_code = teacher_row[f"Period{period}"]
    if course_code[0:4] == "RQS4":
        return 1

    if cycle:
        return (TeacherID + period) * 10 + {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}[
            cycle
        ]
    else:
        if section == 0:
            section = 1
        return section
