def main(student, student_transcript, student_iep):
    year_in_hs = student["year_in_hs"]

    LE_earned = student_transcript["SL_earned"]
    ES_earned = student_transcript["SE_earned"]
    Chem_earned = student_transcript["SC_earned"]
    Phys_earned = student_transcript["SP_earned"]

    phys_elective_earned = student_transcript["SD_earned"]
    life_elective_earned = student_transcript["SW_earned"]

    LE_attempted = student_transcript["SL_attempted"]
    ES_attempted = student_transcript["SE_attempted"]
    Chem_attempted = student_transcript["SC_attempted"]
    Phys_attempted = student_transcript["SP_attempted"]

    phys_elective_attempted = student_transcript["SD_attempted"]
    life_elective_attempted = student_transcript["SW_attempted"]

    total_science_earned = student_transcript["S_earned"]

    if year_in_hs == 2:
        if LE_attempted == 0:
            output_course = "SLS21"
        elif ES_attempted == 0:
            output_course = "SES21"
        elif Chem_attempted == 0:
            output_course = "SCS21"
        elif Phys_attempted == 0:
            output_course = "SPS21"
        else:
            output_course = "SWS21"
    if year_in_hs == 3:
        if LE_attempted == 0:
            output_course = "SLS21"
        elif ES_attempted == 0:
            output_course = "SES21"
        elif Chem_attempted == 0 and LE_earned >= 2 and ES_earned >= 2:
            output_course = "SCS21"
        elif Phys_attempted == 0 and LE_earned >= 2 and ES_earned >= 2:
            output_course = "SPS21"
        else:
            if life_elective_attempted == 0:
                output_course = "SWS21"
            else:
                if Chem_attempted == 0:
                    output_course = "SCS21"
                elif Phys_attempted == 0:
                    output_course = "SPS21"
                else:
                    output_course = "SDS21"

    if year_in_hs == 4:
        if total_science_earned >= 6:
            output_course = ""
            return [output_course]
        else:
            if LE_attempted == 0:
                output_course = "SLS21"
            elif ES_attempted == 0:
                output_course = "SES21"
            else:
                output_course = "SDS21"

    if student_iep:
        if output_course not in ["SPS21"]:
            if output_course == "SCS21" and student_iep.get("S") == "QM":
                if year_in_hs == 3:
                    output_course = "SWS21"
                if year_in_hs == 4:
                    output_course = "SDS21"
                output_course = output_course + student_iep.get("S")
            else:
                output_course = output_course + student_iep.get("S")
        else:
            if year_in_hs == 3:
                output_course = "SWS21"
            if year_in_hs == 4:
                output_course = "SDS21"
            output_course = output_course + student_iep.get("S")

    return [output_course]
