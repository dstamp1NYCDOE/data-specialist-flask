"""
Enhanced analysis utilities for counselor and attendance teacher sheets
Provides comprehensive late/cutting/absence analysis across all student classes
"""

import pandas as pd
import numpy as np
from datetime import datetime


def get_late_to_school_detailed(attendance_df, selected_week_dates, student_filter=None):
    """
    Get detailed late-to-school analysis showing:
    - Which period they were finally marked present/tardy
    - Pattern by day of week
    - Semester trend (improving/declining)
    - All semester dates late
    
    Args:
        attendance_df: Full attendance dataframe
        selected_week_dates: List of dates in selected week
        student_filter: Optional dict to filter students (e.g., {'Counselor': 'SMITH J'})
    
    Returns:
        DataFrame with student info, this week pattern, and semester analysis
    """
    # Filter data
    data = attendance_df.copy()
    if student_filter:
        for col, value in student_filter.items():
            data = data[data[col] == value]
    
    # Get all students late to school (ALL SEMESTER for history)
    late_students = data[data['late_to_school?'] == True].copy()
    
    if len(late_students) == 0:
        return pd.DataFrame()
    
    # Calculate semester stats per student
    semester_summary = late_students.groupby([
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor'
    ]).agg({
        'Date': lambda x: list(x),
        'late_to_school?': 'sum',
        'Period': lambda x: list(x)  # Which periods they were marked in
    }).reset_index()
    
    semester_summary = semester_summary.rename(columns={
        'late_to_school?': 'SemesterLateCount'
    })
    
    # Split this week vs prior
    def split_dates_and_periods(row):
        dates = row['Date']
        periods = row['Period']
        
        this_week_data = []
        prior_dates = []
        
        for date, period in zip(dates, periods):
            if date in selected_week_dates:
                this_week_data.append((date, period))
            else:
                prior_dates.append(date)
        
        return this_week_data, prior_dates
    
    semester_summary['ThisWeekData'] = semester_summary.apply(
        lambda row: split_dates_and_periods(row)[0], axis=1
    )
    semester_summary['PriorDates'] = semester_summary.apply(
        lambda row: split_dates_and_periods(row)[1], axis=1
    )
    
    # Filter to only students late THIS WEEK
    semester_summary = semester_summary[
        semester_summary['ThisWeekData'].apply(len) > 0
    ].copy()
    
    if len(semester_summary) == 0:
        return pd.DataFrame()
    
    # Create day-of-week columns (M, T, W, R, F)
    def create_week_pattern(this_week_data):
        """Create dict of {day_letter: period} for this week"""
        pattern = {'M': '', 'T': '', 'W': '', 'R': '', 'F': ''}
        day_map = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F'}
        
        for date, period in this_week_data:
            day_letter = day_map.get(pd.to_datetime(date).weekday())
            if day_letter:
                pattern[day_letter] = str(period)
        
        return pattern
    
    week_patterns = semester_summary['ThisWeekData'].apply(create_week_pattern)
    for day in ['M', 'T', 'W', 'R', 'F']:
        semester_summary[day] = week_patterns.apply(lambda x: x[day])
    
    # This week count
    semester_summary['ThisWeekCount'] = semester_summary['ThisWeekData'].apply(len)
    
    # Calculate trend (are they getting better or worse?)
    # Compare first half of semester vs second half
    def calculate_late_trend(dates):
        if len(dates) < 4:
            return 'Insufficient Data'
        
        dates_sorted = sorted(dates)
        midpoint = len(dates_sorted) // 2
        first_half = dates_sorted[:midpoint]
        second_half = dates_sorted[midpoint:]
        
        # Get date ranges
        first_half_days = (max(first_half) - min(first_half)).days or 1
        second_half_days = (max(second_half) - min(second_half)).days or 1
        
        first_rate = len(first_half) / first_half_days
        second_rate = len(second_half) / second_half_days
        
        if second_rate < first_rate * 0.7:
            return 'Improving'
        elif second_rate > first_rate * 1.3:
            return 'Worsening'
        else:
            return 'Stable'
    
    all_dates = semester_summary['Date']
    semester_summary['Trend'] = all_dates.apply(calculate_late_trend)
    
    # Format prior dates as comma-separated list
    semester_summary['AllSemesterDates'] = semester_summary['Date'].apply(
        lambda x: ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in sorted(x)])
    )
    
    # Calculate severity score for sorting (worse = higher)
    semester_summary['SeverityScore'] = (
        semester_summary['ThisWeekCount'] * 3 +  # Weight recent behavior heavily
        semester_summary['SemesterLateCount'] +
        semester_summary['Trend'].map({'Worsening': 10, 'Stable': 5, 'Improving': 0, 'Insufficient Data': 0})
    )
    
    # Sort by severity (worst first)
    semester_summary = semester_summary.sort_values(
        'SeverityScore', ascending=False
    )
    
    # Select output columns
    output_cols = [
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor',
        'M', 'T', 'W', 'R', 'F',
        'ThisWeekCount', 'SemesterLateCount', 'Trend', 'AllSemesterDates'
    ]
    
    return semester_summary[output_cols].reset_index(drop=True)


def get_cuts_by_period_detailed(attendance_df, selected_week_dates, student_filter=None):
    """
    Get detailed cutting analysis showing:
    - Total cuts this week and semester
    - Breakdown by period with specific dates cut (semester-long)
    - Sorted by severity
    
    Args:
        attendance_df: Full attendance dataframe
        selected_week_dates: List of dates in selected week
        student_filter: Optional dict to filter students
    
    Returns:
        DataFrame with student info and detailed cutting breakdown
    """
    # Filter data
    data = attendance_df.copy()
    if student_filter:
        for col, value in student_filter.items():
            data = data[data[col] == value]
    
    # Get all cuts (ALL SEMESTER)
    cuts_data = data[data['cutting?'] == True].copy()
    
    if len(cuts_data) == 0:
        return pd.DataFrame()
    
    # Group by student to get summary
    student_summary = cuts_data.groupby([
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor'
    ]).agg({
        'Date': lambda x: list(x),
        'cutting?': 'sum',
        'Course': lambda x: list(x),
        'Section': lambda x: list(x),
        'Period': lambda x: list(x)
    }).reset_index()
    
    student_summary = student_summary.rename(columns={
        'cutting?': 'SemesterCuts'
    })
    
    # Separate this week vs prior
    def split_cuts(row):
        dates = row['Date']
        courses = row['Course']
        sections = row['Section']
        periods = row['Period']
        
        this_week = 0
        prior = 0
        
        for date in dates:
            if date in selected_week_dates:
                this_week += 1
            else:
                prior += 1
        
        return this_week, prior
    
    student_summary['ThisWeekCuts'] = student_summary.apply(
        lambda row: split_cuts(row)[0], axis=1
    )
    student_summary['PriorCuts'] = student_summary.apply(
        lambda row: split_cuts(row)[1], axis=1
    )
    
    # Filter to only students with cuts THIS WEEK
    student_summary = student_summary[
        student_summary['ThisWeekCuts'] > 0
    ].copy()
    
    if len(student_summary) == 0:
        return pd.DataFrame()
    
    # Create detailed breakdown by period (semester-long)
    def create_period_breakdown(row):
        """Create detailed string showing cuts by period with dates"""
        dates = row['Date']
        courses = row['Course']
        sections = row['Section']
        periods = row['Period']
        
        # Group by period
        period_cuts = {}
        for date, course, section, period in zip(dates, courses, sections, periods):
            key = f"{course}-{section} (Pd {period})"
            if key not in period_cuts:
                period_cuts[key] = []
            period_cuts[key].append(date)
        
        # Format as string
        breakdown_parts = []
        for class_key, cut_dates in sorted(period_cuts.items()):
            dates_str = ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in sorted(cut_dates)])
            breakdown_parts.append(f"{class_key}: {dates_str} ({len(cut_dates)} cuts)")
        
        return ' | '.join(breakdown_parts)
    
    student_summary['PeriodBreakdown'] = student_summary.apply(
        create_period_breakdown, axis=1
    )
    
    # Calculate severity score (worse = higher)
    student_summary['SeverityScore'] = (
        student_summary['ThisWeekCuts'] * 5 +  # Weight recent heavily
        student_summary['SemesterCuts']
    )
    
    # Sort by severity
    student_summary = student_summary.sort_values(
        'SeverityScore', ascending=False
    )
    
    # Select output columns
    output_cols = [
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor',
        'ThisWeekCuts', 'SemesterCuts', 'PeriodBreakdown'
    ]
    
    return student_summary[output_cols].reset_index(drop=True)


def get_absent_all_week_with_trends(attendance_df, weekly_stats, selected_week_dates, 
                                     selected_week_id, student_filter=None):
    """
    Get students absent all week with semester attendance analysis
    
    Args:
        attendance_df: Full attendance dataframe
        weekly_stats: Weekly aggregated stats with trends
        selected_week_dates: List of dates in selected week
        selected_week_id: The week ID being analyzed
        student_filter: Optional dict to filter students
    
    Returns:
        DataFrame with student info, semester rates, and trend direction
    """
    # Filter data
    data = attendance_df.copy()
    if student_filter:
        for col, value in student_filter.items():
            data = data[data[col] == value]
    
    # Get week data
    week_data = data[data['Date'].isin(selected_week_dates)].copy()
    
    if len(week_data) == 0:
        return pd.DataFrame()
    
    # Count days per student (aggregate across all classes)
    student_days = week_data.groupby('StudentID').agg({
        'in_school?': lambda x: sum(~x),  # Days absent
        'Date': 'nunique'  # Total unique days
    }).reset_index()
    
    student_days = student_days.rename(columns={
        'in_school?': 'DaysAbsent',
        'Date': 'TotalDays'
    })
    
    # Filter to students absent ALL days
    all_absent_ids = student_days[
        student_days['DaysAbsent'] >= student_days['TotalDays']
    ]['StudentID'].tolist()
    
    if len(all_absent_ids) == 0:
        return pd.DataFrame()
    
    # Get student info
    student_info = data[data['StudentID'].isin(all_absent_ids)].groupby([
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor'
    ]).first().reset_index()
    
    # Get semester attendance stats from weekly_stats
    semester_stats = weekly_stats[
        (weekly_stats['StudentID'].isin(all_absent_ids)) &
        (weekly_stats['week_id'] <= selected_week_id)
    ].groupby('StudentID').agg({
        'attendance_rate_smooth': 'mean',
        'attendance_trend': 'mean',
        'unexcused': 'sum',
        'total_periods': 'sum'
    }).reset_index()
    
    semester_stats['SemesterAttendanceRate'] = np.where(
        semester_stats['total_periods'] > 0,
        1 - (semester_stats['unexcused'] / semester_stats['total_periods']),
        0
    )
    
    # Merge with student info
    result = student_info.merge(semester_stats, on='StudentID', how='left')
    
    # Format trend
    def format_trend(trend_value):
        if pd.isna(trend_value):
            return 'Unknown'
        if trend_value > 0.01:
            return 'Improving'
        elif trend_value < -0.01:
            return 'Declining'
        else:
            return 'Stable'
    
    result['TrendDirection'] = result['attendance_trend'].apply(format_trend)
    
    # Calculate severity score (worse = higher)
    result['SeverityScore'] = (
        (1 - result['SemesterAttendanceRate'].fillna(0)) * 100 +  # Weight poor semester rate
        result['TrendDirection'].map({'Declining': 20, 'Stable': 10, 'Improving': 0, 'Unknown': 15})
    )
    
    # Sort by severity
    result = result.sort_values('SeverityScore', ascending=False)
    
    # Select output columns
    output_cols = [
        'StudentID', 'LastName', 'FirstName', 'year_in_hs', 'Counselor',
        'SemesterAttendanceRate', 'attendance_rate_smooth', 'TrendDirection',
        'unexcused'
    ]
    
    # Rename for clarity
    result_output = result[output_cols].copy()
    result_output.columns = [
        'StudentID', 'LastName', 'FirstName', 'Year', 'Counselor',
        'SemesterRate', 'RecentRate', 'Trend', 'TotalAbsences'
    ]
    
    return result_output.reset_index(drop=True)


def get_tier3_students_for_caseload(tier3_df, student_filter):
    """
    Filter Tier 3 students to a specific caseload
    
    Args:
        tier3_df: Full Tier 3 dataframe
        student_filter: Dict to filter (e.g., {'Counselor': 'SMITH J'} or {'AttendanceTeacher': 'DOE J'})
    
    Returns:
        Filtered and formatted DataFrame
    """
    if len(tier3_df) == 0:
        return pd.DataFrame()
    
    result = tier3_df.copy()
    
    # Apply filter
    for col, value in student_filter.items():
        if col in result.columns:
            result = result[result[col] == value]
    
    if len(result) == 0:
        return pd.DataFrame()
    
    # Select relevant columns
    output_cols = [
        'StudentID', 'LastName', 'FirstName', 'year_in_hs',
        'semester_attendance_rate', 'attendance_rate_smooth',
        'attendance_trend', 'cut_count', 'late_count', 'unexcused'
    ]
    
    result_output = result[output_cols].copy()
    result_output.columns = [
        'StudentID', 'LastName', 'FirstName', 'Year',
        'SemesterRate', 'RecentRate', 'Trend', 'Cuts', 'Lates', 'Absences'
    ]
    
    return result_output