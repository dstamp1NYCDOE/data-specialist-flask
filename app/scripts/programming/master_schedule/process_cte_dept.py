import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids

def main(dept_name):
    df = utils.return_master_schedule_by_sheet(dept_name)

    output_list = []
    for index, teacher_row in df.iterrows():
        for period in range(1,10):
            period_col = f'Period{period}'
            course_code = teacher_row[period_col]
            if course_code:
                if course_code not in ['GQS11','GAS81']:
                    output_list.extend(create_courses(teacher_row,period))

    return output_list

def create_courses(teacher_row,period):
    period_col = f'Period{period}'
    course_code = teacher_row[period_col]
    single_period_courses = [
    'AUS11',
    'ABS11',
    'ANS11',
    'AWS11',
    'AGS11',
    'AYS11',
    'AFS11QE',
    'APS21X',
    'BMS11QE',
    'AUS11QE',
    'BNS11QCA',
    'MKS21H',
    'MKS21X',
    'RZS41',
    'RZS42',
    'RZS43',
    'RZS44',
    ]
    if course_code in single_period_courses:
        return [create_master_course(teacher_row,period)]
    else:
        return [create_master_course(teacher_row,period),create_cte_double_period(teacher_row,period)]

def create_master_course(teacher_row,period):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
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
    'Capacity':return_capacity(course_code),
    'Remaining Capacity':return_capacity(course_code),
    'Gender':'0',
    'Teacher Name':return_teacher_name(teacher_row),
    'Room':'',
    'Mapped Course':'',
    'Mapped Section':'',
    'Bell Schedule':'A',
    }
    return temp_dict

def create_cte_double_period(teacher_row,period):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'11111"

    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_course_code(course_code),
    'SectionID':f'{return_section_number(teacher_row,period)}',
    'Course Name':'',
    'PeriodID':period+1,
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(course_code),
    'Remaining Capacity':return_capacity(course_code),
    'Gender':'0',
    'Teacher Name':return_teacher_name(teacher_row),
    'Room':'',
    'Mapped Course':'',
    'Mapped Section':'',
    'Bell Schedule':'A',
    }
    return temp_dict


def return_capacity(course_code):
    sequence_dict = {
        'ABS11': 28,
        'AYS11': 28,

        'AWS11': 31,
        'AUS11': 31,

        'ANS11': 30,
        'AGS11': 30,


        'ACS11TD': 28,
        'ACS21T': 28,
        'ACS22TD': 28,
        'AES11TE': 28,

        'AFS11QE': 28,
        'AFS61TF': 28,
        'AFS63TD': 28,
        'AFS63TDB': 28,
        'AFS65TC': 28,
        'AFS65TCC': 28,
        'AFS65TCH': 28,
        'ALS21T': 28,
        'ALS21TP': 28,
        
        'APS11TA': 28,
        
        'AUS11QE': 30,
        'AUS11TA': 28,
        

        'BMS11QE': 28,
        'BMS61TV': 28,
        'BMS63TT': 28,
        'BMS65TW': 28,

        'BNS11QCA': 30,
        'BNS21TV': 30,
        'BRS11TF': 30,
        'TUS21TA': 28,

        'SKS21X': 28,
        'MKS21H': 28,
    }
    default_seats = sequence_dict.get(course_code, 28)
    adjusted_seats = adjust_seat_capcity(course_code, default_seats)
    return adjusted_seats

def adjust_seat_capcity(course_code, default_seats):
    adjustment_dict = {
        'ABS11': 0,
        'ACS11TD': -4,
        'ACS21T': -3,
        'ACS22T': 0,
        'AES11TE': -4,
        'AFS11QE': -2,
        'AFS61TF': -4,
        'AFS63TD': -1,
        'AFS63TDB': -11,
        'AFS63TDC': -7,
        'AFS65TC': -4,
        'AFS65TCH': -3,
        'ALS21T': -4,
        'ALS21TP': -3,
        'ANS11': 0,
        'APS11T': -3,
        'APS21X': 0,
        'AUS11': 0,
        'AUS11QE': 0,
        'AUS11TA': 0,
        'AWS11': 0,
        'BMS11QE': -14,
        'BMS61TV': -4,
        'BMS63TT': -10,
        'BMS65TW': -14,
        'BNS11QCA': -1,
        'BNS21TV': -1,
        'BRS11TF': 0,
    }

    return default_seats + adjustment_dict.get(course_code,0)


def return_course_code(course_code):
    return course_code

def return_teacher_name(teacher_row):
    first_name = teacher_row['first_name']
    last_name = teacher_row['last_name']
    if len(first_name) > 0:
        return last_name.replace(' ','').replace('-','').upper() +' '+ first_name[0].upper()
    else:
        return last_name.replace(' ','').replace('-','').upper()

def return_section_number(teacher_row,period,cycle=None):
    TeacherID = teacher_row['TeacherID']
    section = TeacherID*10+period
    if cycle:
        return (TeacherID+period)*10 + {"A":1,"B":2,"C":3,"D":4,"E":5}[cycle]
    else:
        if section == 0:
            section = 1
        return section
