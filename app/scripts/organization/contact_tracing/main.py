import datetime as dt
import pandas as pd  #


from io import BytesIO
from flask import session, current_app
import pandas as pd
import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df

def return_contact_tracing_results(form, request):
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    jupiter_rosters_df = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    jupiter_rosters_df = utils.return_file_as_df(jupiter_rosters_df).drop_duplicates(subset=['StudentID','Course','Section'])


    StudentID = int(form.StudentID.data)

    student_classes = jupiter_rosters_df[jupiter_rosters_df['StudentID'] == StudentID]
    student_classes['Trace'] = True 
    student_classes = student_classes[['Course','Section','Trace']]
    


    df = jupiter_rosters_df.merge(student_classes, on=['Course','Section'], how='right')
    

    pvt_df = pd.pivot_table(df, index='StudentID', values='Section',aggfunc='count').reset_index()
    pvt_df = pvt_df.rename(columns={'Section':'#_of_classes'})
    pvt_df = pvt_df.sort_values(by='#_of_classes', ascending=False)
    

    counselors_df = utils.return_most_recent_report_by_semester(files_df, "1_49", year_and_semester=year_and_semester)
    counselors_df = utils.return_file_as_df(counselors_df)
    counselors_df = counselors_df[['StudentID','LastName','FirstName','Counselor']]
    df = counselors_df.merge(pvt_df, on=['StudentID'], how='right')
    

    Student = df.iloc[0]
    student_initials = Student['FirstName'][0] + Student['LastName'][0]
    f = BytesIO()
    writer = pd.ExcelWriter(f)

    df.to_excel(writer, sheet_name=f"ContactTracingResults", index=False)
    writer.close()
    f.seek(0)
    download_name = f"{student_initials}_{StudentID}_contact_tracing_results.xlsx"
    return f, download_name