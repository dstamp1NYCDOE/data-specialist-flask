from io import BytesIO
import pandas as pd

from app.scripts.attendance.jupiter.process import main as process_jupiter

def main(form, request):
    day_of = form.day_of.data
    
    student_period_attendance_df = process_jupiter(day_of=day_of) 


    f = BytesIO()
    writer = pd.ExcelWriter(f)


    cuts_df = student_period_attendance_df[student_period_attendance_df['cutting?']]
    cuts_pvt = pd.pivot_table(cuts_df,index=['StudentID','LastName', 'FirstName','Counselor'], columns='Pd',values='Teacher',aggfunc=lambda x: x).fillna('')
    cuts_pvt = cuts_pvt.reset_index()

    num_of_cuts_df = student_period_attendance_df[['StudentID','LastName', 'FirstName','Counselor','num_of_cuts']].drop_duplicates()
    cuts_pvt = num_of_cuts_df.merge(cuts_pvt,on=['StudentID','LastName', 'FirstName','Counselor'],how='right')
    cuts_pvt = cuts_pvt.sort_values(by=['num_of_cuts'], ascending=[False])
    cuts_pvt.to_excel(writer, sheet_name='cuts', index=False)


    attendance_errors_df = student_period_attendance_df[student_period_attendance_df['attd_error']]
    cols = ['Teacher','Course','Section','Pd','Type','LastName','FirstName']
    attendance_errors_df = attendance_errors_df[cols].sort_values(by=['Teacher','Pd','Course','Section'])
    attendance_errors_df.to_excel(writer, sheet_name='attd_errors', index=False)

    writer.close()
    f.seek(0)

    download_name = f'JupiterCutReport-{day_of}.xlsx'    
    return f, download_name