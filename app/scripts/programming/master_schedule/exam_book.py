import pandas as pd
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

def main(administration_period):
    output_list = []

    if administration_period == 'January':
        course_code_suffix = 'R'
    if administration_period == 'June':
        course_code_suffix = 'E'

    exam_list = [
        'EXRC',
        'SXRK',
        'MXRK',
        'MXRF',
        'SXRP',
        'MXRN',
        'HXRC',
        'SXRX',
        'SXRU',
    ]

    for exam in exam_list:
        exam_code = exam + course_code_suffix
        for section in range(1,90):
            output_list.append(course_row(exam_code,section))

    return output_list

def course_row(exam_code,section):
    SchoolDBN = '02M600'
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    cycle_day = "'00000"

    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':exam_code,
    'SectionID':section,
    'Course Name':'',
    'PeriodID':f"{10}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(section),
    'Remaining Capacity':return_capacity(section),
    'Gender':'0',
    'Teacher Name':'EXAM',
    'Room':return_room_number(section),
    'Mapped Course':'',
    'Mapped Section':'',
    'Bell Schedule':'A',
    }
    return temp_dict

def return_capacity(section):
    if section < 20:
        return 34
    else:
        return 15

def return_room_number(section):
    return '202'


if __name__ == "__main__":
   print(main('January'))
