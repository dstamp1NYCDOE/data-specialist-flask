import app.scripts.programming.master_schedule.utils as utils
import app.scripts.programming.master_schedule.spreadsheet_ids as spreadsheet_ids


def main(dept_name):
    df = utils.return_master_schedule_by_sheet(dept_name)

    output_list = []
    for index, teacher_row in df.iterrows():
        for period in range(1,10):
            period_col = f'Period{period}'
            course_code = teacher_row[period_col]
            if course_code and course_code[0]!='_':
                output_list.extend(create_courses(teacher_row,period))

    return output_list


def create_courses(teacher_row,period):
    period_col = f'Period{period}'
    course_code = teacher_row[period_col]
    output = []
    if course_code in ['PPS87/PPS85']:
        for course_code_temp in ['PPS87','PPS85']:
            teacher_row[period_col] = course_code_temp
            for day,cycle_day in [("A","'01010"),("B","'10101")]:
                output.append(create_mapped_course(teacher_row,period,day,cycle_day))
                output.append(create_master_course(teacher_row,period,day,cycle_day))
    elif course_code in ['PHS21/PPS83']:
        for course_code_temp,day,cycle_day in [('PPS83','A',"'01010"),("PHS21","B","'10101")]:
            teacher_row[period_col] = course_code_temp
            output.append(create_mapped_course(teacher_row,period,day,cycle_day))
            output.append(create_master_course(teacher_row,period,day,cycle_day))
    elif course_code in ['PPS81']:
        for day,cycle_day in [("A","'01010"),("B","'10101")]:
            output.append(create_mapped_course(teacher_row,period,day,cycle_day))
            output.append(create_master_course(teacher_row,period,day,cycle_day))
            if day == 'A':
                output.append(create_mapped_9th_grade_lunch_course(teacher_row,period,day,cycle_day))
    elif course_code in ['PPS83','PHS21']:
        for day, cycle_day in [("A", "'01010"), ("B", "'10101")]:
            output.append(create_mapped_course(
                teacher_row, period, day, cycle_day))
            output.append(create_master_course(
                teacher_row, period, day, cycle_day))
    elif course_code in ['PPS83/', 'PHS21/']:
        for course_code_temp, day, cycle_day in [("PHS21", "B", "'10101")]:
            teacher_row[period_col] = course_code_temp
            output.append(create_mapped_course(
                teacher_row, period, day, cycle_day))
            output.append(create_master_course(
                teacher_row, period, day, cycle_day))
        # output.append(create_mental_health_mondays(
        #             teacher_row, period, day, cycle_day))
        # output.append(map_mental_health_mondays(
        #     teacher_row, period, day, cycle_day))
    elif course_code in ['PHS11']:
        day = ""
        cycle_day = "11111"
        output.append(create_master_course(
                teacher_row, period, day, cycle_day))        
    else:
        for day,cycle_day in [("A","'01010"),("B","'10101")]:
            output.append(create_mapped_course(teacher_row,period,day,cycle_day))
            output.append(create_master_course(teacher_row,period,day,cycle_day))
    return output


def create_mental_health_mondays(teacher_row, period, day, cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = 'GAS83'
    
    cycle_day = "'10000"
    temp_dict = {
        'SchoolDBN': SchoolDBN,
        'SchoolYear': SchoolYear,
        'TermID': TermID,
        'CourseCode': return_course_code(course_code, day),
        'SectionID': return_section_number(teacher_row, period, day),
        'Course Name': '',
        'PeriodID': f"{period}",
        'Cycle Day': cycle_day,
        'Capacity': return_capacity(course_code, period),
        'Remaining Capacity': return_capacity(course_code, period),
        'Gender': '0',
        'Teacher Name': return_teacher_name(teacher_row),
        'Room': '',
        'Mapped Course': '',
        'Mapped Section': '',
        'Bell Schedule': 'A',
    }
    return temp_dict

def map_mental_health_mondays(teacher_row, period, day, cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    cycle_day = "'10000"
    temp_dict = {
        'SchoolDBN': SchoolDBN,
        'SchoolYear': SchoolYear,
        'TermID': TermID,
        'CourseCode': return_mapped_course_code(course_code, day),
        'SectionID': return_section_number(teacher_row, period, day),
        'Course Name': '',
        'PeriodID': f"{period}",
        'Cycle Day': cycle_day,
        'Capacity': return_capacity(course_code, period),
        'Remaining Capacity': return_capacity(course_code, period),
        'Gender': '0',
        'Teacher Name': return_teacher_name(teacher_row),
        'Room': '',
        'Mapped Course': return_course_code('GAS83', day),
        'Mapped Section': return_section_number(teacher_row, period, day),
        'Bell Schedule': 'A',
    }
    return temp_dict

def create_mapped_9th_grade_lunch_course(teacher_row,period,day,cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_mapped_course_code(course_code,day),
    'SectionID':return_section_number(teacher_row,period,day),
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':"'10000",
    'Capacity':return_capacity(course_code, period),
    'Remaining Capacity':return_capacity(course_code, period),
    'Gender':'0',
    'Teacher Name':'STAFF',
    'Room':'CAFE',
    'Mapped Course':'ZL9',
    'Mapped Section':f'{period}',
    'Bell Schedule':'A',
    }
    return temp_dict


def create_mapped_course(teacher_row,period,day,cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID

    course_code = teacher_row[f"Period{period}"]
    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_mapped_course_code(course_code,day),
    'SectionID':return_section_number(teacher_row,period,day),
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(course_code, period),
    'Remaining Capacity':return_capacity(course_code, period),
    'Gender':'0',
    'Teacher Name':return_teacher_name(teacher_row),
    'Room':'',
    'Mapped Course':return_course_code(course_code, day),
    'Mapped Section':return_section_number(teacher_row,period,day),
    'Bell Schedule':'A',
    }
    return temp_dict

def create_master_course(teacher_row,period,day,cycle_day):
    SchoolDBN = spreadsheet_ids.SchoolDBN
    SchoolYear = spreadsheet_ids.SchoolYear
    TermID = spreadsheet_ids.TermID
    course_code = teacher_row[f"Period{period}"]

    temp_dict = {
    'SchoolDBN':SchoolDBN,
    'SchoolYear':SchoolYear,
    'TermID':TermID,
    'CourseCode':return_course_code(course_code,day),
    'SectionID':return_section_number(teacher_row,period,day),
    'Course Name':'',
    'PeriodID':f"{period}",
    'Cycle Day':cycle_day,
    'Capacity':return_capacity(course_code, period),
    'Remaining Capacity':return_capacity(course_code, period),
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
    
    offset = int(course_code[-1])
    section = TeacherID*10+period

    if cycle:
        return (10*period) + TeacherID + {"A":1,"B":2,"C":3,"D":4,"E":5}.get(cycle,0)
        return (TeacherID*5+period*3-2*offset) + {"A":1,"B":2,"C":3,"D":4,"E":5}[cycle]
    else:
        if section == 0:
            section = 1
        return section

def return_capacity(course_code, period):
    if course_code in ['PPS83']:
        return 35
    if course_code in ['PHS21', 'GAS83','PHS11']:
        return 34
    if course_code in ['PPS81',]:
        if period in [4,7]:
            return 25*2
        else:
            return 25
    else:
        return 25

def return_course_code(course_code, day):
    if day == '':
        return course_code
    return course_code + 'Q' + day


def return_mapped_course_code(course_code, day):
    return course_code
