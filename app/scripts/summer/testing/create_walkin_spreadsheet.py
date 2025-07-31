import pandas as pd
import numpy as np
import os
from io import BytesIO

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

from flask import current_app, session


def main(form, request):
    school_year = session["school_year"]
    term = session["term"]

    cr_3_07_xlsx = request.files[form.cr_3_07_xlsx.name]
    df_dict = pd.read_excel(cr_3_07_xlsx, sheet_name=None)

    dfs_lst = []
    for sheet_name, df in df_dict.items():
        df["Sending school"] = sheet_name
        dfs_lst.append(df)

    cr_3_07_df = pd.concat(dfs_lst)

    last_year_testing_xlsx = request.files[form.last_year_testing_xlsx.name]
    df_dict = pd.read_excel(last_year_testing_xlsx, sheet_name=None)

    sheets_to_ignore = ["Directions", "HomeLangDropdown", "YABC"]
    dfs_lst = [
        df for sheet_name, df in df_dict.items() if sheet_name not in sheets_to_ignore
    ]
    df = pd.concat(dfs_lst)
    df = df.dropna(subset="StudentID")

    df = df.drop_duplicates(subset="StudentID", keep="last")

    cols = [
        "StudentID",
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
    previous_testing_accommodations_df = df[cols]
    previous_testing_accommodations_df['ENL?'] = previous_testing_accommodations_df['ENL?'].astype(bool)

    

    students_df = cr_3_07_df.merge(
        previous_testing_accommodations_df, on="StudentID", how="left"
    ).fillna({"HomeLang":'ENGLISH',"special_notes":""}).fillna(False)

    path = os.path.join(current_app.root_path, f"data/DOE_High_School_Directory.csv")
    dbn_df = pd.read_csv(path)
    dbn_df["Sending school"] = dbn_df["dbn"]
    dbn_df = dbn_df[["Sending school", "school_name"]]

    students_df = students_df.merge(dbn_df, on="Sending school", how="left").fillna(
        "Other"
    )

    filename = utils.return_most_recent_report(files_df, "4_01")
    cr_4_01_df = utils.return_file_as_df(filename)

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

    

    regents_signups_df = regents_signups_pvt.merge(
        students_df, on="StudentID", how="outer"
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

    all_students_df = regents_signups_df[cols]
    all_students_df[exams_in_order] = all_students_df[exams_in_order].fillna(False)
    all_students_df = all_students_df.sort_values(by=["LastName","FirstName"])

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    for sending_school, students_df in all_students_df.groupby("Sending school"):

        students_df.to_excel(writer, sheet_name=str(sending_school), index=False)

    home_lang_df = pd.DataFrame.from_dict(home_lang_dict, orient="index")

    home_lang_df.to_excel(writer, sheet_name="HomeLangDropdown", index=False)

    # return ""

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 5)
        worksheet.autofit()
        worksheet.data_validation(
            "R2:R2000",
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
