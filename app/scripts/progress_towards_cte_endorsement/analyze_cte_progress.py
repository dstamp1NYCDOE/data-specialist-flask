from collections import Counter

import pandas as pd
from io import BytesIO

from flask import session

import app.scripts.utils as utils
import app.scripts.cte_data as cte_data
from app.scripts import scripts, files_df

TERM_ORDER = {1: 1, 2: 2, 3: 3, 4: 4, 7: 5}

# (column label, year_in_hs, term) -- 2=10th, 3=11th, 4=12th; 1=Fall, 2=Spring
SEMESTER_SLOTS = [
    ("10th-Fall", 2, 1),
    ("10th-Spring", 2, 2),
    ("11th-Fall", 3, 1),
    ("11th-Spring", 3, 2),
    ("12th-Fall", 4, 1),
]


def main(data):
    df = process()
    return return_spreadsheet(df)


def return_spreadsheet(df):
    f = BytesIO()
    writer = pd.ExcelWriter(f)
    df.to_excel(writer, sheet_name="CTE Progress", index=False)
    for worksheet in writer.sheets.values():
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()
    writer.close()
    f.seek(0)
    return f


def status_for_course_set(sub_df, course_set):
    matches = sub_df[sub_df["Course"].isin(course_set)]
    if matches.empty:
        return ""
    if (matches["Mark"] == "P").any():
        return "Passed"
    return "Not Passed"


def infer_anchor_year(sub_df, major):
    """Infer the school year in which this student was in 10th grade (year_in_hs=2)
    for their major, purely from their own transcript -- NOT from Cohort/GEC.
    GEC reflects a student's originally-assigned cohort and doesn't get corrected
    when a student is held back, so a retained student's actual course-taking can
    drift a year or more from what their GEC implies. Anchoring on when they
    actually took their own major's courses is robust to that drift.
    """
    if sub_df is None or not major:
        return None
    # Count each course code's EARLIEST year only, once -- a retake shouldn't get
    # extra votes just because the student attempted the same course multiple
    # times, which could otherwise let enough retakes outvote the true original
    # year (e.g. two retake attempts landing in the same later year).
    first_year_per_course = sub_df.groupby("Course")["Year"].min()
    implied_anchors = []
    for candidate_year_in_hs, terms in cte_data.CTE_SEQUENCE.get(major, {}).items():
        codes = set(terms.get(1, [])) | set(terms.get(2, []))
        for course in codes:
            if course in first_year_per_course.index:
                implied_anchors.append(
                    first_year_per_course[course] - (candidate_year_in_hs - 2)
                )
    if not implied_anchors:
        return None
    return Counter(implied_anchors).most_common(1)[0][0]


def process():
    school_year = session["school_year"]
    term = session["term"]

    cr_1_14_filename = utils.return_most_recent_report(files_df, "1_14")
    cr_1_14_df = utils.return_file_as_df(cr_1_14_filename)
    cr_1_14_df["Course"] = cr_1_14_df["Course"].fillna("").astype(str)

    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent", "PassFailEquivalent"]],
        on="Mark",
        how="left",
    )
    # Trust CR_1_30's own PassFailEquivalent rather than re-deriving a numeric
    # threshold: marks like "P"/"CR"/"WA" have no NumericEquivalent at all, and
    # "PL"/"PR" (Local/Regents Pass) carry NumericEquivalent=64 despite being a
    # pass -- a plain ">= 65" check gets both of those wrong.
    cr_1_14_df["earned_credit?"] = cr_1_14_df["PassFailEquivalent"] == "P"
    cr_1_14_df["is_CTE?"] = cr_1_14_df["Course"].apply(cte_data.is_cte_course)

    cte_credit_value = pd.Series(0.0, index=cr_1_14_df.index)
    cte_mask = cr_1_14_df["is_CTE?"] & cr_1_14_df["earned_credit?"]
    cte_credit_value[cte_mask] = cr_1_14_df.loc[cte_mask, "Credits"]
    cr_1_14_df["cte_credit_value"] = cte_credit_value

    cr_1_14_df["_sort_key"] = cr_1_14_df["Year"] * 10 + cr_1_14_df["Term"].map(
        TERM_ORDER
    ).fillna(9)

    cr_3_07_filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    roster_df = (
        cr_3_07_df[["StudentID", "LastName", "FirstName", "GEC"]]
        .drop_duplicates(subset="StudentID")
        .copy()
    )
    roster_df["Cohort"] = roster_df["GEC"].apply(utils.return_cohort_year)

    cr_1_49_filename = utils.return_most_recent_report(files_df, "1_49")
    cr_1_49_df = utils.return_file_as_df(cr_1_49_filename)
    counselor_df = cr_1_49_df[["StudentID", "Counselor"]].drop_duplicates(
        subset="StudentID"
    )
    roster_df = roster_df.merge(counselor_df, on="StudentID", how="left")

    transcript_by_student = {}
    courses_by_student = {}
    for student_id, group in cr_1_14_df.groupby("StudentID"):
        sub_df = group.sort_values("_sort_key").reset_index(drop=True)
        sub_df["cum_cte_credits"] = sub_df["cte_credit_value"].cumsum()
        transcript_by_student[student_id] = sub_df
        courses_by_student[student_id] = sub_df["Course"].tolist()

    rows = []
    for _, student in roster_df.iterrows():
        student_id = student["StudentID"]
        sub_df = transcript_by_student.get(student_id)
        courses = courses_by_student.get(student_id, [])
        major = cte_data.major_for_courses(courses)

        result = {
            "StudentID": student_id,
            "LastName": student["LastName"],
            "FirstName": student["FirstName"],
            "Cohort": student["Cohort"],
            "Counselor": student.get("Counselor"),
            "Major": major or "",
        }

        anchor_year = infer_anchor_year(sub_df, major)
        on_track = True
        any_past_slot = False

        for label, year_in_hs, slot_term in SEMESTER_SLOTS:
            cell = ""
            if major and sub_df is not None and anchor_year is not None:
                target_year = anchor_year + (year_in_hs - 2)
                expected_courses = (
                    cte_data.CTE_SEQUENCE.get(major, {}).get(year_in_hs, {}).get(slot_term, [])
                )
                # Strictly less-than on term: the CURRENT term is still in progress and
                # its grades aren't final yet, so don't judge it as "Not Taken"/off-track
                # just because the session has moved into that term -- only terms that
                # have fully concluded (an earlier term, or an earlier school year) count.
                is_past = (target_year < school_year) or (
                    target_year == school_year and slot_term < term
                )
                match = sub_df[
                    (sub_df["Year"] == target_year)
                    & (sub_df["Term"] == slot_term)
                    & (sub_df["Course"].isin(expected_courses))
                ]
                if not match.empty:
                    # A term slot can have more than one required course actually land in
                    # it (e.g. a major with two flexibly-ordered courses per year, both
                    # taken the same term) -- combine all matches rather than dropping any.
                    cell_parts = []
                    for _, matched_row in match.iterrows():
                        cum = matched_row["cum_cte_credits"]
                        cell_parts.append(
                            f"{matched_row['Course']} – {matched_row['Mark']} ({cum:g} cr)"
                        )
                        if is_past:
                            any_past_slot = True
                            if not matched_row["earned_credit?"]:
                                later_pass = sub_df[
                                    (sub_df["Course"] == matched_row["Course"])
                                    & (sub_df["_sort_key"] > matched_row["_sort_key"])
                                    & (sub_df["earned_credit?"])
                                ]
                                if later_pass.empty:
                                    on_track = False
                    cell = "; ".join(cell_parts)
                elif is_past:
                    cell = "Not Taken"
                    any_past_slot = True
                    on_track = False
            result[label] = cell

        if sub_df is not None:
            result["WBLHR"] = status_for_course_set(sub_df, {"WBLHR"})
            result["JXCTE"] = status_for_course_set(sub_df, {"JXCTE", "JXCTE2", "JXCTE3"})
        else:
            result["WBLHR"] = ""
            result["JXCTE"] = ""

        if not major or not any_past_slot:
            result["On Track?"] = ""
        else:
            result["On Track?"] = "Yes" if on_track else "No"

        rows.append(result)

    columns = (
        ["StudentID", "LastName", "FirstName", "Cohort", "Counselor", "Major"]
        + [slot[0] for slot in SEMESTER_SLOTS]
        + ["WBLHR", "JXCTE", "On Track?"]
    )
    return pd.DataFrame(rows, columns=columns)
