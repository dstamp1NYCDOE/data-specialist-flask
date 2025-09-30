import pandas as pd
import numpy as np


def main(df):
    cols = [
        'Student ID',
        'Last Name',
        'First Name',
        'Grade',
        'Programs',
        'Related Services',
        'Specialized Transportation (from safest curb location to school)'
    ]
    df = df[cols]
    df = df.rename(columns={
        "Student ID": "StudentID",
        "Last Name": "LastName",
        "First Name": "FirstName",
    }
    )

    output_list = []

    output_dict = {}
    
    for index, student in df.iterrows():
        StudentID = student['StudentID']
        temp_dict = {
            'E' : 'QP',
            'H' : 'QP',
            'S' : 'QP',
            'M' : 'QP',
            'SETSS':False,
            'Counseling':False,
            'Speech':False,
            'OT':False,
            'Transportation':False,
        }
        mandates = str(student['Programs']).split('\n')
        if mandates:
            for mandate in mandates:
                if 'ICT' in mandate:
                    pgrm_rec = 'QT'
                elif 'SETSS' in mandate:
                    pgrm_rec = 'QT'
                    temp_dict['SETSS'] = True
                elif 'Special Class' in mandate:
                    pgrm_rec = 'QM'
                else:
                    pgrm_rec = 'QP'
                
                if 'ELA' in mandate:
                    temp_dict['E'] = pgrm_rec
                elif 'Math' in mandate:
                    temp_dict['M'] = pgrm_rec
                elif 'Science' in mandate:
                    temp_dict['S'] = pgrm_rec
                elif 'Social Studies' in mandate:
                    temp_dict['H'] = pgrm_rec

        related_services = str(student['Related Services']).split('\n')
        
        if related_services:
            for service in related_services:
                if 'Counseling Services' in service:
                    temp_dict['Counseling'] = True                
                elif 'Speech-Language' in service:
                    temp_dict['Speech'] = True

        transportation = str(student['Specialized Transportation (from safest curb location to school)'])
        if transportation == 'Yes':
            temp_dict['Transportation'] = True
        output_dict[StudentID] = temp_dict

    output_df = pd.DataFrame.from_dict(output_dict, orient='index')
    
    return output_dict



if __name__ == '__main__':
    iep_df = pd.read_excel('data/Recommended_Programs.xlsx', skiprows=1)
    main(iep_df)
