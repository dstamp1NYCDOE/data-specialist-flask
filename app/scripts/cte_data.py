from collections import Counter

CTE_MAJOR_DISPLAY_NAMES = {
    "FD": "Fashion Design",
    "VP": "Visual Presentation",
    "FMM": "Fashion Marketing & Management",
    "SD": "Software Development",
    "Photo": "Photography",
    "AnD": "Art and Design",
}

# major -> year_in_hs (2=10th, 3=11th, 4=12th) -> term (1=Fall, 2=Spring) -> [valid course codes]
#
# Filled in from real course-code frequency counts against CR_1_14 (2022+ data).
# FD / VP / AnD / Photo slots are high-confidence (one dominant code, or a documented
# parity/cohort split). FMM and SD slots are LOW CONFIDENCE -- multiple inconsistent
# codes show up in real data for the same slot and need review/correction.
CTE_SEQUENCE = {
    "FD": {
        2: {1: ["AFS61TF", "AFS83T"], 2: ["AFS62TF", "AFS84T"]},
        3: {
            1: ["AFS63TD", "AFS63TDA", "AFS63TDB", "AFS63TDC"],
            2: ["AFS64TD", "AFS64TDA", "AFS64TDB", "AFS64TDC"],
        },
        4: {1: ["AFS65TC", "AFS65TCT", "AFS65TCH"], 2: []},
    },
    "VP": {
        2: {1: ["BMS61TV"], 2: ["BMS62TD"]},
        3: {1: ["BMS63TT"], 2: ["BMS64TP"]},
        4: {1: ["BMS65TW"], 2: []},
    },
    "FMM": {  # LOW CONFIDENCE -- please confirm
        2: {1: ["TUS21TA", "BQS11T"], 2: ["TUS21TA", "BQS11T"]},
        3: {1: ["BRS11TF", "BKS11TE"], 2: ["BRS11TF", "BKS11TE"]},
        4: {1: ["BNS21TV"], 2: []},
    },
    "SD": {  # LOW CONFIDENCE -- please confirm
        2: {1: ["SKS21X"], 2: ["SKS22X"]},
        3: {1: ["TQS21TQW"], 2: ["TQS22TQW"]},
        4: {1: ["TQS21TQS"], 2: []},
    },
    "Photo": {
        2: {1: ["ACS21T"], 2: ["ACS21TD"]},
        3: {1: ["ACS22T"], 2: ["ACS22TD"]},
        4: {1: ["ALS21TP"], 2: []},
    },
    "AnD": {
        2: {1: ["AUS11TA", "APS11T"], 2: ["AUS11TA", "APS11T"]},
        3: {1: ["ACS11TD", "AES11TE"], 2: ["ACS11TD", "AES11TE"]},
        4: {1: ["ALS21T"], 2: []},
    },
}

# Legacy/companion course codes carried over from the pre-unification process_majors.py
# dict that don't have a reliable per-term slot from real data. Kept here (rather than
# dropped) so the major lookup doesn't regress for students on these codes; folded into
# CTE_COURSE_TO_MAJOR below but intentionally excluded from CTE_SEQUENCE.
LEGACY_COURSE_TO_MAJOR = {
    "ANS11": "AnD",
    "AGS11": "AnD",
    "ALS22": "AnD",
    "ALS22QP": "Photo",
    "AYS11": "FMM",
    "ABS11": "FMM",
    "BNS22QV": "FMM",
    "BQS11QQI": "FMM",
    "AWS11": "FD",
    "AUS11": "FD",
    "AFS66QC": "FD",
    "AFS66QCH": "FD",
    "BMS66QW": "VP",
}

CTE_COURSE_TO_MAJOR = {
    course: major
    for major, years in CTE_SEQUENCE.items()
    for year in years.values()
    for term in year.values()
    for course in term
}
CTE_COURSE_TO_MAJOR.update(LEGACY_COURSE_TO_MAJOR)


def is_cte_course(course):
    """Broad check for whether a course code is CTE-coded at all (used for the
    NYSED 10-credit CTE total, as opposed to identifying a specific major)."""
    if len(course) <= 5:
        return False
    if course in ["SKS21X", "SKS22X"]:
        return True
    return course[5] == "T"


def major_for_courses(course_list):
    """Given all the course codes a student has ever taken, return their most
    frequently matched CTE major, or None if no CTE major course is found."""
    matches = [CTE_COURSE_TO_MAJOR[course] for course in course_list if course in CTE_COURSE_TO_MAJOR]
    if not matches:
        return None
    return Counter(matches).most_common(1)[0][0]
