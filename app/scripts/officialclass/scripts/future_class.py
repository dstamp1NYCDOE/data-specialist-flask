from flask import session

import pandas as pd
import datetime as dt
from io import BytesIO

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df


def main(data):
    school_year = session["school_year"]
    
    ## Student Current Student Official Classes
    filename = utils.return_most_recent_report(files_df, "ROCL")
    ROCL_df = utils.return_file_as_df(filename, skiprows=3)

    old_officials = ROCL_df['OCL'].unique()

    ## Student Current Official Classes
    filename = utils.return_most_recent_report(files_df, "RACL")
    RACL_df = utils.return_file_as_df(filename, skiprows=2)
    

    promoted_officials = []
    for index, current_official in RACL_df.iterrows():
        promoted_official = return_promoted_official(current_official)
        if promoted_official:
            promoted_officials.append(promoted_official)



    ## generate new officials
    
    cohort_code = data['form']['cohort_code']
    new_officials = generate_incoming_officials(cohort_code)
    
    promoted_officials_df = pd.DataFrame(promoted_officials)
    new_officials_df = pd.DataFrame(new_officials)

    officials_df = pd.concat([promoted_officials_df,new_officials_df])
    
    print(officials_df)
    #keep only new officials
    officials_df = officials_df[~officials_df['OFC'].isin(old_officials)]
    print(officials_df)

    f = BytesIO()
    writer = pd.ExcelWriter(f)
    ROCL_df.to_excel(writer, sheet_name='ROCL', index=False)
    officials_df.to_excel(writer, sheet_name='New Officials', index=False)
    


    current_student_officials_df = ROCL_df[['Student ID','Name','DOB','OCL','GL','Grade']]
    current_student_officials_df = current_student_officials_df.merge(officials_df[['OCL','Grades','Grade Level','OFC']], on=['OCL'], how='left')
    cols = ['Student ID', 'Name', 'DOB', 'OCL', 'GL', 'Grade', 'Grades',
       'Grade Level', 'OFC']
    print(current_student_officials_df.columns)
    current_student_officials_df.to_excel(writer, sheet_name='New Officials Students', index=False)


    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 0)
        worksheet.autofit()

    writer.close()

    f.seek(0)
    # return ''
    return f

import re 

def return_promoted_official(RACL_row):
    current_official = RACL_row['Class Code']
    matches = re.findall(r'\d{1}', current_official)
    if matches:
        if len(matches) == 2:
            first_digit, last_digit = matches
        matches = re.findall(r'[A-Z]{1}', current_official)
        if matches:
            letter = matches[0]
        
            GL_promotion_dict = {
                '9':'0','0':'1','1':'2','2':'2'
            }
            GradeLevel_promotion_dict = {
                '9':'10','0':'11','1':'12','2':'12'
            }
            Grade_promotion_dict = {
                '9':200,'0':210,'1':220,'2':220
            }
            Grade_promotion = Grade_promotion_dict.get(last_digit)
            GL_promotion = GL_promotion_dict.get(last_digit)
            cohort_str = first_digit

            letter_pos = current_official.find(letter)

            if letter_pos == 0:
                new_official = f"{letter}{cohort_str}{GL_promotion}"
                Grade_promotion = 962
            if letter_pos == 1:
                new_official = f"{cohort_str}{letter}{GL_promotion}"
            if letter_pos == 2:
                new_official = f"{cohort_str}{GL_promotion}{letter}"
                Grade_promotion = Grade_promotion+ 9

            temp_dict = {
                'OFC':new_official,
                'OCL':current_official,
                'Bilingual':'N',
                'SAR':'N',
                'Teacher':RACL_row['TEACHER NAME'],
                'Advisor':RACL_row['BAD INFO'],
                'Grades':Grade_promotion,
                'Grade Level':GradeLevel_promotion_dict.get(last_digit),
                'OPT NUMBER':'02533',
                'Room Num':int(RACL_row['Room Num']),
                'CAP CLASS':RACL_row['Cap Class'],
            }
            print(temp_dict)
            return temp_dict

def generate_incoming_officials(cohort_code):
    cohort_year = utils.return_cohort_year(cohort_code)
    cohort_year_str = str(cohort_year)[-1]

    new_officials_lst = []
    for letter in ['A','B','C','D','E','F','G','R','S','T','U','V','W','X']:
        new_officials_lst.append(
            {
                'OFC':f"{cohort_year_str}{letter}9",
                'Grade Level':'09',
                'Grades':'190',
                'OPT NUMBER':'02533',
                'Room Num':'',
                'CAP CLASS':'',
            }
        )
        new_officials_lst.append(
            {
                'OFC':f"{cohort_year_str}9{letter}",
                'Grade Level':'09',
                'Grades':'199',
                'OPT NUMBER':'02533',
                'Room Num':'',
                'CAP CLASS':'T01'
            }
        )
    new_officials_lst.append(
            {
                'OFC':f"P{cohort_year_str}9",
                'Grade Level':'09',
                'Grades':'962',
                'OPT NUMBER':'02533',
                'Room Num':'',
                'CAP CLASS':'E25'
            }
        )
    return new_officials_lst              