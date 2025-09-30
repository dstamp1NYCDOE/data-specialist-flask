

def main(student_data):
    ## start with lunch
    requests = ['ZL','ZM29']
    student_data['requests'] = requests
    ## append SS request
    requests.append(return_SS_request(student_data))
    ## append ELA request
    requests.append(return_ELA_request(student_data))
    ## append Math request
    requests.append(return_Math_request(student_data))
    ## append Science request
    requests.append(return_science_request(student_data))
    ## append Health request
    requests.append(append_health_request(student_data))
    ## append PE request
    requests.append(return_PE_request(student_data))

    ## remove blank requests
    requests = [request for request in requests if request != '']

    ## apply recommended programs
    recommended_program = student_data['recommended_program']
    requests = [append_sped_rec(course,recommended_program) for course in requests]

    recommended_program = student_data['recommended_program']
    if recommended_program.get('SETSS') == True:
        requests.append('ZJS11QA')   
        requests.remove('ZM29')

    return requests

def append_sped_rec(course,recommended_program):
    dept = course[0]
    if dept in recommended_program.keys():
        return course + recommended_program[dept]
    return course


def return_PE_request(student_data):
    requests = student_data['requests']
    if 'PHS21' in requests:
        PE_request = 'PPS83'
    else:
        PE_request = 'PPS83'
    return PE_request

def return_SS_request(student_data):
    SWD_flag = student_data['SWD_flag']
    if SWD_flag:
        SS_request = 'HGS43'
    else:
        SS_request = 'HGS43QQ'
    return SS_request

def return_ELA_request(student_data):
    SWD_flag = student_data['SWD_flag']
    if SWD_flag:
        ELA_request = 'EES83'
    else:
        ELA_request = 'EES83QQ'
    return ELA_request


def return_Math_request(student_data):
    Math_request = 'MES43'
    regents_max = student_data['regents_max']
    if regents_max == {}:
        return Math_request
    
    alg_score = regents_max.get('ALGEBRA REG NumericEquivalent')
    alg_passed = regents_max.get('ALGEBRA REG Passed?')
    if alg_passed:
        Math_request = 'MGS21'
    
    return Math_request


def return_science_request(student_data):
    course_request = 'SBS43'
    regents_max = student_data['regents_max']
    if regents_max == {}:
        return course_request

    life_sci_score = regents_max.get('LIVING ENV REG NumericEquivalent')
    life_sci_passed = regents_max.get('LIVING ENV REG Passed?')
    if life_sci_passed:
        course_request = 'SJS21'
    
    return course_request  

def append_health_request(student_data):
    health_earned = student_data['progress_towards_graduation'].get('Health (1)-Earned',0)
    if health_earned == 1:
        return ''
    else:
        return 'PHS21'