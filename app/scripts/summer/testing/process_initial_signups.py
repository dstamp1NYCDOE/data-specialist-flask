import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def main():
    school_year = session["school_year"]
    term = session["term"]

    filename = utils.return_most_recent_report(files_df, "4_01")
    cr_4_01_df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report(files_df, "s_01")
    cr_s_01_df = utils.return_file_as_df(filename)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    cr_s_01_df = cr_s_01_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "NoSendingSchool"
    )

    ## attach other demographics data
    filename = utils.return_most_recent_report(files_df, "3_07")
    cr_3_07_df = utils.return_file_as_df(filename)
    cr_3_07_df["HomeLang"] = cr_3_07_df["HomeLangCode"].apply(
        lambda x: home_lang_dict.get(x, "ENGLISH")
    )
    cr_3_07_df["SWD?"] = cr_3_07_df["IEPFlag"].apply(lambda x: x == "Y")
    cr_3_07_df["ENL?"] = cr_3_07_df["LEPFlag"].apply(lambda x: x == "Y")

    cr_s_01_df = cr_s_01_df.merge(
        cr_3_07_df[["StudentID", "SWD?", "ENL?", "HomeLang"]],
        how="left",
        on="StudentID",
    )

    regents_signups_df = cr_4_01_df[cr_4_01_df["Course"].str[1] == "X"]

    path = os.path.join(current_app.root_path, f"data/RegentsCalendar.xlsx")
    regents_calendar_df = pd.read_excel(path, sheet_name=f"{school_year}-{term}")

    exams_in_order = regents_calendar_df.sort_values(by=["Day", "Time", "ExamTitle"])[
        "ExamTitle"
    ]

    regents_signups_df = regents_signups_df.merge(
        regents_calendar_df[["CourseCode", "ExamTitle"]],
        left_on="Course",
        right_on="CourseCode",
    )

    regents_signups_pvt = pd.pivot_table(
        regents_signups_df,
        index="StudentID",
        columns="ExamTitle",
        values="Section",
        aggfunc="count",
    )

    regents_signups_pvt = regents_signups_pvt >= 0

    regents_signups_pvt = regents_signups_pvt.reset_index()

    ## all students
    s_01_cols = [
        "Sending school",
        "school_name",
        "StudentID",
        "LastName",
        "FirstName",
        "SWD?",
        "ENL?",
        "HomeLang",
    ]
    all_students_df = (
        cr_s_01_df[s_01_cols]
        .merge(regents_signups_pvt, on="StudentID", how="left")
        .fillna(False)
    )

    testing_accommodations_cols = [
        "time_and_a_half?",
        "double_time?",
        "read_aloud?",
        "scribe?",
        "large_print?",
        "special_notes",
    ]
    for testing_accommodations_col in testing_accommodations_cols:
        if testing_accommodations_col == "HomeLang":
            all_students_df[testing_accommodations_col] = ""
        else:
            all_students_df[testing_accommodations_col] = False

    all_students_df = all_students_df.sort_values(
        by=["Sending school", "LastName", "FirstName"]
    )

    cols = (
        [
            "Sending school",
            "school_name",
            "StudentID",
            "LastName",
            "FirstName",
        ]
        + list(exams_in_order)
        + [
            "ENL?",
            "HomeLang",
            "SWD?",
            "time_and_a_half?",
            "double_time?",
            "read_aloud?",
            "scribe?",
            "large_print?",
            "special_notes",
        ]
    )

    all_students_df = all_students_df[cols]

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    for sending_school, students_df in all_students_df.groupby("Sending school"):
        students_df.to_excel(writer, sheet_name=sending_school, index=False)

    home_lang_df = pd.DataFrame.from_dict(home_lang_dict, orient="index")

    home_lang_df.to_excel(writer, sheet_name="HomeLangDropdown", index=False)

    # return ""

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 5)
        worksheet.autofit()
        worksheet.data_validation(
            "Q2:Q501",
            {
                "validate": "list",
                "source": "=HomeLangDropdown!$A$2:$A$209",
            },
        )

    writer.close()
    f.seek(0)

    return f


home_lang_dict = {
    "English": "ENGLISH",
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
