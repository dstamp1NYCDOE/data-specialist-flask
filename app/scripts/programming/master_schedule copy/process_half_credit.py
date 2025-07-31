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
                output_list.extend(create_courses(teacher_row, period))

    return output_list


def create_courses(teacher_row, period):
    period_col = f"Period{period}"
    course_code = teacher_row[period_col]
    course_code = course_code.replace("+", "")

    output = []
    if course_code in ["RZS42"]:
        for day, cycle_day in [("A", "'01010"), ("B", "'00101")]:
            # output.append(create_mapped_course(teacher_row, period, day, cycle_day))
            output.append(create_master_course(teacher_row, period, day, cycle_day))
    if course_code in ["GQS22", "GQS21"]:
        for day, cycle_day in [("A", "'01010"), ("B", "'00101")]:
            output.append(create_mapped_course(teacher_row, period, day, cycle_day))
            output.append(create_master_course(teacher_row, period, day, cycle_day))
    if course_code in ["GAS85", "GAS87"]:
        for day, cycle_day in [
            ("A", "'01000"),
            ("B", "'00100"),
            ("C", "'00010"),
            ("D", "'00001"),
        ]:
            output.append(create_mapped_course(teacher_row, period, day, cycle_day))
            output.append(create_master_course(teacher_row, period, day, cycle_day))
    if course_code in ["GAS81", "GAS82"]:
        for day, cycle_day in [("A", "'01010"), ("B", "'00101")]:
            output.append(create_mapped_course(teacher_row, period, day, cycle_day))
            output.append(create_master_course(teacher_row, period, day, cycle_day))
        for day, cycle_day in [("A", "'01010"), ("B", "'00101")]:
            offset = teacher_row[f"Period{period}"].count("+")
            if offset > 0:
                offset_string = "+" * offset
            else:
                offset_string = ""
            teacher_row[f"Period{period}"] = "GLS11" + offset_string
            output.append(create_mapped_course(teacher_row, period, day, cycle_day))
            output.append(create_master_course(teacher_row, period, day, cycle_day))

            output.append(create_mapped_yl_training(teacher_row, period, day, "'10000"))
            output.append(
                return_mapped_lunch_for_yl(teacher_row, period, day, cycle_day)
            )
            teacher_row[f"Period{period}"] = "GLS11QYL" + offset_string
            output.append(create_master_course(teacher_row, period, day, "'10000"))

    return output


def return_mapped_lunch_for_yl(teacher_row, period, day, cycle_day):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = "02M600"
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")
    course_code = course_code.replace("+", "")

    if cycle_day == "'01010":
        cycle_day = "'00101"
        mapped_section = 20 + period
    elif cycle_day == "'00101":
        cycle_day = "'01010"
        mapped_section = 10 + period

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_mapped_course_code(course_code, day),
        "SectionID": return_section_number(teacher_row, period, day),
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code, period),
        "Remaining Capacity": return_capacity(course_code, period),
        "Gender": "0",
        "Teacher Name": "STAFF",
        "Room": "CAFE",
        "Mapped Course": "ZLYL",
        "Mapped Section": f"{mapped_section}",
        "Bell Schedule": "A",
    }
    return temp_dict


def create_mapped_yl_training(teacher_row, period, day, cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")
    course_code = course_code.replace("+", "")

    cycle_day = "'10000"

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_mapped_course_code(course_code, day),
        "SectionID": return_section_number(teacher_row, period, day),
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code, period),
        "Remaining Capacity": return_capacity(course_code, period),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": return_course_code("GLS11QYL", day),
        "Mapped Section": return_section_number(teacher_row, period, day),
        "Bell Schedule": "A",
    }
    return temp_dict


def create_mapped_course(teacher_row, period, day, cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")
    course_code = course_code.replace("+", "")

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_mapped_course_code(course_code, day),
        "SectionID": return_section_number(teacher_row, period, day),
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code, period),
        "Remaining Capacity": return_capacity(course_code, period),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": return_course_code(course_code, day),
        "Mapped Section": return_section_number(teacher_row, period, day),
        "Bell Schedule": "A",
    }
    return temp_dict


def create_master_course(teacher_row, period, day, cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID
    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")
    course_code = course_code.replace("+", "")

    temp_dict = {
        "SchoolDBN": SchoolDBN,
        "SchoolYear": SchoolYear,
        "TermID": TermID,
        "CourseCode": return_course_code(course_code, day),
        "SectionID": return_section_number(teacher_row, period, day),
        "Course Name": "",
        "PeriodID": f"{period}",
        "Cycle Day": cycle_day,
        "Capacity": return_capacity(course_code, period),
        "Remaining Capacity": return_capacity(course_code, period),
        "Gender": "0",
        "Teacher Name": return_teacher_name(teacher_row),
        "Room": "",
        "Mapped Course": "",
        "Mapped Section": "",
        "Bell Schedule": "A",
    }
    return temp_dict


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
    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")

    TeacherID = teacher_row["TeacherID"]
    section = TeacherID * 10 + period
    return (
        (TeacherID + offset) * 10
        + {"A": 1, "B": 3, "C": 5, "D": 7, "E": 9}.get(cycle, 0)
        - period
    )


def return_capacity(course_code, period):
    yl_per_section = 5
    if course_code in ["GLS11"]:
        return yl_per_section
    if course_code in ["GLS11QYL"]:
        return 2 * yl_per_section
    if course_code in ["ZLYL"]:
        return 2 * 2 * yl_per_section
    if course_code in ["GQS21", "GQS22"]:
        if period in [1,8]:
            return 25
        return 34
    if course_code in ["GAS85", "GAS87"]:
        return 34
    if course_code[0] == "R":
        return 25
    if course_code in ["GAS81", "GAS82"]:
        return 25 + 9
    else:
        return round(2 * 34 / 3)


def return_course_code(course_code, day):
    if course_code in ["GLS11QYL", "RZS42"]:
        return course_code
    if day:
        return course_code + "Q" + day
    else:
        return course_code


def return_mapped_course_code(course_code, day):
    return course_code
