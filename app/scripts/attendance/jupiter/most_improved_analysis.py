import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import session
from io import BytesIO
import openpyxl

from app.scripts.attendance.jupiter import process as process_jupiter_data


def calculate_weighted_trend(df, value_col, weight_col='week_weight'):
    """Calculate weighted linear regression slope"""
    if len(df) < 2:
        return 0
    
    # Remove any NaN values
    df = df.dropna(subset=[value_col, weight_col])
    if len(df) < 2:
        return 0
    
    x = np.arange(len(df))
    y = df[value_col].values
    w = df[weight_col].values
    
    # Weighted least squares
    sum_w = np.sum(w)
    sum_wx = np.sum(w * x)
    sum_wy = np.sum(w * y)
    sum_wxx = np.sum(w * x * x)
    sum_wxy = np.sum(w * x * y)
    
    denominator = (sum_w * sum_wxx - sum_wx * sum_wx)
    if denominator == 0:
        return 0
    
    slope = (sum_w * sum_wxy - sum_wx * sum_wy) / denominator
    return slope


def main(award_month_str):
    """
    Main function to calculate most improved attendance awards
    
    Args:
        award_month_str: String in format 'YYYY-MM' (e.g., '2024-11')
    
    Returns:
        BytesIO object containing Excel file, download filename
    """
    
    # Parse award month
    award_date = datetime.strptime(award_month_str, '%Y-%m')
    award_month = award_date.month
    award_year = award_date.year
    
    # Get all attendance data for the semester
    attendance_marks_df = process_jupiter_data.process_local_file()
    
    # Convert Date to datetime if not already
    attendance_marks_df['Date'] = pd.to_datetime(attendance_marks_df['Date'])
    
    # Determine school year start (September)
    if award_month >= 9:
        school_year_start = datetime(award_year, 9, 1)
    else:
        school_year_start = datetime(award_year - 1, 9, 1)
    
    # Filter data from September through end of award month
    end_of_award_month = datetime(award_year, award_month, 1) + timedelta(days=32)
    end_of_award_month = end_of_award_month.replace(day=1) - timedelta(days=1)
    
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df['Date'] >= school_year_start) &
        (attendance_marks_df['Date'] <= end_of_award_month)
    ]
    
    # Add week number (ISO week)
    attendance_marks_df['week_num'] = attendance_marks_df['Date'].dt.isocalendar().week
    attendance_marks_df['year'] = attendance_marks_df['Date'].dt.year
    
    # Create unique week identifier (to handle year transitions)
    attendance_marks_df['week_id'] = (
        attendance_marks_df['Date'] - school_year_start
    ).dt.days // 7
    
    # Identify double-period courses (same StudentID, Course, Teacher on consecutive periods)
    # Sort by StudentID, Course, Teacher, Pd to identify consecutive periods
    attendance_marks_df = attendance_marks_df.sort_values(['StudentID', 'Course', 'Teacher', 'Pd', 'Date'])
    
    # Create a course_group identifier that combines consecutive periods
    def assign_course_group(group):
        """Assign same group ID to consecutive periods of the same course"""
        group = group.sort_values('Pd')
        periods = group['Pd'].unique()
        
        course_group_id = 0
        period_to_group = {}
        
        for i, period in enumerate(periods):
            if i == 0:
                period_to_group[period] = course_group_id
            else:
                # Check if consecutive with previous period
                if period == periods[i-1] + 1:
                    # Same group as previous period
                    period_to_group[period] = period_to_group[periods[i-1]]
                else:
                    # New group
                    course_group_id += 1
                    period_to_group[period] = course_group_id
        
        group['course_group'] = group['Pd'].map(period_to_group)
        return group
    
    attendance_marks_df = attendance_marks_df.groupby(
        ['StudentID', 'Course', 'Teacher']
    ).apply(assign_course_group).reset_index(drop=True)
    
    # Get the first (lowest) period for each course group for output purposes
    period_mapping = attendance_marks_df.groupby(
        ['StudentID', 'Course', 'Teacher', 'course_group']
    )['Pd'].min().reset_index()
    period_mapping = period_mapping.rename(columns={'Pd': 'first_period'})
    
    attendance_marks_df = attendance_marks_df.merge(
        period_mapping,
        on=['StudentID', 'Course', 'Teacher', 'course_group'],
        how='left'
    )
    
    # Calculate weekly attendance rates by student-course-group (combining double periods)
    weekly_stats = attendance_marks_df.groupby(
        ['StudentID', 'LastName', 'FirstName', 'Course', 'Teacher', 'course_group', 'first_period', 'week_id']
    ).agg({
        'Type': lambda x: {
            'present': (x == 'present').sum(),
            'tardy': (x == 'tardy').sum(),
            'excused': (x == 'excused').sum(),
            'unexcused': (x == 'unexcused').sum(),
            'total': len(x)
        }
    }).reset_index().rename(columns={'first_period': 'Pd'})
    
    # Expand the Type dictionary into columns
    weekly_stats['present'] = weekly_stats['Type'].apply(lambda x: x['present'])
    weekly_stats['tardy'] = weekly_stats['Type'].apply(lambda x: x['tardy'])
    weekly_stats['excused'] = weekly_stats['Type'].apply(lambda x: x['excused'])
    weekly_stats['unexcused'] = weekly_stats['Type'].apply(lambda x: x['unexcused'])
    weekly_stats['total'] = weekly_stats['Type'].apply(lambda x: x['total'])
    weekly_stats = weekly_stats.drop('Type', axis=1)
    
    # Calculate rates
    weekly_stats['attendance_rate'] = (
        (weekly_stats['present'] + weekly_stats['tardy']) / weekly_stats['total']
    )
    weekly_stats['punctuality_rate'] = np.where(
        (weekly_stats['present'] + weekly_stats['tardy']) > 0,
        weekly_stats['present'] / (weekly_stats['present'] + weekly_stats['tardy']),
        0
    )
    
    # Calculate 3-week rolling averages
    def rolling_3week(group):
        group = group.sort_values('week_id')
        group['attendance_rate_smooth'] = group['attendance_rate'].rolling(
            window=3, min_periods=1
        ).mean()
        group['punctuality_rate_smooth'] = group['punctuality_rate'].rolling(
            window=3, min_periods=1
        ).mean()
        return group
    print(weekly_stats.columns)
    print(weekly_stats)
    weekly_stats = weekly_stats.groupby(
        ['StudentID', 'Course', 'Teacher', 'Pd']
    ).apply(rolling_3week).reset_index(drop=True)
    
    # Calculate recency weights (70% decay)
    max_week = weekly_stats['week_id'].max()
    weekly_stats['weeks_back'] = max_week - weekly_stats['week_id']
    weekly_stats['week_weight'] = 0.7 ** weekly_stats['weeks_back']
    
    # Calculate baseline (first 4 weeks) and recent (last 3 weeks) periods
    baseline_cutoff = weekly_stats['week_id'].min() + 4
    recent_cutoff = max_week - 2
    
    # Calculate improvement metrics for each student-course-period
    improvement_list = []
    
    for (student_id, last_name, first_name, course, teacher, PD), group in weekly_stats.groupby(
        ['StudentID', 'LastName', 'FirstName', 'Course', 'Teacher', 'Pd']
    ):
        if len(group) < 3:  # Need at least 3 weeks of data
            continue
        
        # Baseline period (first 4 weeks)
        baseline = group[group['week_id'] < baseline_cutoff]
        if len(baseline) == 0:
            continue
        
        baseline_attendance = baseline['attendance_rate_smooth'].mean()
        baseline_punctuality = baseline['punctuality_rate_smooth'].mean()
        
        # Recent period (last 3 weeks)
        recent = group[group['week_id'] >= recent_cutoff]
        if len(recent) == 0:
            continue
        
        recent_attendance = recent['attendance_rate_smooth'].mean()
        recent_punctuality = recent['punctuality_rate_smooth'].mean()
        
        # Calculate weighted trend slopes
        attendance_slope = calculate_weighted_trend(
            group, 'attendance_rate_smooth', 'week_weight'
        )
        punctuality_slope = calculate_weighted_trend(
            group, 'punctuality_rate_smooth', 'week_weight'
        )
        
        # Calculate deltas (recent vs baseline)
        attendance_delta = recent_attendance - baseline_attendance
        punctuality_delta = recent_punctuality - baseline_punctuality
        
        # Combined improvement score (equal weighting)
        # Normalize slopes and deltas to similar scales
        improvement_score = (
            (attendance_slope * 10 + attendance_delta) * 0.5 +
            (punctuality_slope * 10 + punctuality_delta) * 0.5
        )
        
        # Eligibility: must show improvement in BOTH metrics
        # and recent attendance must be reasonable (>= 50%)
        is_eligible = (
            (attendance_delta > 0 and punctuality_delta > 0) and
            recent_attendance >= 0.5 and
            baseline_attendance < 0.95  # Exclude already excellent students
        )
        
        improvement_list.append({
            'StudentID': student_id,
            'LastName': last_name,
            'FirstName': first_name,
            'Course': course,
            'Teacher': teacher,
            'Period': PD,
            'baseline_attendance': baseline_attendance,
            'recent_attendance': recent_attendance,
            'baseline_punctuality': baseline_punctuality,
            'recent_punctuality': recent_punctuality,
            'attendance_delta': attendance_delta,
            'punctuality_delta': punctuality_delta,
            'attendance_slope': attendance_slope,
            'punctuality_slope': punctuality_slope,
            'improvement_score': improvement_score,
            'is_eligible': is_eligible
        })
    
    improvement_df = pd.DataFrame(improvement_list)
    
    if len(improvement_df) == 0:
        # Return empty file if no data
        output = BytesIO()
        pd.DataFrame().to_excel(output, index=False)
        output.seek(0)
        return output, f"Most_Improved_Attendance_Awards_{award_month_str}_NO_DATA.xlsx"
    
    # Filter to eligible students only
    improvement_df = improvement_df[improvement_df['is_eligible']]
    
    if len(improvement_df) == 0:
        output = BytesIO()
        pd.DataFrame().to_excel(output, index=False)
        output.seek(0)
        return output, f"Most_Improved_Attendance_Awards_{award_month_str}_NO_ELIGIBLE.xlsx"
    
    # Rank students within each course section
    improvement_df['rank'] = improvement_df.groupby(
        ['Teacher', 'Course', 'Period']
    )['improvement_score'].rank(ascending=False, method='first')
    
    # Sort by Teacher, Course, Period, then rank
    improvement_df = improvement_df.sort_values(
        ['Teacher', 'Course', 'Period', 'rank']
    )
    
    # Award selection: exactly one winner per course section
    # If top student already won elsewhere, award goes to next best in that section
    awarded_students = set()
    awards_list = []
    
    # Group by section and iterate through each section
    for (teacher, course, period), section_df in improvement_df.groupby(['Teacher', 'Course', 'Period']):
        # Sort by rank to get students in order of improvement
        section_df = section_df.sort_values('rank')
        
        # Find the first student who hasn't already won an award
        awarded_in_section = False
        for _, row in section_df.iterrows():
            student_id = row['StudentID']
            
            if student_id not in awarded_students:
                # This student gets the award for this section
                awards_list.append({
                    'StudentID': row['StudentID'],
                    'LastName': row['LastName'],
                    'FirstName': row['FirstName'],
                    'CourseCode': row['Course'],
                    'TeacherName': row['Teacher'],
                    'Period': row['Period'],
                    'AttendanceImprovement': f"{row['attendance_delta']:.1%}",
                    'PunctualityImprovement': f"{row['punctuality_delta']:.1%}",
                    'ImprovementScore': f"{row['improvement_score']:.3f}"
                })
                awarded_students.add(student_id)
                awarded_in_section = True
                break
        
        # If no eligible students in this section (shouldn't happen with our logic, but just in case)
        if not awarded_in_section and len(section_df) > 0:
            # Award to rank 1 student anyway (their first occurrence wins)
            row = section_df.iloc[0]
            awards_list.append({
                'StudentID': row['StudentID'],
                'LastName': row['LastName'],
                'FirstName': row['FirstName'],
                'CourseCode': row['Course'],
                'TeacherName': row['Teacher'],
                'Period': row['Period'],
                'AttendanceImprovement': f"{row['attendance_delta']:.1%}",
                'PunctualityImprovement': f"{row['punctuality_delta']:.1%}",
                'ImprovementScore': f"{row['improvement_score']:.3f}"
            })
            awarded_students.add(row['StudentID'])
    
    awards_df = pd.DataFrame(awards_list)
    
    # Sort final output for mail merge
    awards_df = awards_df.sort_values(['TeacherName', 'CourseCode', 'Period'])
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        awards_df.to_excel(writer, sheet_name='Awards', index=False)
        
        # Optional: Add a summary sheet with improvement details
        improvement_df_export = improvement_df[
            improvement_df['StudentID'].isin(awarded_students)
        ].sort_values(['Teacher', 'Course', 'Period'])
        
        improvement_df_export.to_excel(
            writer, sheet_name='Detailed Analysis', index=False
        )
    
    output.seek(0)
    download_name = f"Most_Improved_Attendance_Awards_{award_month_str}.xlsx"
    
    return output, download_name