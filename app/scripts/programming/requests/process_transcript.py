import pandas as pd
import numpy as np

from app.scripts.programming.requests.marks import marks_dict

def main(transcript_raw_df):
    
    transcript_raw_df = transcript_raw_df[transcript_raw_df['Credits']>0]
    transcript_raw_df['passed?'] = transcript_raw_df['PassFailEquivalent'].apply(lambda x: x == 'P')
    
    
    transcript_raw_df['dept'] = transcript_raw_df['Course']\
    .apply(lambda x: x[0])

    transcript_raw_df['curriculum'] = transcript_raw_df['Course']\
    .apply(lambda x: x[0:2])

    transcript_raw_df['credits_earned'] = transcript_raw_df.apply(
        credits_earned, axis=1)

    transcript_earned_by_dept_df = pd.pivot_table(
        transcript_raw_df,
        values='credits_earned',
        index='StudentID',
        columns = ['dept'],
        aggfunc = np.sum,
    ).fillna(0)

    transcript_earned_by_dept_df.columns = [
        x+"_earned" for x in transcript_earned_by_dept_df.columns]
    
    transcript_earned_by_curriculum_df = pd.pivot_table(
        transcript_raw_df,
        values='credits_earned',
        index='StudentID',
        columns=['curriculum'],
        aggfunc=np.sum,
    ).fillna(0)

    transcript_earned_by_curriculum_df.columns = [
        x+"_earned" for x in transcript_earned_by_curriculum_df.columns]

    ##

    transcript_attempted_by_dept_df = pd.pivot_table(
        transcript_raw_df,
        values='Credits',
        index='StudentID',
        columns = ['dept'],
        aggfunc = np.sum,
    ).fillna(0)

    transcript_attempted_by_dept_df.columns = [
        x+"_attempted" for x in transcript_attempted_by_dept_df.columns]
    
    transcript_attempted_by_curriculum_df = pd.pivot_table(
        transcript_raw_df,
        values='Credits',
        index='StudentID',
        columns=['curriculum'],
        aggfunc=np.sum,
    ).fillna(0)

    transcript_attempted_by_curriculum_df.columns = [
        x+"_attempted" for x in transcript_attempted_by_curriculum_df.columns]
    
    output_df = transcript_earned_by_curriculum_df.merge(
        transcript_earned_by_dept_df, how='left', on='StudentID'
        )
    output_df = output_df.merge(
        transcript_attempted_by_dept_df, how='left', on='StudentID'
    )
    output_df = output_df.merge(
        transcript_attempted_by_curriculum_df, how='left', on='StudentID'
    )
    

    return output_df


def credits_earned(student_row):
    course_passed = student_row['passed?']

    if course_passed:
        return student_row['Credits']
    else:
        return 0

def passed_course(mark):
    return int(mark) >= 65


if __name__ == '__main__':
    transcript_raw_df = pd.read_excel('data/1_14.xlsx')
    main(transcript_raw_df)
