def main(student_data):
    requests = []
    ## update individual requests
    for request in student_data['requests']:
        if request.startswith('S') and request != 'SKS21X':
            request = update_science_request(request, student_data)
        if request.startswith('M'):
            request = update_math_request(request, student_data)
        if request.startswith('ZM'):
            request = update_session_request(request, student_data)
        if request in ['APS11T','AUS11TA']:
            course_a = 'APS11T'
            course_b = 'AUS11TA'
            request = split_course(course_a,course_b,75-3)
        if request in ['BRS11TF','BKS11TE']:
            course_a = 'BRS11TF'
            course_b = 'BKS11TE'
            request = split_course(course_a,course_b,25-1)
        if request in ['BQS11T','TUS21TA']:
            course_a = 'BQS11T'
            course_b = 'TUS21TA'
            request = split_course(course_a,course_b,25-1)    
        # if request in ['MGS21','MRS21']:
        #     request = move_to_honors_math(request, student_data) 
        requests.append(request)
    ## update by looking at full list
    requests = update_pe_request(requests, student_data)
    requests = replace_sci_request_with_math_elective_request(requests, student_data)
    # requests = move_to_ap_pre_calc(requests, student_data)
    
 
    ## remove duplicates
    requests = list(set(requests))

    return requests

def move_to_honors_math(course,student_data):
    # Initialize counters dictionary if it doesn't exist
    if not hasattr(move_to_honors_math, 'counters'):
        move_to_honors_math.counters = {'MRS21':0,'MGS21':0}
    

    num_to_move = 999
    if course == 'MGS21':
        regents_max = student_data['regents_max']
        
        geo_score = regents_max.get('GEOMETRY REG NumericEquivalent',0)
        alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)


        if alg_score >= 70:
            if move_to_honors_math.counters[course] < num_to_move:
                move_to_honors_math.counters[course] += 1
                return course + 'H'
        else:
            return course

    if course == 'MRS21':
        regents_max = student_data['regents_max']
        
        geo_score = regents_max.get('GEOMETRY REG NumericEquivalent',0)
        alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)

        if alg_score >= 75 and geo_score >= 70:
            if move_to_honors_math.counters[course] < num_to_move:
                move_to_honors_math.counters[course] += 1
                return course + 'H'
        else:
            return course

    return course

def split_course(course_a, course_b, split_num):
    # Initialize counters dictionary if it doesn't exist
    if not hasattr(split_course, 'counters'):
        split_course.counters = {}
    
    # Initialize counter for this specific course_a if it doesn't exist
    if course_a not in split_course.counters:
        split_course.counters[course_a] = 0
    
    # Check if we haven't reached the split limit yet
    if split_course.counters[course_a] < split_num:
        split_course.counters[course_a] += 1
        return course_a
    return course_b


def append_sped_rec(course,recommended_program):
    dept = course[0]
    if dept in recommended_program.keys():
        if course.endswith('QQ'):
            return course[:-2] + recommended_program[dept]
        return course + recommended_program[dept]
    return course

def update_session_request(session_course,student_data):
    recommended_program = student_data['recommended_program']
    year_in_hs = student_data['year_in_hs']
    if recommended_program.get('Transportation') == True and year_in_hs > 2:
        session_course = 'ZM18'
    return session_course

def move_to_ap_pre_calc(requests,student_data):
    if not hasattr(move_to_ap_pre_calc, 'counter'):
        move_to_ap_pre_calc.counter = 0
    
    for current_course in ['MPS21','MPS21QP']:
        if current_course in requests:
            regents_max = student_data['regents_max']
            num_to_move = 22
            alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)
            geo_score = regents_max.get('GEOMETRY REG NumericEquivalent',0)
            trig_score = regents_max.get('ALG2/TRIG REG NumericEquivalent',0)

            if alg_score >= 80 and (geo_score >= 65 or trig_score >= 65):
                if move_to_ap_pre_calc.counter < num_to_move:
                    move_to_ap_pre_calc.counter += 1
                    requests.remove(current_course)
                    requests.append('MPS21XX')
                    return requests
            elif alg_score >= 65 or geo_score >= 65 or trig_score >= 65:
                return requests
            else:
                requests.remove(current_course)
                requests.append('MQS11')
                return requests

    return requests

def update_science_request(course,student_data):
    year_in_hs = student_data['year_in_hs']
    regents_max = student_data['regents_max']
    num_sci_passed = regents_max.get("S Passed Count",0)
    recommended_program = student_data['recommended_program']

    print(regents_max)
    liv_env_score = regents_max.get('LIVING ENV NumericEquivalent',0)
    es_score = regents_max.get('EARTH SCI  REG NumericEquivalent',0)

    attempted_le_flag = liv_env_score > 0
    attempted_es_flag = es_score > 0

    cutoff = 65
    liv_env_cutoff_met = liv_env_score >= cutoff
    es_cutoff_met = es_score >= cutoff

    print(course)
    print(num_sci_passed)
    print(liv_env_score)
    print(es_score)

    ## check if student is on track for two science regents exams
    if year_in_hs == 2 and num_sci_passed >= 1:
        return course
    if year_in_hs == 3 and num_sci_passed >= 2:
        return course
    if year_in_hs == 4 and num_sci_passed >= 3:
        return course
    ## check if student should do repeaters or circle back to a standalone first attempt at a course
    #### Check if sophomores should repeat into a second year the science they took the year before
    if year_in_hs in [2] and num_sci_passed == 0 and attempted_le_flag and not attempted_es_flag:
        return append_sped_rec('SBS43',recommended_program)
    if year_in_hs in [2] and num_sci_passed in [0,1] and not attempted_le_flag and attempted_es_flag:
        return append_sped_rec('SJS43',recommended_program)
    ## if a junior who hasn't attempted earth science go into the standalone SJS21QQ course for 11th and 12th grade students
    if year_in_hs in [3] and num_sci_passed == 0 and not attempted_es_flag:
        return append_sped_rec('SJS21QQ',recommended_program)
    ## if a junior who has attempted earth science and has not passed 0 or 1 science regents go into the SJS43 course
    if year_in_hs in [3] and num_sci_passed in [0,1] and es_score > 0:
        return append_sped_rec('SJS43',recommended_program)
    ## if a senior, look at a reduced cutoff score and say if the student meets that lower score, they will go into their current science class
    #### if they dont meet that score, they will go into the standalone SJS21QQ course as their last attempt.
    if year_in_hs in [4] and num_sci_passed == 0:
        if recommended_program == {}:
            cutoff = 60
        else:
            cutoff = 55
        liv_env_cutoff_met = liv_env_score >= cutoff
        es_cutoff_met = es_score >= cutoff

        if liv_env_cutoff_met or es_cutoff_met:
            return course
        else:
            return append_sped_rec('SJS21QQ',recommended_program)                  
    return course

def update_math_request(course,student_data):
    year_in_hs = student_data['year_in_hs']
    regents_max = student_data['regents_max']
    num_math_passed = regents_max.get("M Passed Count",0)
    recommended_program = student_data['recommended_program']
    if year_in_hs == 2 and num_math_passed == 0:
        return append_sped_rec('MES43',recommended_program)
    elif year_in_hs > 2 and num_math_passed == 0:
        alg_score = regents_max.get('ALGEBRA REG NumericEquivalent',0)
        geo_score = regents_max.get('GEOMETRY REG NumericEquivalent',0)
        trig_score = regents_max.get('ALG2/TRIG REG NumericEquivalent',0)
        if recommended_program == {}:
            cutoff = 60
        else:
            cutoff = 55
        alg_cutoff_met = alg_score >= cutoff
        geo_cutoff_met = geo_score >= cutoff
        trig_cutoff_met = trig_score >= cutoff

        if alg_cutoff_met or geo_cutoff_met or trig_cutoff_met:
            return course
        else:
            return append_sped_rec('MES21QQ',recommended_program)

    return course

def update_pe_request(course_lst,student_data):
    year_in_hs = student_data['year_in_hs']
    pe_requested = [course for course in course_lst if course.startswith('PP')]
    non_pe_requested = [course for course in course_lst if not course.startswith('PP')]
    
    num_in_pps87 = 0
    num_in_pps85 = 13
    if year_in_hs < 3:
        pass
    elif len(pe_requested)>=2:
        progress_towards_graduation = student_data['progress_towards_graduation']
        credit_area = 'PE (4)'
        pe_deficiency=progress_towards_graduation[f"{credit_area}-Deficiency"]    
        if year_in_hs == 4:
            pe_to_take = ['PPS87','PPS11']
        if year_in_hs == 3:
            pe_to_take = ['PPS85','PPS11']
        else:
            pe_to_take = ['PPS83','PPS11']  
        if pe_deficiency == 0.5:
            pe_to_take = pe_to_take[0:1]
        
        course_lst = non_pe_requested + pe_to_take
        
        return course_lst
    
    return course_lst

def update_PPS85_PPS87(course_lst,student_data,num_in_pps85,num_in_pps87):
    year_in_hs = student_data['year_in_hs']
    pe_requested = [course for course in course_lst if course.startswith('PP')]
    non_pe_requested = [course for course in course_lst if not course.startswith('PP')]

    if year_in_hs in [3,4]:
        pe_requested = split_PE_requests(year_in_hs,num_in_pps85,num_in_pps87)
        course_lst = non_pe_requested + pe_requested
        return course_lst
    
    return course_lst    

def split_PE_requests(year_in_hs,num_in_pps85,num_in_pps87):
    if not hasattr(split_PE_requests, 'year_3_calls'):
        split_PE_requests.year_3_calls = num_in_pps85
    if not hasattr(split_PE_requests, 'year_4_calls'):
        split_PE_requests.year_4_calls = num_in_pps87

    if year_in_hs == 3 and split_PE_requests.year_3_calls < 260:
        split_PE_requests.year_3_calls += 1
        return ['PPS85']
    if year_in_hs == 4 and split_PE_requests.year_4_calls < 260:
        split_PE_requests.year_4_calls += 1
        return ['PPS87']
    return ['PPS11']

def replace_sci_request_with_math_elective_request(course_lst,student_data):
    year_in_hs = student_data['year_in_hs']
    if year_in_hs <= 3:
        return course_lst
    sci_requested = [course for course in course_lst if course.startswith('S')]
    math_requested = [course for course in course_lst if course.startswith('M')]

    if len(sci_requested) == 0 and len(math_requested) == 0:
        return course_lst

    #sci courses to not remove
    sci_not_to_remove = ['SBS21X','SDS21QQ7']
    if any(course in sci_not_to_remove for course in sci_requested):
        return course_lst
    
    ## check if met science graduation requirment
    progress_towards_graduation = student_data['progress_towards_graduation']
    life_science_deficiency=progress_towards_graduation["Life Science (2)-Deficiency"]
    phy_science_deficiency=progress_towards_graduation["Phy. Science (2)-Deficiency"]
    life_or_phy_science_deficiency=progress_towards_graduation["Life or Phys. Science (2)-Deficiency"]


    if life_science_deficiency == 0 and phy_science_deficiency == 0 and life_or_phy_science_deficiency == 0 and len(math_requested) == 0:
        for sci_course in sci_requested:
            course_lst.remove(sci_course)
        if 'ZM18' not in course_lst and 'ZM29' not in course_lst and 'ZM1' not in course_lst:
            if 'ZA' not in course_lst:
                course_lst.append('ZM1')
        else:
            recommended_program = student_data['recommended_program']  
            course_to_add = 'MQS11'
            course_to_add = append_sped_rec(course_to_add,recommended_program)          
            course_lst.append(course_to_add)

    return course_lst
    
    