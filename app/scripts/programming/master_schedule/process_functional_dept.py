import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

def main():
    functional_course_list = [
    ('ZA',1),
    ('ZA',2),
    ('ZA',3),
    ('ZA',4),
    ('ZA',5),
    ('ZA',6),
    ('ZA',7),
    ('ZA',8),
    ('ZA',9),

    ('ZL',4),
    ('ZL',5),
    ('ZL',6),
    ('ZL',7),
    ('ZL8',8),

    ('ZL9',4),
    ('ZL9',5),
    ('ZL9',6),
    ('ZL9',7),

    ('ZLYL',4),
    ('ZLYL',5),
    ('ZLYL',6),
    ('ZLYL',7),

    ('ZM18',9),
    ('ZM29',1),
    ]

    output_list = []
    for course_code, period in functional_course_list:
        if course_code in ['ZLYL']:
            for cycle_day in ["'01010","'00101"]:
                output_list.append(create_course(course_code,period,cycle_day))
        elif course_code in ['ZL9']:
            output_list.append(create_course(course_code,period,"'10000"))
        else:
            output_list.append(create_course(course_code,period))


    return output_list

def create_course(course_code,period, cycle_day = "'11111"):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID


    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':course_code,
    'SectionID':return_section_number(course_code, period,cycle_day),
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(course_code, period),
    'Remaining Capacity':return_capacity(course_code, period),
    'Gender':'0',
    'Teacher Name':'STAFF',
    'Room':return_room(course_code),
    'Mapped Course':return_mapped_course(course_code, period),
    'Mapped Section':return_mapped_section(course_code, period),
    'Bell Schedule':'A',
    }
    return temp_dict

def return_mapped_course(course_code, period):
    if course_code == 'ZM1':
        if period == 1:
            return 'ZM29'
        if period == 9:
            return 'ZM18'
    return ''

def return_mapped_section(course_code, period):
    if course_code == 'ZM1':
        return f"{period}"
    return ''

def return_section_number(course_code, period,cycle=None):
    if course_code == 'ZA':
        return 1
    if cycle == "'01010":
        return 10+period
    elif cycle == "'00101":
        return 20+period
    else:
        return period

def return_capacity(course_code, period):
    if course_code == 'ZL':
        return 425
    if course_code == 'ZL8':
        return 50
    if course_code == 'ZLYL':
        ZLYL_dict = {
        4:13*4,
        5:13*2,
        6:13*2,
        7:13*2,
        }
        return ZLYL_dict.get(period)
    if course_code == 'ZA':
        return 999
    if course_code == 'ZM1':
        return 800
    if course_code == 'ZM18':
        return 500
    if course_code == 'ZM29':
        return 1200
    else:
        return 0

def return_room(course_code):
    if course_code[0:2] == 'ZL':
        return 'CAFE'
    if course_code == 'ZA':
        return '125'
    if course_code == 'ZM1':
        return ''
    if course_code == 'ZM18':
        return ''
    if course_code == 'ZM29':
        return ''


def return_hard_coded():
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_list = [
    {'CourseCode': 'GQS11',
        'SectionID': '1',
        'PeriodID': '0',
        'Cycle Day': "'10000",
        'Capacity': 50,
        'Remaining Capacity': 50,
        'Teacher Name': 'ARCAMAY J',
        'Room': '829', },

    {'CourseCode':'ZJS11QA',
    'SectionID':'1',
    'PeriodID':'0',
    'Cycle Day':"'11111",
    'Capacity':0,
    'Remaining Capacity':0,
    'Teacher Name':'MCGUINNESS B',
    'Room':'329',},

    {'CourseCode':'ZJS11QA',
    'SectionID':'2',
    'PeriodID':'0',
    'Cycle Day':"'11111",
    'Capacity':0,
    'Remaining Capacity':0,
    'Teacher Name':'MCGUINNESS B',
    'Room':'329',},

    {'CourseCode':'ZJS11QB',
    'SectionID':'1',
    'PeriodID':'1',
    'Cycle Day':"'11111",
    'Capacity':8,
    'Remaining Capacity':8,
    'Teacher Name':'GURUNG S',
    'Room':'323',},

    {'CourseCode':'ZJS11QB',
    'SectionID':'2',
    'PeriodID':'1',
    'Cycle Day':"'11111",
    'Capacity':8,
    'Remaining Capacity':8,
    'Teacher Name':'SMITHBROWN S',
    'Room':'323',},


        {'CourseCode': 'RQS41TY',
         'SectionID': '1',
         'PeriodID': '9',
         'Cycle Day': "'11111",
         'Capacity': 8,
         'Remaining Capacity': 8,
         'Teacher Name': 'NIEVES M',
         'Room': '845', },
        {'CourseCode': 'RQS41TY',
         'SectionID': '1',
         'PeriodID': '8',
         'Cycle Day': "'11111",
         'Capacity': 8,
         'Remaining Capacity': 8,
         'Teacher Name': 'NIEVES M',
         'Room': '845', },
        {'CourseCode': 'RQS41TY',
         'SectionID': '1',
         'PeriodID': '7',
         'Cycle Day': "'11111",
         'Capacity': 8,
         'Remaining Capacity': 8,
         'Teacher Name': 'NIEVES M',
         'Room': '845', },



    ]
    output_list = []
    for course in course_list:
        temp = course.copy()
        temp['SchoolDBN'] = SchoolDBN
        temp['SchoolYear'] = SchoolYear
        temp['TermID'] = TermID
        temp['Mapped Course'] = ''
        temp['Mapped Section'] = ''
        temp['Gender'] = '0'
        temp['Course Name']  = ''
        temp['Bell Schedule'] = 'A'

        output_list.append(temp)

    return output_list
