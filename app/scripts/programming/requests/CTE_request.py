
def main(student, student_transcript, majors_dict):
    year_in_hs = student['year_in_hs']
    StudentID = student['StudentID']
    major = majors_dict.get(StudentID)
    
    if major == 'FD':
        if year_in_hs == 2:
            return ['AFS61TF']
        if year_in_hs == 3:
            return ['AFS63TD']
        if year_in_hs == 4:
            return ['AFS65TC','AFS11QE']
        
    if major == 'VP':
        if year_in_hs == 2:
            return ['BMS61TV']
        if year_in_hs == 3:
            return ['BMS63TT']
        if year_in_hs == 4:
            return ['BMS65TW', 'BMS11QE']

    if major == 'FMM':
        if year_in_hs == 2:
            return ['TUS21TA']
        if year_in_hs == 3:
            return ['BRS11TF']
        if year_in_hs == 4:
            return ['BNS21TV', 'BNS11QCA']

    if major == 'WD':
        if year_in_hs == 2:
            return ['SKS21X']
        if year_in_hs == 3:
            return ['TQS21TQW']
        if year_in_hs == 4:
            return ['TQS21TQS', 'TQS11QE']

    if major == 'Photo':
        if year_in_hs == 2:
            return ['ACS21T']
        if year_in_hs == 3:
            return ['ACS22T']
        if year_in_hs == 4:
            return ['ALS21TP', 'AUS11QE']

    if major == 'A&D':
        if year_in_hs == 2:
            if StudentID % 2 == 0:
                return ['AUS11TA']
            else:
                return ['APS11T']
        if year_in_hs == 3:
            if StudentID % 2 == 0:
                return ['ACS11TD']
            else:
                return ['AES11TE']
        if year_in_hs == 4:
            return ['ALS21T', 'AUS11QE']

    return ['']
