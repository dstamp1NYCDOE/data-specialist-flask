credits_dict = {
    "ACS11TD": 2.0,
    "ACS22T": 2.0,
    "AES11TE": 2.0,
    "AFS11QE": 1.0,
    "AFS61TF": 2.0,
    "AFS63TD": 2.0,
    "AFS65TC": 2.0,
    "ALS21T": 2.0,
    "ALS21TP": 2.0,
    "APS11T": 2.0,
    "AUS11QE": 1.0,
    "AUS11TA": 2.0,
    "BMS11QE": 1.0,
    "BMS63TT": 2.0,
    "BMS65TW": 2.0,
    "BNS11QCA": 1.0,
    "BNS21TV": 2.0,
    "BRS11TF": 2.0,
    "EES83": 1.0,
    "EES83QE": 1.0,
    "EES83QET": 1.0,
    "EES83QM": 1.0,
    "EES83QP": 1.0,
    "EES83QT": 1.0,
    "EES85": 1.0,
    "EES85QE": 1.0,
    "EES85QET": 1.0,
    "EES85QM": 1.0,
    "EES85QP": 1.0,
    "EES85QT": 1.0,
    "EES87": 1.0,
    "EES87QE": 1.0,
    "EES87QET": 1.0,
    "EES87QM": 1.0,
    "EES87QP": 1.0,
    "EES87QT": 1.0,
    "FSS61": 1.0,
    "FSS61Q2": 1.0,
    "GAS85": 0.5,
    "GQS21": 0.5,
    "GQS22": 0.5,
    "HGS43": 1.0,
    "HGS43QM": 1.0,
    "HGS43QP": 1.0,
    "HGS43QT": 1.0,
    "HUS21": 1.0,
    "HUS21QM": 1.0,
    "HUS21QP": 1.0,
    "HUS21QT": 1.0,
    "HVS11": 1.0,
    "HVS11QM": 1.0,
    "HVS11QP": 1.0,
    "HVS11QT": 1.0,
    "MGS21": 1.0,
    "MGS21QM": 1.0,
    "MGS21QT": 1.0,
    "MGS21QP": 1.0,
    "MPS21": 1.0,
    "MPS21QP": 1.0,
    "MPS21QT": 1.0,
    "MPS21QM": 1.0,
    "MRS21": 1.0,
    "MRS21QM": 1.0,
    "MRS21QP": 1.0,
    "MRS21QT": 1.0,
    "MQS11": 1.0,
    "MQS11QM": 1.0,
    "MQS11QP": 1.0,
    "MQS11QT": 1.0,
    "MSS21": 1.0,
    "MSS21QM": 1.0,
    "MSS21QP": 1.0,
    "MSS21QT": 1.0,
    "PHS21": 0.5,
    "PHS22": 0.5,
    "PHS11": 1,
    "PPS83": 0.5,
    "PPS85": 0.5,
    "PPS87": 0.5,
    "SDS21QT": 1.0,
    "SDS21": 1.0,
    "SDS21QM": 1.0,
    "SCS21": 1.0,
    "SCS21QP": 1.0,
    "SCS21QT": 1.0,
    "SES21": 1.0,
    "SES21QM": 1.0,
    "SES21QP": 1.0,
    "SES21QT": 1.0,
    "SJS21": 1.0,
    "SJS21QM": 1.0,
    "SJS21QP": 1.0,
    "SJS21QT": 1.0,    
    "SLS21": 1.0,
    "SLS21QP": 1.0,
    "SLS21QT": 1.0,
    "SBS21": 1.0,
    "SBS21QP": 1.0,
    "SBS21QM": 1.0,
    "SBS21QT": 1.0,    
    "SPS21": 1.0,
    "SWS21": 1.0,
    "SWS21QM": 1.0,
    "SWS21QP": 1.0,
    "SWS21QT": 1.0,
    "TUS21TA": 2.0,
    "TQS21TQW": 2.0,
    'TQS21TQS':2.0,
    'TQS11QE':1.0,
    "ZA": 9.0,
    "ZL": 1.0,
    "ZM18": 1.0,
    "ZM29": 1.0,
    "": 0,
}


def finalize_student_requests(
    student, student_courses, student_transcript, student_iep
):
    year_in_hs = student["year_in_hs"]


    if return_total_credits(student_courses) <= 7:
        student_courses = add_math_and_science(student_courses, student_iep)
        student_courses = list(set(student_courses))
        return student_courses
    elif return_total_credits(student_courses) <= 8:
        student_courses = add_math_or_science(student_courses, student_iep)
        student_courses = list(set(student_courses))
        return student_courses    
    elif return_total_credits(student_courses) in [8.5, 9]:
        student_courses = list(set(student_courses))
        return student_courses        
    if return_total_credits(student_courses) > 9:
        student_courses = drop_science_course(student_courses)
    if return_total_credits(student_courses) > 9:
        student_courses = drop_math_course(student_courses)
    if return_total_credits(student_courses) > 9:
        student_courses = drop_3rd_pd_CTE(student_courses)
    
    student_courses = list(set(student_courses))
    return student_courses


def drop_course(student_courses, course_to_drop):
    output = []
    for course in student_courses:
        if course != course_to_drop:
            output.append(course)

    return output


def return_total_credits(student_courses):
    total_credits = 0
    for course in student_courses:
        total_credits += credits_dict.get(course, 1)

    return total_credits


def drop_3rd_pd_CTE(student_courses):
    output = []
    courses_to_drop = ["AFS11QE", "AUS11QE", "BMS11QE", "BNS11QCA","TQS11QE"]
    for course in student_courses:
        if course not in courses_to_drop:
            output.append(course)

    return output

def add_math_and_science(student_courses, student_iep):

    class_depts = [course[0] for course in student_courses]
    has_math = "M" in class_depts
    has_sci = "S" in class_depts

    sci_course = "SDS21"
    if student_iep:
        sci_course = "SDS21" + student_iep.get("S")
    math_course = "MQS11"
    if student_iep:
        math_course = math_course + student_iep.get("M")

    if not has_math and not has_sci:
        return student_courses + [math_course, sci_course]
    if not has_math and has_sci:
        return student_courses + [math_course]
    if has_math and not has_sci:
        return student_courses + [sci_course]

    return student_courses




def add_math_or_science(student_courses, student_iep):
    class_depts = [course[0] for course in student_courses]
    has_math = "M" in class_depts
    has_sci = "S" in class_depts
    if has_math and not has_sci:
        sci_course = "SDS21"
        if student_iep:
            sci_course = "SDS21" + student_iep.get("S")
        return student_courses + [sci_course]
    if not has_math and has_sci:
        math_course = "MQS11"
        if student_iep:
            math_course = math_course + student_iep.get("M")
        return student_courses + [math_course]
    #generic class to fill space
    sci_course = "SDS21"
    if student_iep:
        sci_course = "SDS21" + student_iep.get("S")
    return student_courses + [sci_course]


def drop_math_course(student_courses):
    output = []
    for course in student_courses:
        if course[0] != "M":
            output.append(course)

    return output


def drop_science_course(student_courses):
    output = []
    for course in student_courses:
        if course[0] != "S":
            output.append(course)

    return output
