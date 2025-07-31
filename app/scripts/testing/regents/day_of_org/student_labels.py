
from app.scripts import scripts, files_df, gsheets_df
from flask import render_template, request, send_file, session, current_app
from io import BytesIO
from reportlab.graphics import shapes
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
import app.scripts.utils.utils as utils
import datetime as dt

import labels

import pandas as pd

PADDING = 0
specs = labels.Specification(
    215.9,
    279.4,
    3,
    10,
    66.6,
    25.2,
    corner_radius=2,
    left_margin=5,
    right_margin=5,
    top_margin=12.25,
    # bottom_margin=13,
    left_padding=PADDING,
    right_padding=PADDING,
    top_padding=PADDING,
    bottom_padding=PADDING,
    row_gap=0,
)


def main(course, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    if term == 1:
        administration = f"January {school_year+1}"
    elif term == 2:
        administration = f"June {school_year+1}"

    gsheet_url = utils.return_gsheet_url_by_title(
        gsheets_df, "regents_exam_book", year_and_semester
    )

    exam_book_df = utils.return_google_sheet_as_dataframe(gsheet_url, sheet="ExamBook")

    cr_1_08_filename = utils.return_most_recent_report_by_semester(
        files_df, "1_08", year_and_semester=year_and_semester
    )
    cr_1_08_df = pd.read_csv(cr_1_08_filename)

    if course != "All":
        cr_1_08_df = cr_1_08_df[cr_1_08_df["Course"] == course]
        download_name = f"{course}_Student_Labels.pdf"
    else:
        download_name = f"All_Student_Labels.pdf"

    if "Rooms" in request.args.keys():
        if request.args.get("Rooms") == "ALL":
            pass
        else:
            room = request.args.get("Rooms")
            cr_1_08_df = cr_1_08_df[cr_1_08_df["Room"] == int(room)]

    if "Sections" in request.args.keys():
        if request.args.get("Sections") == "ALL":
            pass
        else:
            section = request.args.get("Sections")
            cr_1_08_df = cr_1_08_df[cr_1_08_df["Section"] == int(section)]

    cr_1_08_df["ExamAdministration"] = administration
    registered_students_df = cr_1_08_df[cr_1_08_df["Status"]]

    registered_students_df = registered_students_df.merge(
        exam_book_df, left_on=["Course", "Section"], right_on=["Course Code", "Section"]
    )

    labels_to_make = []
    for (day, time, exam_title), students_df in registered_students_df.groupby(
        ["Day", "Time", "ExamTitle"]
    ):

        for room, students_in_room_df in students_df.groupby("Room_y"):
            previous_remainder = len(labels_to_make) % 30
            exam_code = students_in_room_df.iloc[0]["Course"]
            Type = students_in_room_df.iloc[0]["Type"]
            if "scribe" in Type.lower():
                for student in students_in_room_df.to_dict("records"):
                    for i in range(2):
                        labels_to_make.append(student)
                    for i in range(4):
                        labels_to_make.append({})
                for i in range(3):
                    labels_to_make.pop()
            else:
                if exam_code[0] in ["M"]:
                    labels_to_make.extend(students_in_room_df.to_dict("records"))
                elif exam_code[0:4] == "SXRK":
                    labels_to_make.extend(students_in_room_df.to_dict("records"))
                else:
                    for student in students_in_room_df.to_dict("records"):
                        for i in range(2):
                            labels_to_make.append(student)
            next_remainder = len(labels_to_make) % 30

            blanks_to_add = 0
            if next_remainder == 0:
                blanks_to_add += 0
            else:
                if len(labels_to_make) % 3 == 0:
                    blanks_to_add += 0
                elif len(labels_to_make) % 3 == 1:
                    blanks_to_add += 2
                elif len(labels_to_make) % 3 == 2:
                    blanks_to_add += 1
                if (len(labels_to_make) + blanks_to_add) % 30 != 0:
                    blanks_to_add += 3
            for i in range(blanks_to_add):
                labels_to_make.append({})

    sheet = labels.Sheet(specs, draw_label, border=True)
    sheet.add_labels(labels_to_make)

    f = BytesIO()
    sheet.save(f)
    f.seek(0)
    return f, download_name


def draw_label(label, width, height, obj):
    if obj:
        student_name = f"{obj['LastName']}, {obj['FirstName']}"
        course_section = f"{obj['Course']}/{obj['Section']}"

        label.add(
            shapes.String(
                5,
                58,
                f'{obj["ExamAdministration"]} {return_exam_name(obj["Course"])} Regents',
                fontName="Helvetica",
                fontSize=12,
            )
        )
        label.add(
            shapes.String(5, 46, f"School: 02M600", fontName="Helvetica", fontSize=10)
        )
        label.add(
            shapes.String(
                95, 46, f"Course: {course_section}", fontName="Helvetica", fontSize=10
            )
        )

        label.add(shapes.String(5, 30, student_name, fontSize=11))

        label.add(
            shapes.String(
                5, 16, f"ID: {obj['StudentID']}", fontName="Helvetica", fontSize=8
            )
        )
        label.add(
            shapes.String(
                75,
                16,
                f"Off.Class: {obj['OffClass']}",
                fontName="Helvetica",
                fontSize=8,
            )
        )
        label.add(
            shapes.String(
                140, 16, f"Room: {obj['Room_y']}", fontName="Helvetica", fontSize=8
            )
        )

        # label.add(
        #     shapes.String(5, 6, f'DOB: {obj["DOB"]}', fontName="Helvetica", fontSize=8)
        # )
        # label.add(
        #     shapes.String(
        #         95,
        #         6,
        #         f'Home Lang.: {return_language_name(obj["HomeLangCode"])}',
        #         fontName="Helvetica",
        #         fontSize=8,
        #     )
        # )


def return_exam_name(course):
    exam_code = course[0:4]
    exam_dict = {
        "SXRP": "Physics",
        "EXRC": "ELA",
        "SXRK": "LivEnv",
        "HXRC": "Global Hist",
        "HXRK": "USH",
        "MXRC": "Algebra I",
        "MXRF": "Algebra I",
        "SXRX": "Chemistry",
        "SXRU": "Earth Sci",
        "MXRK": "Geometry",
        "MXRN": "AlgII Trig",
        "FXTS": "Spanish",
    }
    return exam_dict.get(exam_code)


def return_language_name(HomeLangCode):
    lang_dict = {
        "English": "English",
        "AC": "ARAUCANIAN",
        "AD": "ADANGME",
        "AE": "AFROASIATIC",
        "AF": "AFRIKAANS",
        "AH": "AMHARIC",
        "AJ": "ACHOLI",
        "AK": "AKAN",
        "AL": "ALBANIAN",
        "AM": "ARMENIAN",
        "AO": "AMOY",
        "AR": "ARABIC",
        "AS": "ASSAMESE",
        "AW": "ARAWAK",
        "AY": "AYMARA",
        "AZ": "AZERBAIJANI",
        "BA": "BALANTE",
        "BB": "BEMBA",
        "BE": "BELORUSSIAN",
        "BG": "BENGALI",
        "BH": "BHILI",
        "BI": "BIHARI",
        "BL": "BALUCHI",
        "BM": "BAMBARA",
        "BO": "BOSNIAN",
        "BQ": "BASQUE",
        "BR": "BRAHUI",
        "BS": "BURMESE",
        "BT": "BRETON",
        "BU": "BULGARIAN",
        "BY": "BALINESE",
        "CA": "CHAM",
        "CB": "CEBUAN",
        "CE": "CHINESE-DIALECT",
        "CH": "CHINESE",
        "CJ": "CHECHEN",
        "CN": "CANTONESE",
        "CS": "CHINESE",
        "CT": "CATALAN",
        "CU": "CHUUKESE",
        "CZ": "CZECH",
        "DA": "DARI/FARSI/PERSIAN",
        "DG": "DAGOMBA",
        "DJ": "DEJULA",
        "DN": "DANISH",
        "DU": "DUTCH",
        "DZ": "DZONGKHA",
        "EO": "ESTONIAN",
        "EW": "EWE",
        "FH": "FRENCH-HAITIAN CREOLE",
        "FJ": "FIJIAN",
        "FK": "FRENCH-KHMER",
        "FL": "FLEMISH",
        "FN": "FINNISH",
        "FO": "FON",
        "FR": "FRENCH",
        "FT": "FANTI",
        "FU": "FULANI",
        "GA": "GA",
        "GC": "GALICIAN",
        "GE": "GEORGIAN",
        "GF": "GARIFUNA",
        "GJ": "GUJARATI",
        "GK": "GREEK",
        "GL": "GALLA",
        "GM": "GURMA",
        "GO": "GREBO",
        "GR": "GERMAN",
        "GU": "GUARANI",
        "HA": "HAITIAN CREOLE",
        "HE": "HEBREW",
        "HG": "HUNGARIAN",
        "HI": "HINDI",
        "HM": "HMONG",
        "HU": "HAUSA",
        "IB": "IBO",
        "IC": "ICELANDIC",
        "IL": "ILOCANO",
        "IN": "INDONESIAN",
        "IR": "IRISH (GAELIC)",
        "IT": "ITALIAN",
        "JA": "JAPANESE",
        "JM": "JAMAICAN-CREOLE",
        "JO": "JOHKHA",
        "KA": "KASHMIRI",
        "KB": "KAMBA",
        "KC": "KACHI",
        "KD": "KANNADA",
        "KE": "KABRE",
        "KF": "KAFIRI",
        "KG": "KANARESE",
        "KH": "KHMER",
        "KI": "KIKUYU",
        "KK": "KRIO",
        "KN": "KANURI",
        "KO": "KOREAN",
        "KP": "KPELLE",
        "KR": "KAREN",
        "KS": "KHOISAN",
        "KU": "KURDISH",
        "KW": "KHOWAN",
        "KY": "KABYLE",
        "KZ": "KAZAKH",
        "LA": "LAO",
        "LG": "LUGANDA",
        "LM": "LOMA",
        "LO": "LUO",
        "LT": "LITHUANIAN",
        "LU": "LUBA",
        "LV": "LATVIAN",
        "LY": "LUNYANKOLE",
        "MA": "MACEDONIAN",
        "MB": "MANDINKA",
        "MD": "MOLDAVIAN",
        "ME": "MENDE",
        "MG": "MALAGASY",
        "MH": "MOHAWK",
        "MI": "MONGOLIAN",
        "MK": "MALINKE",
        "ML": "MALAY",
        "MN": "MANDARIN",
        "MO": "MOSSI",
        "MR": "MARATHI",
        "MT": "MALTESE",
        "MX": "MIXTEC",
        "MY": "MALAYALAM",
        "NA": "NAHUATL",
        "NC": "NIGER-CONGO",
        "ND": "NDEBELE",
        "NE": "NEPALI",
        "NL": "NATIVE AMERICAN LANGUAGES",
        "NO": "ENGLISH",
        "NS": "STUDENT DOES NOT SPEAK",
        "NW": "NORWEGIAN",
        "NY": "NYANJA",
        "ON": "ONEIDA",
        "OR": "ORIYA",
        "OS": "OSSETIAN",
        "PA": "PASHTO",
        "PI": "PILIPINO",
        "PJ": "PUNJABI",
        "PL": "POLISH",
        "PN": "PALAUAN",
        "PO": "PORTUGUESE",
        "PP": "PAPIAMENTO",
        "PR": "PROVENCAL",
        "QC": "QUICHE",
        "QU": "QUECHUA",
        "RA": "RAJASTHANI",
        "RD": "RUNDI",
        "RM": "ROMANSCH",
        "RO": "ROMANIAN",
        "RU": "RUSSIAN",
        "RW": "RWANDA",
        "RY": "RUSSIAN-YIDDISH",
        "SA": "SAMOAN",
        "SB": "SHINA",
        "SC": "SERBO-CROATIAN",
        "SD": "SINDHI",
        "SE": "SENECA",
        "SF": "SINHALESE",
        "SG": "SCOTTISH-GAELIC",
        "SH": "SHAN",
        "SI": "SWAHILI",
        "SJ": "SOMALI",
        "SK": "SUKUMA",
        "SL": "SHLUH",
        "SM": "SIDAMO",
        "SN": "SANSKRIT",
        "SO": "SLOVAK",
        "SP": "SPANISH",
        "SQ": "SONINKE",
        "SR": "SERI",
        "SS": "SETSWANA",
        "ST": "SESOTHO",
        "SU": "SUDANESE",
        "SV": "SLOVENIAN",
        "SW": "SWEDISH",
        "SX": "(AMERICAN) SIGN LANGUAGE",
        "SY": "SOUTH ARABIC",
        "SZ": "SWAZI",
        "TA": "TAMIL",
        "TE": "TELUGU",
        "TG": "TIGRE",
        "TH": "THAI",
        "TI": "TIBETAN",
        "TK": "TURKMAN",
        "TM": "TAMAZIGHT",
        "TO": "TONGA",
        "TR": "TIGRINYA",
        "TT": "TUAREG",
        "TU": "TURKISH",
        "TW": "TWI",
        "TZ": "TADZHIK",
        "UD": "URDU",
        "UK": "UNKNOWN",
        "UR": "UKRAINIAN",
        "UZ": "UZBEK",
        "VC": "VIETNAMESE-CHINESE",
        "VF": "VIETNAMESE-FRENCH",
        "VN": "VIETNAMESE",
        "VS": "VISAYAK",
        "WE": "WELSH",
        "WO": "WOLOF",
        "YI": "YIDDISH",
        "YO": "YONBA",
        "YR": "YORUBA",
        "ZZ": "OTHER",
    }
    return lang_dict.get(HomeLangCode, "").title()
