import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

from flask import current_app, session

def main(dept_name):
    df = utils.return_master_schedule_by_sheet(dept_name)
    

    output_list = []
    for index, teacher_row in df.iterrows():
        for period in range(1,10):
            period_col = f'Period{period}'
            course_code = teacher_row[period_col]
            course_code = course_code.replace("+", '')
            
            if course_code and course_code[0]!='_':
                if course_code not in ['GQS11', 'GAS81', 'GQS21', 'GQS22', 'GAS85']:
                    output_list.extend(create_courses(teacher_row,period))

    return output_list

def create_courses(teacher_row,period):
    period_col = f'Period{period}'
    course_code = teacher_row[period_col]
    course_code = course_code.replace("+",'').replace("-", '')
    if len(course_code) == 5 and course_code[0] not in ['F'] and course_code[0:2] not in ['ES','GQ']:
        if course_code not in ['MQS21','MQS22','MGS11','MES11']:
            return [create_master_course(teacher_row,period),create_mapped_course(teacher_row,period)]
    if course_code[0:4] in ['MQS1']:
        return create_mapped_elective_course_pair(teacher_row, period)
    
    return [create_master_course(teacher_row,period)]


def create_mapped_elective_course_pair(teacher_row, period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = '02M600'
    SchoolYear = school_year_str
    

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"
    offset = course_code.count("+")
    course_code = course_code.replace("+", '').replace("-", '')

    temp_codes = []
    temp_dict = {
        'SchoolDBN': SchoolDBN,
        'SchoolYear': SchoolYear,
        'TermID': TermID,
        'CourseCode': return_course_code(course_code),
        'SectionID': return_section_number(teacher_row, period),
        'Course Name': '',
        'PeriodID': f"{period}",
        'Cycle Day': cycle_day,
        'Capacity': return_mapped_capacity(course_code),
        'Remaining Capacity': return_mapped_capacity(course_code),
        'Gender': '0',
        'Teacher Name': return_teacher_name(teacher_row),
        'Room': '',
        'Mapped Course': return_elective_mapped_course_code(teacher_row, period),
        'Mapped Section': return_section_number(teacher_row, period),
        'Bell Schedule': 'A',
    }
    temp_codes.append(temp_dict)

    temp_dict = {
        'SchoolDBN': SchoolDBN,
        'SchoolYear': SchoolYear,
        'TermID': TermID,
        'CourseCode': return_elective_mapped_course_code(teacher_row, period),
        'SectionID': return_section_number(teacher_row, period),
        'Course Name': '',
        'PeriodID': f"{period}",
        'Cycle Day': cycle_day,
        'Capacity': return_mapped_capacity(course_code),
        'Remaining Capacity': return_mapped_capacity(course_code),
        'Gender': '0',
        'Teacher Name': return_teacher_name(teacher_row),
        'Room': '',
        'Mapped Course': '',
        'Mapped Section': '',
        'Bell Schedule': 'A',
    }
    temp_codes.append(temp_dict)

    return temp_codes


def return_elective_mapped_course_code(teacher_row, period):
    course_code = teacher_row[f"Period{period}"]
    elective_mapped_course_code = course_code
    teacher_name = return_teacher_name(teacher_row)


    if course_code[0:5] == 'MQS11':
        if teacher_name in ['LATANZA E']:
            return 'MQS11QG'
        if teacher_name in ['DYE S']:
            return 'MQS11QGT'
        if teacher_name in ['MATELUS J']:
            return 'MQS11QF'
        if teacher_name in ['WALKER B']:
            return 'MQS11QFT'

    return elective_mapped_course_code

def create_mapped_course(teacher_row,period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = '02M600'
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"
    offset = course_code.count("+")
    course_code = course_code.replace("+",'').replace("-", '')

    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_mapped_course_code(course_code),
    'SectionID':return_section_number(teacher_row,period),
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':cycle_day,
    'Capacity':return_mapped_capacity(course_code),
    'Remaining Capacity':return_mapped_capacity(course_code),
    'Gender':'0',
    'Teacher Name':return_teacher_name(teacher_row),
    'Room':'',
    'Mapped Course':return_course_code(course_code),
    'Mapped Section':return_section_number(teacher_row,period),
    'Bell Schedule':'A',
    }
    return temp_dict

def create_master_course(teacher_row,period):
    school_year = session["school_year"]
    term = session["term"]
    school_year_str = f"{int(school_year)}-{int(school_year)+1}"
    TermID = str(term)

    SchoolDBN = '02M600'
    SchoolYear = school_year_str

    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")
    course_code = course_code.replace("+",'').replace("-", '')
    cycle_day = "'11111"

    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_course_code(course_code),
    'SectionID':f'{return_section_number(teacher_row,period)}',
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(course_code,return_section_number(teacher_row,period)),
    'Remaining Capacity':return_capacity(course_code,return_section_number(teacher_row,period)),
    'Gender':'0',
    'Teacher Name':return_teacher_name(teacher_row),
    'Room':'',
    'Mapped Course':'',
    'Mapped Section':'',
    'Bell Schedule':'A',
    }
    return temp_dict

def return_teacher_name(teacher_row):
    first_name = teacher_row['first_name']
    
    last_name = teacher_row['last_name']
    if len(first_name) > 0:
        return last_name.replace(' ','').replace('-','').upper() +' '+ first_name[0].upper()
    else:
        return last_name.replace(' ','').replace('-','').upper()

def return_section_number(teacher_row,period,cycle=None):
    TeacherID = teacher_row['TeacherID']
    course_code = teacher_row[f"Period{period}"]
    offset = course_code.count("+")

    section = TeacherID*10+period + offset

    offset = course_code.count("-")
    section -= offset

    if course_code in ['HGS43X','HGS43X']:
        if period == 2:
            return section - 1
    if course_code in ['HUS21X','HUS22X']:
        if period == 2:
            return section - 1
    if cycle:
        return (TeacherID+period)*10 + {"A":1,"B":2,"C":3,"D":4,"E":5}[cycle]+offset
    else:
        if section == 0:
            section = 1
        return section

def return_capacity(course_code, section=None):
    return return_adjusted_capacity(course_code,section)

def return_default_capacity(course_code,section=None):
    if course_code == 'EES87QD' and section == 47:
        return 34
    if course_code in ['MQS21','MQS22']:
        return 39
    if len(course_code) > 5:
        if course_code[5] in ['X','H']:
            return 34
    if course_code[0:2] == 'ES':
        return 34
    
    if course_code in ['AUS11QE']:
        return 32
    if course_code[0:2] == 'PP':
        return 50
    if course_code[0:2] == 'GQ':
        return 34
    if course_code[0:2] == 'PH':
        return 33
    if course_code[0:2] == 'ZL':
        return 450
    if course_code[0:2] == 'ZA':
        return 9999
    if course_code in ['EES81QE','EES82QE','EES83QE','EES84QE','EES85QE','EES86QE']:
        return 22
    if course_code[0:5] in ['EES87','EES88']:
        if course_code[-1] == 'T':
            return 12
        if course_code[-1] == 'M':
            return 15
        if course_code[-2:] == 'QP':
            return 2
        if course_code[-2:] == 'QD':
            return 22
        if course_code[-2:] == 'QC':
            return 22
        if course_code[-2:] in ['QF','QW']:
            return 35
        return 32
    if course_code[0:2] == 'AF':
        return 28
    if course_code[0:2] in ['BM','BN']:
        return 32
    if course_code[0:2] == 'FS':
        return 34
    if course_code[-2:] == 'QE':
        return 4
    if course_code[-2:] == 'QM':
        return 15
    if course_code[-3:] == 'QEM':
        return 15
    if course_code[-2:] == 'QT':
        return 12
    if course_code[-3:] == 'QET':
        return 12
    if course_code[-2:] == 'QA':
        return 20
    if course_code[-3:] == 'QEA':
        return 20
    if course_code[-2:] == 'QP':
        return 4
    if course_code[-1] in ['H','X']:
        return 32
    return 30

def return_course_code(course_code):
    if course_code[0] in ['P','G','A','B','T','Z']:
        return course_code
    if len(course_code) == 7:
        if course_code[5] != 5 and course_code[-2:] == 'QA':
            return course_code[0:5]
    return course_code

def return_mapped_course_code(course_code):
    if len(course_code) == 5:
        return course_code[0:5] + 'QP'
    return course_code


def return_mapped_capacity(course_code):
    if len(course_code) == 5:
        course_code = course_code +'QP'
    return return_adjusted_capacity(course_code)

def return_adjusted_capacity(course_code,section=None):
    default_capacity = return_default_capacity(course_code,section)
    adjustment_dict = {
    }

    adjustment = adjustment_dict.get(course_code, 0)
    if adjustment < 0:
        adjustment += 1

    return default_capacity + adjustment
