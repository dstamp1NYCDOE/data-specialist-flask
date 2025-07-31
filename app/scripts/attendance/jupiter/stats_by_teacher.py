import pandas as pd 
from flask import session

import app.scripts.utils.utils as utils
from app.scripts import files_df

from app.scripts.attendance.jupiter import process as process_jupiter_data

def main():
    attendance_marks_df = process_jupiter_data.main()

    teacher_pvt = pd.pivot_table(attendance_marks_df,index=['Teacher','Pd'], columns='Type', values='StudentID',aggfunc='count').fillna(0)   
    teacher_pvt['late_%'] = teacher_pvt['tardy'] / (teacher_pvt['tardy'] + teacher_pvt['present'])
    teacher_pvt = teacher_pvt.reset_index()

    late_stats_pvt = pd.pivot_table(teacher_pvt, index='Pd',values='late_%', aggfunc=('mean','std'))
    late_stats_pvt = late_stats_pvt.reset_index()

    teacher_pvt = teacher_pvt.merge(late_stats_pvt, on=['Pd'], how='left')

    teacher_pvt['late_%_z_score'] = (teacher_pvt['late_%'] - teacher_pvt['mean']) / teacher_pvt['std']

    return teacher_pvt