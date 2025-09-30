

def main(student_data):
    ## start with lunch
    requests = ['ZL','GSS81']
    student_data['requests'] = requests
    ## append CTE request
    requests.append(return_CTE_request(student_data))    
    ## append SS request
    requests.append(return_SS_request(student_data))
    ## append PE request
    requests.append(return_PE_request(student_data))
    ## append ELA request
    requests.append(return_ELA_request(student_data))
    ## append Math request
    requests.append(return_Math_request(student_data))
    ## append Science request
    requests.append(return_science_request(student_data))
    ## append LOTE request
    requests.append(append_additional_class(student_data))
    # append session
    requests.append(append_session_request(student_data))

    ## remove blank requests
    requests = [request for request in requests if request != '']

    ## apply recommended programs
    recommended_program = student_data['recommended_program']
    requests = [append_sped_rec(course,recommended_program) for course in requests]

    return requests
def append_session_request(student_data):
    session_request = 'ZM1'
    recommended_program = student_data['recommended_program']
    if recommended_program.get('Transportation') == True:
        session_request = 'ZM18'
    return session_request

def append_sped_rec(course,recommended_program):
    dept = course[0]
    if dept in recommended_program.keys():
        return course + recommended_program[dept]
    return course


def return_PE_request(student_data):
    PE_request = 'PPS81'
    return PE_request

def return_CTE_request(student_data):

    SWD_flag = student_data['SWD_flag']
    if SWD_flag:
        return 'ABS11'
    
    regents_max = student_data['regents_max']
    global_score = regents_max.get('GLOBAL REG NumericEquivalent',0)
    ush_score = regents_max.get('US HIST REG NumericEquivalent',0)
    if (global_score>=70 or ush_score>=70) and not SWD_flag:
        return 'ANS11'
    
    ela_score = regents_max.get('ENG REG NumericEquivalent',0)
    if (ela_score>0) and not SWD_flag:
        return 'ANS11'

    alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)
    if (alg_score>0) and not SWD_flag:
        return 'ANS11'

    StudentID = student_data['StudentID']

    if StudentID % 2 == 0:
        return 'ANS11'
    return 'ABS11'


def return_SS_request(student_data):

    SWD_flag = student_data['SWD_flag']

    SS_request = 'HGS41'
    regents_max = student_data['regents_max']
    global_passed = regents_max.get('GLOBAL REG Passed?',0)
    ush_passed = regents_max.get('US HIST REG Passed?',0)

    global_score = regents_max.get('GLOBAL REG NumericEquivalent',0)
    ush_score = regents_max.get('US HIST REG NumericEquivalent',0)
    if (global_score>=70 or ush_score>=70) and not SWD_flag:
        SS_request = 'HGS41QQ'
    return SS_request

def return_ELA_request(student_data):
    SWD_flag = student_data['SWD_flag']

    ELA_request = 'EES81'
    regents_max = student_data['regents_max']
    ela_passed = regents_max.get('ENG REG Passed?',0)
    ela_score = regents_max.get('ENG REG NumericEquivalent',0)

    if (ela_score>0) and not SWD_flag:
        ELA_request = 'EES81QQ'
    return ELA_request


def return_Math_request(student_data):
    Math_request = 'MES21'
    regents_max = student_data['regents_max']
    if regents_max == {}:
        return Math_request
    
    alg_score = regents_max.get('ALGEBRA REG NumericEquivalent')
    alg_passed = regents_max.get('ALGEBRA REG Passed?',0)
    if alg_passed:
        Math_request = 'MGS21'
    elif alg_score > 0:
        Math_request = 'MES43'
    
    return Math_request


def return_science_request(student_data):
    course_request = 'SBS21'
    regents_max = student_data['regents_max']
    if regents_max == {}:
        return course_request

    life_sci_score = regents_max.get('LIVING ENV REG NumericEquivalent',0)
    life_sci_passed = regents_max.get('LIVING ENV REG Passed?')
    if life_sci_passed:
        course_request = 'SJS21'
    elif life_sci_score > 0:
        course_request = 'SBS43'
    
    return course_request  

def append_additional_class(student_data):
    regents_max = student_data['regents_max']
    alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)
    life_sci_score = regents_max.get('LIVING ENV REG NumericEquivalent',0)
    requests = student_data['requests']

    recommended_program = student_data['recommended_program']

    if recommended_program.get('SETSS') == True:
        return 'ZJS11QA'

    if recommended_program:
        if 'MES43' in requests:
            return 'MGS21'
        if 'SBS43' in requests:
            return 'SJS21'
        return 'FSS61'
    

    if 'MES43' in requests:
        return 'MGS21'
    if 'SBS43' in requests:
        return 'SJS21'
    
    if alg_score >= 75:
        return 'MKS21'
    if life_sci_score >= 75:
        return 'MKS21'

    lote_earned = student_data['progress_towards_graduation'].get('LOTE (2/6)-Earned',0)
    if lote_earned == 0:
        return 'FSS61'   
    else:
        return 'MKS21'