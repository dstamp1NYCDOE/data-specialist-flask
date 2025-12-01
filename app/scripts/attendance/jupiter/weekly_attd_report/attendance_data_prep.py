"""
Data preparation utilities for attendance analysis
Handles aggregation, grouping, and data transformations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def parse_period_schedule(pd_str):
    """
    Parse period schedule string to extract meeting days and periods
    
    Examples:
        '1' -> meets period 1 every day (M-F)
        '1,2' -> meets periods 1 and 2 every day (M-F) 
        'M1,W1,F1' -> meets period 1 on Mon, Wed, Fri
        'T1,R1' -> meets period 1 on Tue, Thu
    
    Returns:
        dict: {day: period} mapping, e.g. {'M': 1, 'W': 1, 'F': 1}
    """
    pd_str = str(pd_str).strip()
    
    # Check if it's just numbers (meets every day)
    if pd_str.replace(',', '').isdigit():
        periods = [int(p) for p in pd_str.split(',')]
        # Meets every day M-F
        schedule = {}
        for day in ['M', 'T', 'W', 'R', 'F']:
            for period in periods:
                schedule[f"{day}{period}"] = period
        return schedule
    
    # Parse day-period combinations
    schedule = {}
    parts = pd_str.split(',')
    for part in parts:
        part = part.strip()
        if len(part) >= 2:
            day = part[0]  # First char is day (M, T, W, R, F)
            period = part[1:]  # Rest is period number
            if period.isdigit():
                schedule[part] = int(period)
    
    return schedule


def get_meeting_days(pd_str):
    """
    Get list of days (M, T, W, R, F) when a course meets
    
    Returns:
        list: ['M', 'W', 'F'] or ['T', 'R'] etc.
    """
    schedule = parse_period_schedule(pd_str)
    days = set()
    for key in schedule.keys():
        if key and len(key) >= 1:
            days.add(key[0])
    
    # Return in order M, T, W, R, F
    day_order = ['M', 'T', 'W', 'R', 'F']
    return [d for d in day_order if d in days]


def date_to_day_letter(date):
    """Convert date to day letter (M, T, W, R, F)"""
    day_map = {0: 'M', 1: 'T', 2: 'W', 3: 'R', 4: 'F'}
    return day_map.get(date.weekday(), None)


def should_have_attendance(date, pd_str):
    """
    Check if a course should have attendance on a given date
    
    Args:
        date: datetime object or string
        pd_str: period schedule string
    
    Returns:
        bool: True if course meets on this date
    """
    if isinstance(date, str):
        date = pd.to_datetime(date)
    
    day_letter = date_to_day_letter(date)
    if day_letter is None:
        return False  # Weekend
    
    meeting_days = get_meeting_days(pd_str)
    return day_letter in meeting_days


def calculate_rolling_window(df, value_col, window=3, group_cols=None):
    """
    Calculate rolling window average with proper grouping
    
    Args:
        df: DataFrame with data
        value_col: Column to calculate rolling average for
        window: Window size (default 3 weeks)
        group_cols: Columns to group by before calculating rolling average
    
    Returns:
        Series with rolling averages
    """
    if group_cols:
        def rolling_calc(group):
            group = group.sort_values('week_id')
            return group[value_col].rolling(window=window, min_periods=1).mean()
        
        return df.groupby(group_cols, group_keys=False).apply(rolling_calc)
    else:
        df_sorted = df.sort_values('week_id')
        return df_sorted[value_col].rolling(window=window, min_periods=1).mean()


def calculate_weighted_trend(df, value_col, weight_col='week_weight'):
    """
    Calculate weighted linear regression slope for trend analysis
    More recent weeks weighted more heavily (70% decay per week back)
    
    Returns:
        float: Slope of trend (positive = improving, negative = declining)
    """
    if len(df) < 2:
        return 0
    
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


def aggregate_weekly_attendance(attendance_df):
    """
    Aggregate daily attendance to weekly statistics per student per course
    
    Returns:
        DataFrame with weekly stats including:
        - attendance_rate (present + tardy / total)
        - punctuality_rate (present / (present + tardy))
        - absence_count, cut_count, late_count
    """
    # Add week identifiers - USE ISO WEEK NUMBER
    attendance_df['Date'] = pd.to_datetime(attendance_df['Date'])
    attendance_df['week_id'] = attendance_df['Date'].dt.isocalendar().week
    attendance_df['year'] = attendance_df['Date'].dt.year
    
    # Group by student, course, week
    weekly_stats = attendance_df.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Period',
        'Teacher', 'Counselor', 'year_in_hs', 'week_id'
    ]).agg({
        'Type': lambda x: {
            'present': (x == 'present').sum(),
            'tardy': (x == 'tardy').sum(),
            'excused': (x == 'excused').sum(),
            'unexcused': (x == 'unexcused').sum(),
            'total': len(x)
        },
        'cutting?': 'sum',
        'late_to_school?': 'sum',
        'Date': 'nunique'  # Number of school days this week
    }).reset_index()
    
    # Expand Type dictionary
    weekly_stats['present'] = weekly_stats['Type'].apply(lambda x: x['present'])
    weekly_stats['tardy'] = weekly_stats['Type'].apply(lambda x: x['tardy'])
    weekly_stats['excused'] = weekly_stats['Type'].apply(lambda x: x['excused'])
    weekly_stats['unexcused'] = weekly_stats['Type'].apply(lambda x: x['unexcused'])
    weekly_stats['total_periods'] = weekly_stats['Type'].apply(lambda x: x['total'])
    weekly_stats = weekly_stats.drop('Type', axis=1)
    
    # Calculate rates
    weekly_stats['attendance_rate'] = np.where(
        weekly_stats['total_periods'] > 0,
        (weekly_stats['present'] + weekly_stats['tardy']) / weekly_stats['total_periods'],
        0
    )
    
    weekly_stats['punctuality_rate'] = np.where(
        (weekly_stats['present'] + weekly_stats['tardy']) > 0,
        weekly_stats['present'] / (weekly_stats['present'] + weekly_stats['tardy']),
        0
    )
    
    # Rename columns
    weekly_stats = weekly_stats.rename(columns={
        'cutting?': 'cut_count',
        'late_to_school?': 'late_count',
        'Date': 'school_days'
    })
    
    return weekly_stats


def calculate_semester_trends(weekly_stats):
    """
    Calculate semester-long trends for each student in each course
    Adds rolling averages and weighted trend slopes
    
    Returns:
        DataFrame with added columns:
        - attendance_rate_smooth (3-week rolling avg)
        - punctuality_rate_smooth (3-week rolling avg)
        - attendance_trend (weighted slope)
        - punctuality_trend (weighted slope)
        - week_weight (recency weighting)
    """
    # Sort by student, course, week
    weekly_stats = weekly_stats.sort_values([
        'StudentID', 'Course', 'Section', 'week_id'
    ])
    
    # Calculate 3-week rolling averages
    group_cols = ['StudentID', 'Course', 'Section']
    weekly_stats['attendance_rate_smooth'] = calculate_rolling_window(
        weekly_stats, 'attendance_rate', window=3, group_cols=group_cols
    )
    weekly_stats['punctuality_rate_smooth'] = calculate_rolling_window(
        weekly_stats, 'punctuality_rate', window=3, group_cols=group_cols
    )
    
    # Calculate recency weights (70% decay) - based on most recent week in data
    max_week = weekly_stats['week_id'].max()
    weekly_stats['weeks_back'] = max_week - weekly_stats['week_id']
    weekly_stats['week_weight'] = 0.7 ** weekly_stats['weeks_back']
    
    # Calculate trends for each student-course
    def calc_trends(group):
        if len(group) < 2:
            group['attendance_trend'] = 0
            group['punctuality_trend'] = 0
        else:
            group['attendance_trend'] = calculate_weighted_trend(
                group, 'attendance_rate_smooth', 'week_weight'
            )
            group['punctuality_trend'] = calculate_weighted_trend(
                group, 'punctuality_rate_smooth', 'week_weight'
            )
        return group
    
    weekly_stats = weekly_stats.groupby(group_cols).apply(calc_trends).reset_index(drop=True)
    
    return weekly_stats


def identify_tier3_students(weekly_stats, selected_week_id, top_pct=0.05):
    """
    Identify Tier 3 students needing intervention
    
    Criteria:
    1. Students with negative attendance trends (declining)
    2. Top 5% worst in each year_in_hs cohort
    
    Args:
        weekly_stats: DataFrame with semester trends
        selected_week_id: The week being analyzed
        top_pct: Percentage cutoff (default 5%)
    
    Returns:
        DataFrame of Tier 3 students with summary stats
    """
    # Get most recent data for each student (up to selected week)
    recent_data = weekly_stats[weekly_stats['week_id'] <= selected_week_id].copy()
    
    # Get latest week data per student across all courses
    student_summary = recent_data.groupby(['StudentID', 'LastName', 'FirstName', 'year_in_hs']).agg({
        'attendance_rate_smooth': 'mean',
        'attendance_trend': 'mean',
        'punctuality_rate_smooth': 'mean',
        'punctuality_trend': 'mean',
        'cut_count': 'sum',
        'late_count': 'sum',
        'unexcused': 'sum',
        'total_periods': 'sum',
        'Counselor': 'first',
        'Teacher': lambda x: ', '.join(sorted(set(x)))  # All teachers
    }).reset_index()
    
    # Calculate overall semester attendance rate
    student_summary['semester_attendance_rate'] = np.where(
        student_summary['total_periods'] > 0,
        1 - (student_summary['unexcused'] / student_summary['total_periods']),
        1
    )
    
    # Identify students with negative trends
    student_summary['declining'] = student_summary['attendance_trend'] < -0.01
    
    # Calculate percentile rank within year_in_hs (lower is worse)
    student_summary['attendance_percentile'] = student_summary.groupby('year_in_hs')[
        'semester_attendance_rate'
    ].rank(pct=True)
    
    # Tier 3 criteria: declining OR in bottom 5%
    student_summary['is_tier3'] = (
        student_summary['declining'] | 
        (student_summary['attendance_percentile'] <= top_pct)
    )
    
    tier3_students = student_summary[student_summary['is_tier3']].copy()
    
    # Sort by year, then by trend (most negative first)
    tier3_students = tier3_students.sort_values([
        'year_in_hs', 'attendance_trend', 'semester_attendance_rate'
    ])
    
    return tier3_students


def return_attendance_teacher(student_row):
    """Assign attendance teacher based on year_in_hs and counselor"""
    year_in_hs = student_row['year_in_hs']
    counselor = student_row['Counselor']
    student_id = student_row['StudentID']

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
            if student_id % 2 == 0:
                return 'CABRERA A'
            else:
                return 'OVALLES P'
    if year_in_hs >= 5:
        return 'AMEH M'
    
    return 'UNKNOWN'