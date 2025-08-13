import pandas as pd
import numpy as np

import app.scripts.utils as utils
from app.scripts import files_df

from flask import session

from functools import reduce


def main(cr_1_14_df):

    ## attach numeric equivalent
    cr_1_30_filename = utils.return_most_recent_report(files_df, "1_30")
    cr_1_30_df = utils.return_file_as_df(cr_1_30_filename)
    cr_1_14_df = cr_1_14_df.merge(
        cr_1_30_df[["Mark", "NumericEquivalent","PassFailEquivalent"]], on=["Mark"], how="left"
    )
    cr_1_14_df = cr_1_14_df[cr_1_14_df['Credits']>0]
    cr_1_14_df['passed?'] = cr_1_14_df['PassFailEquivalent'].apply(lambda x: x == 'P')
    
    
    cr_1_14_df['dept'] = cr_1_14_df['Course']\
    .apply(lambda x: x[0])

    cr_1_14_df['curriculum'] = cr_1_14_df['Course']\
    .apply(lambda x: x[0:2])

    cr_1_14_df['credits_earned'] = cr_1_14_df.apply(
        credits_earned, axis=1)

    transcript_earned_by_dept_df = pd.pivot_table(
        cr_1_14_df,
        values='credits_earned',
        index='StudentID',
        columns = ['dept'],
        aggfunc = np.sum,
    ).fillna(0)

    transcript_earned_by_dept_df.columns = [
        x+"_earned" for x in transcript_earned_by_dept_df.columns]
    
    transcript_earned_by_curriculum_df = pd.pivot_table(
        cr_1_14_df,
        values='credits_earned',
        index='StudentID',
        columns=['curriculum'],
        aggfunc=np.sum,
    ).fillna(0)

    transcript_earned_by_curriculum_df.columns = [
        x+"_earned" for x in transcript_earned_by_curriculum_df.columns]

    ##

    transcript_attempted_by_dept_df = pd.pivot_table(
        cr_1_14_df,
        values='Credits',
        index='StudentID',
        columns = ['dept'],
        aggfunc = np.sum,
    ).fillna(0)

    transcript_attempted_by_dept_df.columns = [
        x+"_attempted" for x in transcript_attempted_by_dept_df.columns]
    
    transcript_attempted_by_curriculum_df = pd.pivot_table(
        cr_1_14_df,
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
    
    output_df = output_df.reset_index()
    return output_df


def credits_earned(student_row):
    course_passed = student_row['passed?']

    if course_passed:
        return student_row['Credits']
    else:
        return 0

def passed_course(mark):
    return int(mark) >= 65

