
import numpy as np
import pandas as pd
import datetime as dt

import app.scripts.utils as utils
from app.scripts import scripts, files_df

def main():
    
    filename = utils.return_most_recent_report(files_df, "TestingAccommodations")
    df = utils.return_file_as_df(filename,skiprows=1)
    
    cols = [
        'Student_ID',
        'Last_Name',
        'First_Name',
        'Date_of_Meeting','Document_Type',
        'Testing_Accommodation',
        'Condition',
        'Implementation_Recommendation'
        ]
    df = df[cols]
    df = df.rename(columns={
        "Student_ID": "StudentID",
        "Last_Name": "LastName",
        "First_Name": "FirstName",
        }
        )

    student_list = df['StudentID'].unique()
    df['Implementation_Recommendation'] = df['Implementation_Recommendation'].apply(lambda x: x.lower())
    df['Testing_Accommodation'] = df['Testing_Accommodation'].apply(lambda x: x.lower())

    testing_conditions = [
    {'testing_condition':'time_and_a_half?',
        'text_matches':[
        'Time and a Half',
        'Time & Half',
        'time and a half',
        'time and one half',
        '1.5x',
        'x1.5',
        'time and half',
        'time and a haalf',
        'time-and-a-half',
        'time and a a half',
        '1.5 time',
        '1 1/2',
        '1.5',
        'time +1/2',
        ]},
    {'testing_condition': 'double_time?', 'text_matches': [
            'Time extended to double time', 
            'Double Time',
            'Double',
            '2 x',
            '2x',
            'x2',
            ]},
        {'testing_condition': 'read_aloud?', 'text_matches': [
            'multiple-choice responses read aloud', 
            'multiple-choice responses read', 
            'multiple choice responses read', 
            'test read and re-read', 
            'test read aloud',
            'questions read and reread', 
            'test will be read', 
            'test read two times',
            'passages, questions, and multiple choice answers will be read and repeated one time',
            'questions, multiple choice items and passages should be read aloud',
            'passage, questions, items and multiple choice items and multiple choice responses are read aloud',
            'passages, questions, and multiple choice answers will be read and repeated one time',
            'measuring reading comprehension on all assessments not testing reading comprehension',
            'directions, questions, multiple choice responses, and test passages, excluding those measuring comprehension, should be read to',
            'directions, questions, multiple choice responses, and test passages, excluding those measuring reading comprehension, should be read to',
            'on all tests, the directions, questions, multiple choice responses, and test passages, excluding those measuring comprehension, should be read to the student',]},
    {'testing_condition':'scribe?','text_matches':['will write down student responses','scribe']},
    {'testing_condition':'one_on_one?','text_matches':['one on one']},
    {'testing_condition':'Technology?','text_matches':['laptop']},
    {'testing_condition': 'large_print?', 
    'text_matches': ['Large print']},
    ]

    output = []
    for student in student_list:
        dff = df[df['StudentID']==student]

        date_of_meeting = dff.to_dict('records')[0]['Date_of_Meeting']
        date_of_meeting = pd.to_datetime(date_of_meeting)
        todays_date = dt.datetime.now()

        document_type = dff.to_dict('records')[0]['Document_Type']

        if document_type == 'Declassification':
            if date_of_meeting.replace(year = date_of_meeting.year + 1) >= todays_date:
                is_declassified = False 
            else:    
                is_declassified = True 
        else:
            is_declassified = False
        

        temp_dict = {
            'StudentID':student,
            'LastName':dff.to_dict('records')[0]['LastName'],
            'FirstName':dff.to_dict('records')[0]['FirstName'],
            'Grouping':'HSFI',
            'Date_of_Meeting': dff.to_dict('records')[0]['Date_of_Meeting'],
            'Document_Type': document_type,
            'Declassified?': is_declassified,
        }

        all_accomodations_text = '; '.join(dff['Implementation_Recommendation'].to_list())

        for type in ['extended time','test read','use of scribe']:
            type_text = '; '.join(
                dff[dff['Testing_Accommodation']==type]['Implementation_Recommendation'].to_list())
            temp_dict[type] = type_text
        temp_dict['Implementation_Recommendation'] = all_accomodations_text

        for testing_condition_dict in testing_conditions:
            testing_condition = testing_condition_dict['testing_condition']
            text_matches = testing_condition_dict['text_matches']
            temp_dict[testing_condition] = check_text_match(dff, text_matches)

        
        output.append(temp_dict)

    output_df = pd.DataFrame(output)
    return output_df
    filename = f"TestingAccomodations.xlsx"
    output_df.to_excel(filename,sheet_name='parsed',index=False)


def check_text_match(dff, text_matches):
    for text_match in text_matches:
        if dff['Implementation_Recommendation'].str.contains(text_match.lower()).any():
            return True
    return False

if __name__ == "__main__":
    main()
