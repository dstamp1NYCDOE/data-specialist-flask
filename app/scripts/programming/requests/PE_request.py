def main(student, student_transcript, student_iep):
    year_in_hs = student["year_in_hs"]

    pe_earned = student_transcript["PP_earned"]
    health_earned = student_transcript["PH_earned"]

    if year_in_hs == 2:
        if health_earned >= 1:
            PE_courses = ["PPS83"]
        else:
            PE_courses = ["PHS21", "PPS83"]
    if year_in_hs == 3:
        if pe_earned >= 1.5:
            PE_courses = ["PPS85", "GAS85"]
            PE_courses = ["PPS85"]
        elif health_earned == 0:
            PE_courses = ["PHS11", "PPS85"]
        else:
            PE_courses = ["PPS85", "PPS87"]
    if year_in_hs == 4:
        if health_earned >= 1:
            PE_courses = ["PPS87", "GQS22"]
        elif health_earned == 0:
            PE_courses = ["PHS11", "PPS87", "GQS22"]
        else:
            PE_courses = ["PHS21", "PPS87", "GQS22"]

    return PE_courses
