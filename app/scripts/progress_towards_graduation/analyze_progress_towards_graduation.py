import pandas as pd
from io import BytesIO

from flask import session

import app.scripts.utils as utils
from app.scripts import scripts, files_df

credit_areas = ['Total Credits earned', 'Core ELA (8)', 'Global Hist. (4)',
       'US Hist. (2)', 'Part. in Govt. (1)', 'Econ. (1)', 'Adv. Math (2)',
       'Other Math (4)', 'Life Science (2)', 'Phy. Science (2)',
       'Life or Phys. Science (2)', 'LOTE (2/6)', 'Arts (2)', 'Health (1)',
       'PE (4)', 'Electives (3/7)',]

def main(data):
    
    df = process_1_68()

    

    return return_spreadsheet(df)

def return_spreadsheet(processed_1_68_df):
    f = BytesIO()
    writer = pd.ExcelWriter(f)

    processed_1_68_df.to_excel(writer,sheet_name='processed', index=False)

    for credit_area in credit_areas:
        cols = ['StudentID', 'LastName', 'FirstName','year_in_hs',
            credit_area,
            f"{credit_area}-Earned",
            f"{credit_area}-Remaining",
            f"{credit_area}-Enrolled",
            f"{credit_area}-On_Track_Needed",
            f"{credit_area}-Deficiency",
            f"{credit_area}-EnrolledToCloseGap",]
        df = processed_1_68_df[processed_1_68_df[f"{credit_area}-EnrolledToCloseGap"]==False]
        df = df[cols].sort_values(by=['year_in_hs',f"{credit_area}-Deficiency"])
        df.to_excel(writer, sheet_name=credit_area.split('(')[0], index=False)

    df = processed_1_68_df[processed_1_68_df['AreasOnTrack'] < 16]
    df = df.sort_values(by=['year_in_hs',"AreasOnTrack"])
    df.to_excel(writer, sheet_name='off_track', index=False)

    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()            
    
    writer.close()
    f.seek(0)    
    return f

def process_1_68():
    filename = utils.return_most_recent_report(files_df, "1_68")
    df = utils.return_file_as_df(filename)        
    school_year = session['school_year']
    term = session['term']

    df = df[df["Grade"]!='ST']
    df["year_in_hs"] = df["Cohort"].apply(utils.return_year_in_hs, args=(school_year,))


    for credit_area in credit_areas:
        df[f"{credit_area}-Earned"] = df[credit_area].apply(return_earned_credits)
        df[f"{credit_area}-Remaining"] = df[credit_area].apply(return_remaining_credits)
        df[f"{credit_area}-Enrolled"] = df[credit_area].apply(return_enrolled_credits)
        df[f"{credit_area}-On_Track_Needed"] = df['year_in_hs'].apply(return_on_track_credits_by_year_in_hs, args=(term, credit_area))
        df[f"{credit_area}-On_Track_Needed_by_end_of_term"] = df['year_in_hs'].apply(return_on_track_credits_by_year_in_hs, args=(term+1, credit_area))
        df[f"{credit_area}-Deficiency"] = df.apply(return_deficiency, args=(credit_area,), axis=1)
        df[f"{credit_area}-EnrolledToCloseGap"] = df[f"{credit_area}-Enrolled"] >= df[f"{credit_area}-Deficiency"]

    df['AreasOnTrack'] = df[[f"{credit_area}-EnrolledToCloseGap" for credit_area in credit_areas]].sum(axis=1)

    df['TotalExcessCreditsDeficient'] = df[[f"{credit_area}-Deficiency" for credit_area in credit_areas if credit_area!='Total Credits earned']].sum(axis=1) - df[[f"{credit_area}-Enrolled" for credit_area in credit_areas if credit_area!='Total Credits earned']].sum(axis=1)
    df['TotalExcessCreditsDeficient'] = df['TotalExcessCreditsDeficient'].apply(lambda x: max(0,x))

    df = df.sort_values(by=['TotalExcessCreditsDeficient'])
    return df

def return_deficiency(student_row,credit_area):
    credits_earned = student_row[f"{credit_area}-Earned"] 
    credits_remaining = student_row[f"{credit_area}-Remaining"] 
    credits_enrolled = student_row[f"{credit_area}-Enrolled"] 
    credits_on_track_needed = student_row[f"{credit_area}-On_Track_Needed"]
    credits_On_Track_Needed_by_end_of_term = student_row[f"{credit_area}-On_Track_Needed_by_end_of_term"]

    current_credit_gap = credits_On_Track_Needed_by_end_of_term - credits_earned
    return max(current_credit_gap,0)

def return_on_track_credits_by_year_in_hs(year_in_hs, term, credit_area):
    if credit_area == 'Total Credits earned':
        credit_dict = {1:44,2:44,3:44}
        if year_in_hs == 4:
            credit_dict = {1:33,2:38.5,3:44}
        if year_in_hs == 3:
            credit_dict = {1:22,2:27.5,3:33}    
        if year_in_hs == 2:
            credit_dict = {1:11,2:16.5,3:22} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:5.5,3:11} 
    if credit_area == 'Core ELA (8)':
        credit_dict = {1:8,2:8,3:8}
        if year_in_hs == 4:
            credit_dict = {1:6,2:7,3:8}
        if year_in_hs == 3:
            credit_dict = {1:4,2:5,3:6}    
        if year_in_hs == 2:
            credit_dict = {1:2,2:3,3:4} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:1,3:2} 
    if credit_area == 'Global Hist. (4)':
        credit_dict = {1:4,2:4,3:4}
        if year_in_hs == 4:
            credit_dict = {1:4,2:4,3:4}
        if year_in_hs == 3:
            credit_dict = {1:4,2:4,3:4}    
        if year_in_hs == 2:
            credit_dict = {1:2,2:3,3:4} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:1,3:2} 
    if credit_area == 'US Hist. (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:0,2:1,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0,3:0} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'Part. in Govt. (1)':
        credit_dict = {1:1,2:1,3:1}
        if year_in_hs == 4:
            credit_dict = {1:0,2:1,3:1}
        if year_in_hs == 3:
            credit_dict = {1:0,2:0,3:0}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0,3:0} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'Econ. (1)':
        credit_dict = {1:1,2:1,3:1}
        if year_in_hs == 4:
            credit_dict = {1:0,2:0,3:1}
        if year_in_hs == 3:
            credit_dict = {1:0,2:0,3:0}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0,3:0} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'Adv. Math (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:2,2:2,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:1,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0}   

    if credit_area == 'Other Math (4)':
        credit_dict = {1:4,2:4,3:4}
        if year_in_hs == 4:
            credit_dict = {1:4,2:4,3:4}
        if year_in_hs == 3:
            credit_dict = {1:2,2:3,3:4}    
        if year_in_hs == 2:
            credit_dict = {1:2,2:2,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:1,3:2}   

    if credit_area == 'Life Science (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:2,2:2,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:2,2:2,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:1,3:2}   

    if credit_area == 'Phy. Science (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:2,2:2,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:1,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'Life or Phys. Science (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:0,2:1,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0,3:0} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'LOTE (2/6)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:0,2:1,3:2}
        if year_in_hs == 3:
            credit_dict = {1:0,2:0,3:0}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0,3:0} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'Arts (2)':
        credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 4:
            credit_dict = {1:2,2:2,3:2}
        if year_in_hs == 3:
            credit_dict = {1:2,2:2,3:2}    
        if year_in_hs == 2:
            credit_dict = {1:2,2:2,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:1,3:2} 

    if credit_area == 'Electives (3/7)':
        credit_dict = {1:7,2:7,3:7}
        if year_in_hs == 4:
            credit_dict = {1:5,2:6,3:7}
        if year_in_hs == 3:
            credit_dict = {1:3,2:4,3:5}    
        if year_in_hs == 2:
            credit_dict = {1:1,2:2,3:3} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 

    if credit_area == 'PE (4)':
        credit_dict = {1:4,2:4,3:4}
        if year_in_hs == 4:
            credit_dict = {1:3,2:3.5,3:4}
        if year_in_hs == 3:
            credit_dict = {1:2,2:2.5,3:3}    
        if year_in_hs == 2:
            credit_dict = {1:1,2:1.5,3:2} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0.5,3:1}

    if credit_area == 'Health (1)':
        credit_dict = {1:1,2:1,3:1}
        if year_in_hs == 4:
            credit_dict = {1:1,2:1,3:1}
        if year_in_hs == 3:
            credit_dict = {1:1,2:1,3:1}    
        if year_in_hs == 2:
            credit_dict = {1:0,2:0.5,3:1} 
        if year_in_hs == 1:
            credit_dict = {1:0,2:0,3:0} 



    return credit_dict[term]



def return_earned_credits(credit_str):
    credit_lst = credit_str.split('+')
    for credit in credit_lst:
        if credit[0] == '`':
            return float(credit[1:])
        
def return_enrolled_credits(credit_str):
    credit_lst = credit_str.split('+')
    for credit in credit_lst:
        if credit[0] not in ['`','[']:
            return float(credit)
    
    return 0
    

def return_remaining_credits(credit_str):
    credit_lst = credit_str.split('+')
    for credit in credit_lst:
        if credit[0] == '[':
            return float(credit[1:-1])
    
    return 0

