from flask import session
import pandas as pd
from app.scripts.attendance.jupiter import process as jupiter_process

import app.scripts.utils as utils
from app.scripts import files_df

from io import BytesIO

def main(form, request):

    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    daily_jupiter_attd_file = request.files[form.daily_jupiter_attd_file.name]
    daily_jupiter_attd_df = pd.read_csv(daily_jupiter_attd_file)

    daily_jupiter_attd_processed_df = jupiter_process.process_uploaded_file(daily_jupiter_attd_df)
    daily_jupiter_attd_processed_df['Attendance Teacher'] = daily_jupiter_attd_processed_df.apply(return_attendance_teacher, axis=1)
    
    # Determine the day of week from the attendance file
    if 'Date' in daily_jupiter_attd_processed_df.columns and len(daily_jupiter_attd_processed_df) > 0:
        file_date = pd.to_datetime(daily_jupiter_attd_processed_df['Date'].iloc[0])
        date_str = file_date.strftime('%Y-%m-%d')  # Full date
        day_of_week = file_date.strftime('%A')  # Full day name
        day_letter = get_day_letter(day_of_week)
    else:
        day_letter = None  # If we can't determine, show all    
        date_str = None
    
    # Create summary statistics before pivoting
    summary_stats = create_summary_statistics(daily_jupiter_attd_processed_df)
    
    daily_jupiter_attd_pivot_df = pd.pivot_table(
        daily_jupiter_attd_processed_df,
        index=["StudentID", "LastName", "FirstName",'Counselor','Attendance Teacher','in_school?','present_in_period_3'],
        columns=['Pd'],
        values='enhanced_mark',
        aggfunc='first',
    ).fillna('')
    daily_jupiter_attd_pivot_df = daily_jupiter_attd_pivot_df.reset_index()

    jupiter_rosters_df = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades", year_and_semester=year_and_semester)
    jupiter_rosters_df = utils.return_file_as_df(jupiter_rosters_df).drop_duplicates(subset=['StudentID','Course','Section'])
    jupiter_master_schedule_df = utils.return_most_recent_report_by_semester(files_df, "jupiter_master_schedule", year_and_semester=year_and_semester)
    jupiter_master_schedule_df = utils.return_file_as_df(jupiter_master_schedule_df)

    jupiter_rosters_df = jupiter_rosters_df.merge(jupiter_master_schedule_df[['Course','Section','Period']], on=['Course','Section'], how='left').fillna('')

    f = BytesIO()
    writer = pd.ExcelWriter(f, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}})
    workbook = writer.book
    
    # Define formats
    cut_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006",'bold': True, 'border':1})
    absent_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    present_format = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})    
    late_format = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
    late_to_school_format = workbook.add_format({"bg_color": "#CFA500", "font_color": "#FFEB9C",'bold': True, 'border':1})
    excused_format = workbook.add_format({"bg_color": "#2546f0", "font_color": "#FFFFFF"})    
    attd_error = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100",'bold': True, 'border':1})
    thick_border_format = workbook.add_format({'border': 2})
    
    # Write Summary Sheet
    write_summary_sheet(writer, workbook, summary_stats)

    # Track teacher sheets for conditional formatting
    teacher_sheets = []

    ## loop through attendance teachers
    attendance_teachers_list = daily_jupiter_attd_pivot_df["Attendance Teacher"].unique()
    for attendance_teacher in attendance_teachers_list:
        students_df = daily_jupiter_attd_pivot_df[daily_jupiter_attd_pivot_df['Attendance Teacher']==attendance_teacher]    
        students_df = students_df.sort_values(by=['in_school?','LastName','FirstName'])
        students_df.to_excel(writer, index=False, sheet_name=attendance_teacher)

    ## loop through counselors 
    counselors_lst = daily_jupiter_attd_pivot_df["Counselor"].unique()
    for counselor in counselors_lst:
        students_df = daily_jupiter_attd_pivot_df[daily_jupiter_attd_pivot_df['Counselor']==counselor]    
        students_df = students_df.sort_values(by=['in_school?','LastName','FirstName'])
        students_df.to_excel(writer, index=False, sheet_name=counselor)
                
    ## loop through jupiter rosters
    teachers_lst = pd.unique(jupiter_rosters_df[["Teacher1", "Teacher2"]].values.ravel("K"))
    teachers_lst = [teacher for teacher in teachers_lst if teacher != '']
    teachers_lst = sorted(teachers_lst)

    # Store teacher dataframes for border application
    teacher_dataframes = {}
    
    for teacher in teachers_lst:
        students_df = jupiter_rosters_df[(jupiter_rosters_df['Teacher1']==teacher) | (jupiter_rosters_df['Teacher2']==teacher)]    
        students_df = students_df[['StudentID','Period']]
        
        # Filter by day of week if we have day_letter
        if day_letter:
            students_df = filter_by_day_of_week(students_df, day_letter)
        
        # Skip if no students meet on this day
        if len(students_df) == 0:
            continue

        students_with_attd_df = students_df.merge(daily_jupiter_attd_pivot_df, on=['StudentID'], how='left')
        column_to_move = students_with_attd_df.pop('Period')  # Remove 'Period' and store its data
        students_with_attd_df.insert(4, 'Period', column_to_move)
        students_with_attd_df = students_with_attd_df.sort_values(by=['Period'])
        students_with_attd_df.to_excel(writer, index=False, sheet_name=teacher)
        teacher_sheets.append(teacher)
        teacher_dataframes[teacher] = students_with_attd_df

    # Apply formatting to all sheets
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        
        if sheet == 'Summary':
            # Don't apply standard formatting to summary sheet
            continue
            
        worksheet.freeze_panes(1, 3)
        worksheet.autofit()
        
        # Determine end column (adjust based on number of periods)
        end_col_str = 'Z750'  # Extended to row 750
        
        # Apply conditional formatting
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'Possible Attd Err',
                                            'format': attd_error})         
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'potential late to school',
                                            'format': late_to_school_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'potential cut',
                                            'format': cut_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'unexcused',
                                            'format': absent_format})        
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'present',
                                            'format': present_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'tardy',
                                            'format': late_format})
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'text',
                                            'criteria': 'containing',
                                            'value': 'excused',
                                            'format': excused_format})    
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'cell',
                                            'criteria': 'equal to',
                                            'value': 'False',
                                            'format': absent_format})   
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'cell',
                                            'criteria': 'equal to',
                                            'value': 'True',
                                            'format': late_to_school_format})    
        worksheet.conditional_format(f'A1:{end_col_str}', {'type': 'cell',
                                            'criteria': 'equal to',
                                            'value': 'True',
                                            'format': present_format})
        
        # Apply thick borders for teacher sheets only
        if sheet in teacher_sheets:
            apply_period_borders(worksheet, teacher_dataframes[sheet], thick_border_format)
            
    writer.close()
    f.seek(0)

    return f, f"jupiter_midday_{school_year}_{term}_{date_str}.xlsx"


def create_summary_statistics(df):
    """Create summary statistics by year_in_hs"""
    
    # Overall stats
    total_records = len(df)
    unique_students = df['StudentID'].nunique()
    
    # Stats by year_in_hs
    year_stats = df.groupby('year_in_hs').agg({
        'StudentID': 'nunique',
        'cutting?': 'sum',
        'late_to_school?': 'sum',
        'in_school?': lambda x: (~x).sum(),  # Count False values (absences)
    }).reset_index()
    
    year_stats.columns = ['Year in HS', 'Total Students', 'Total Cuts', 'Total Late to School', 'Total Absences']
    
    # Attendance type breakdown by year
    attd_type_stats = pd.pivot_table(
        df,
        index='year_in_hs',
        columns='Type',
        values='StudentID',
        aggfunc='count',
        fill_value=0
    ).reset_index()
    
    # Period 3 presence stats
    p3_stats = df.groupby('year_in_hs').agg({
        'present_in_period_3': 'sum',
        'StudentID': 'count'
    }).reset_index()
    p3_stats['P3 Presence Rate'] = (p3_stats['present_in_period_3'] / p3_stats['StudentID'] * 100).round(2)
    
    return {
        'year_stats': year_stats,
        'attd_type_stats': attd_type_stats,
        'p3_stats': p3_stats,
        'total_records': total_records,
        'unique_students': unique_students
    }


def write_summary_sheet(writer, workbook, summary_stats):
    """Write summary statistics to the first sheet with charts"""
    
    worksheet = workbook.add_worksheet('Summary')
    writer.sheets['Summary'] = worksheet
    
    # Header format
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter'
    })
    
    subheader_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#D9E1F2',
        'align': 'center'
    })
    
    # Write title
    worksheet.write('A1', 'Daily Attendance Summary Report', header_format)
    worksheet.merge_range('A1:F1', 'Daily Attendance Summary Report', header_format)
    
    # Write overall stats
    row = 3
    worksheet.write(row, 0, 'Total Records:', subheader_format)
    worksheet.write(row, 1, summary_stats['total_records'])
    row += 1
    worksheet.write(row, 0, 'Unique Students:', subheader_format)
    worksheet.write(row, 1, summary_stats['unique_students'])
    
    # Write year stats table
    row += 3
    worksheet.write(row, 0, 'Statistics by Year in High School', subheader_format)
    worksheet.merge_range(row, 0, row, 5, 'Statistics by Year in High School', subheader_format)
    row += 1
    
    # Write year stats dataframe
    for col_num, value in enumerate(summary_stats['year_stats'].columns):
        worksheet.write(row, col_num, value, subheader_format)
    row += 1
    
    for idx, data_row in summary_stats['year_stats'].iterrows():
        for col_num, value in enumerate(data_row):
            worksheet.write(row, col_num, value)
        row += 1
    
    # Create chart for cuts, lates, and absences by year
    chart_row = row + 2
    chart1 = workbook.add_chart({'type': 'column'})
    
    data_start_row = 10  # Adjust based on where year_stats table starts
    data_end_row = data_start_row + len(summary_stats['year_stats'])
    
    chart1.add_series({
        'name': 'Total Cuts',
        'categories': ['Summary', data_start_row, 0, data_end_row - 1, 0],
        'values': ['Summary', data_start_row, 2, data_end_row - 1, 2],
    })
    chart1.add_series({
        'name': 'Total Late to School',
        'categories': ['Summary', data_start_row, 0, data_end_row - 1, 0],
        'values': ['Summary', data_start_row, 3, data_end_row - 1, 3],
    })
    chart1.add_series({
        'name': 'Total Absences',
        'categories': ['Summary', data_start_row, 0, data_end_row - 1, 0],
        'values': ['Summary', data_start_row, 4, data_end_row - 1, 4],
    })
    
    chart1.set_title({'name': 'Attendance Issues by Year in HS'})
    chart1.set_x_axis({'name': 'Year in HS'})
    chart1.set_y_axis({'name': 'Count'})
    chart1.set_style(11)
    
    worksheet.insert_chart(chart_row, 0, chart1, {'x_scale': 1.5, 'y_scale': 1.5})
    
    # Write attendance type breakdown
    row = chart_row + 20
    worksheet.write(row, 0, 'Attendance Type Breakdown by Year', subheader_format)
    worksheet.merge_range(row, 0, row, 5, 'Attendance Type Breakdown by Year', subheader_format)
    row += 1
    
    for col_num, value in enumerate(summary_stats['attd_type_stats'].columns):
        worksheet.write(row, col_num, value, subheader_format)
    row += 1
    
    for idx, data_row in summary_stats['attd_type_stats'].iterrows():
        for col_num, value in enumerate(data_row):
            worksheet.write(row, col_num, value)
        row += 1
    
    # Set column widths
    worksheet.set_column('A:F', 20)


def apply_period_borders(worksheet, df, border_format):
    """Apply thick borders to cells corresponding to student periods in teacher sheets"""
    
    # Find the 'Period' column index (should be column 4, which is index 4, column E in Excel)
    # The period attendance columns start after that
    # Assuming structure: StudentID, LastName, FirstName, Counselor, Period, Attendance Teacher, in_school?, present_in_period_3, then period columns
    
    period_col_idx = df.columns.get_loc('Period')
    
    # Find where the numeric period columns start (after present_in_period_3)
    # These are the columns that contain attendance marks by period
    numeric_period_cols = [col for col in df.columns if isinstance(col, (int, float))]
    
    if not numeric_period_cols:
        return
    
    first_period_col_idx = df.columns.get_loc(min(numeric_period_cols))
    
    # Iterate through each row (skip header row 0)
    for row_idx in range(len(df)):
        excel_row = row_idx + 2  # +1 for header, +1 for 0-indexing
        
        period_value = df.iloc[row_idx]['Period']
        
        # Skip if period is empty
        if pd.isna(period_value) or period_value == '':
            continue
        
        # Extract period numbers from the period string
        period_nums = extract_period_numbers(str(period_value))
        
        if not period_nums:
            continue
        
        # Apply border to all relevant period columns
        for period_num in period_nums:
            if period_num in numeric_period_cols:
                period_col_excel_idx = df.columns.get_loc(period_num)
                cell_value = df.iloc[row_idx][period_num]
                
                # Handle NaN values
                if pd.isna(cell_value):
                    cell_value = ''
                
                # Apply thick border to this cell
                worksheet.write(excel_row - 1, period_col_excel_idx, cell_value, border_format)


def extract_period_numbers(period_str):
    """Extract numeric period values from period string
    Examples: '5' -> [5], '8,9' -> [8,9], 'T4' -> [4], 'MWF3' -> [3]
    """
    import re
    
    # Remove day letters (M, T, W, R, F)
    period_str = re.sub(r'[MTWRF]', '', period_str)
    
    # Find all numbers
    numbers = re.findall(r'\d+', period_str)
    
    return [int(num) for num in numbers]


def filter_by_day_of_week(students_df, day_letter):
    """Filter students whose Period matches the day of week
    day_letter: 'M', 'T', 'W', 'R', 'F'
    """
    # If Period doesn't contain a day letter, it meets every day (keep it)
    # If Period contains a day letter, only keep if it matches the current day
    def should_include(period_str):
        if pd.isna(period_str) or period_str == '':
            return True
        
        period_str = str(period_str)
        
        # Check if any day letters are present
        has_day_letters = any(letter in period_str for letter in ['M', 'T', 'W', 'R', 'F'])
        
        if not has_day_letters:
            # No day letters means it meets every day
            return True
        else:
            # Has day letters, check if our day is included
            return day_letter in period_str
    
    return students_df[students_df['Period'].apply(should_include)]


def get_day_letter(day_name):
    """Convert full day name to letter code"""
    day_map = {
        'Monday': 'M',
        'Tuesday': 'T',
        'Wednesday': 'W',
        'Thursday': 'R',  # R for Thursday to avoid confusion with Tuesday
        'Friday': 'F'
    }
    return day_map.get(day_name, None)


def return_attendance_teacher(student_row):
    StudentID = student_row['StudentID']
    year_in_hs = student_row['year_in_hs']
    counselor = student_row['Counselor']

    if year_in_hs == 1:
        return 'AMEH M'
    if year_in_hs == 2:
        return 'CABRERA A'
    if year_in_hs == 3:
        return 'OVALLES P'
    if year_in_hs == 4:
        if counselor == 'WEISS JESSICA':
            return 'OVALLES P'
        if counselor == 'MARIN BETH':
            return 'CABRERA A'
        if counselor == 'SAN JORGE AMELIA':
            if StudentID % 2 == 0:
                return 'CABRERA A'
            else:
                return 'OVALLES P'
    if year_in_hs >= 5:
        return 'AMEH M'