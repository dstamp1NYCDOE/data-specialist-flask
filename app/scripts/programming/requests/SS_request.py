
def main(student, student_transcript, student_iep):
    year_in_hs = student['year_in_hs']
    
    global_earned = student_transcript['HG_earned']
    us_earned = student_transcript['HU_earned']
    govt_earned = student_transcript['HV_earned']

    ss_course = ''


    if year_in_hs == 2:
        ss_course = 'HGS43'
    if year_in_hs == 3:
        if us_earned == 2:
            ss_course = 'HVS11'
        else:
            ss_course = 'HUS21'
    if year_in_hs == 4:
        if govt_earned == 1:
            ss_course = ''
            return [ss_course]
        else:
            ss_course = 'HVS11'

    if student_iep:
        ss_course = ss_course + student_iep.get('H')

    return [ss_course]


