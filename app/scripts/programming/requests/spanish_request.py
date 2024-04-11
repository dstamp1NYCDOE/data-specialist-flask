
def main(student, student_transcript):
    year_in_hs = student['year_in_hs']
    
    lote_earned = student_transcript['F_earned']


    if year_in_hs == 4:
        if lote_earned < 2:
            return ['FSS61Q2']

    return ['']

