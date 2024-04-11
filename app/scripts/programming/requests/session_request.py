
def main(student, student_transcript, best_on_time_students_by_year_in_hs):
    year_in_hs = student['year_in_hs']
    StudentID = student['StudentID']

    if year_in_hs == 1:
        return ['ZM29']
    if year_in_hs == 2:
        return ['ZM29']
    if year_in_hs > 2:
        if StudentID in best_on_time_students_by_year_in_hs:
            return ['ZM18']
        else:
            return ['ZM29']