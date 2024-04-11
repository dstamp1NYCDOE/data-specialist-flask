
def main(student, student_transcript, student_iep):
    year_in_hs = student['year_in_hs']
    
    Alg_earned = student_transcript['ME_earned']
    Geo_earned = student_transcript['MG_earned']
    Trig_earned = student_transcript['MR_earned']
    PreCalc_earned = student_transcript['MP_earned']

    Alg_attempted = student_transcript['ME_attempted']
    Geo_attempted = student_transcript['MG_attempted']
    Trig_attempted = student_transcript['MR_attempted']
    PreCalc_attempted = student_transcript['MP_attempted']

    total_math_earned = student_transcript['M_earned']

    

    if year_in_hs == 2:
        if Geo_attempted == 0:
            output_course = 'MGS21'
        elif Trig_attempted == 0:
            output_course = 'MRS21'
        elif PreCalc_attempted == 0:
            output_course = 'MPS21'
        else:
            output_course = 'MQS11'
    if year_in_hs == 3:
        if Geo_attempted == 0:
            output_course = 'MGS21'
        elif Trig_attempted == 0:
            output_course = 'MRS21'
        elif PreCalc_attempted == 0:
            output_course = 'MPS21'
        else:
            output_course = 'MQS11'
    if year_in_hs == 4:
        if total_math_earned >= 6:
            output_course = ''
            return [output_course]
        else:
            if Geo_attempted == 0:
                output_course = 'MGS21'
            elif Trig_attempted == 0:
                output_course = 'MRS21'
            elif PreCalc_attempted == 0:
                output_course = 'MPS21'
            else:
                output_course = 'MQS11'


    if student_iep:
        output_course = output_course + student_iep.get('M')
        
    return [output_course]


