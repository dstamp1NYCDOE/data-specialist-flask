
def main(student, student_transcript, student_iep):
    year_in_hs = student['year_in_hs']
    LEPFlag = student['LEPFlag']

    ELA_course = f'EES8{2*year_in_hs-1}'

    if LEPFlag == 'Y' and student_iep:
        if student_iep.get('E') in ['QT']:
            ELA_course = ELA_course + 'QET'
        else:
            ELA_course = ELA_course + 'QE'
    elif LEPFlag == 'Y':
        ELA_course = ELA_course + 'QE'
    elif student_iep:
        ELA_course = ELA_course + student_iep.get('E')

    return [ELA_course]
