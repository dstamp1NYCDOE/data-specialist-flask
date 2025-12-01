"""
Analysis utilities for attendance data
Handles specific calculations and aggregations for reports
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .attendance_data_prep import (
    should_have_attendance, 
    date_to_day_letter,
    get_meeting_days
)


def create_attendance_completion_grid(attendance_df, teacher, selected_week_dates):
    """
    Create a grid showing which courses are missing attendance marks
    
    Args:
        attendance_df: Full attendance dataframe
        teacher: Teacher name to filter for
        selected_week_dates: List of dates in the selected week
    
    Returns:
        DataFrame with columns: Course, Section, Period, M, T, W, R, F, PriorMissing (sorted by Period)
    """
    # Filter to teacher's courses
    teacher_data = attendance_df[attendance_df['Teacher'] == teacher].copy()
    
    # Get unique course sections
    course_sections = teacher_data[['Course', 'Section', 'Pd']].drop_duplicates()
    
    # Get all dates in semester (for prior missing)
    all_dates = sorted(attendance_df['Date'].unique())
    
    results = []
    
    for _, row in course_sections.iterrows():
        course = row['Course']
        section = row['Section']
        pd_str = row['Pd']
        
        grid_row = {
            'Course': course,
            'Section': section,
            'Period': pd_str,
        }
        
        # Initialize all days with '-' (doesn't meet)
        for day in ['M', 'T', 'W', 'R', 'F']:
            grid_row[day] = '-'
        
        # Check each day of selected week
        for date in selected_week_dates:
            day_letter = date_to_day_letter(pd.to_datetime(date))
            
            if day_letter and should_have_attendance(date, pd_str):
                # Check if we have attendance for this course/section/date
                has_attendance = len(teacher_data[
                    (teacher_data['Course'] == course) &
                    (teacher_data['Section'] == section) &
                    (teacher_data['Date'] == date)
                ]) > 0
                
                grid_row[day_letter] = '✓' if has_attendance else '✗'
        
        # Check for prior missing dates (before selected week)
        prior_dates = [d for d in all_dates if d < min(selected_week_dates)]
        missing_prior = []
        
        for date in prior_dates:
            if should_have_attendance(date, pd_str):
                has_attendance = len(teacher_data[
                    (teacher_data['Course'] == course) &
                    (teacher_data['Section'] == section) &
                    (teacher_data['Date'] == date)
                ]) > 0
                
                if not has_attendance:
                    missing_prior.append(pd.to_datetime(date).strftime('%m/%d'))
        
        grid_row['PriorMissing'] = ', '.join(missing_prior) if missing_prior else ''
        
        results.append(grid_row)
    
    df = pd.DataFrame(results)
    
    # Sort by Period (extract numeric part for sorting)
    
    if len(df) > 0:
        # df['_sort_period'] = df['Period'].str.extract('(\d+)', expand=False).fillna('99').astype(int)
        # df = df.sort_values('_sort_period').drop('_sort_period', axis=1)
        df = df.sort_values('Period')

    # Ensure column order: Course, Section, Period, M, T, W, R, F, PriorMissing
    column_order = ['Course', 'Section', 'Period', 'M', 'T', 'W', 'R', 'F', 'PriorMissing']
    return df[column_order]


def get_students_with_cuts(attendance_df, teacher, selected_week_dates):
    """
    Get students with potential cuts in teacher's classes
    Includes semester-long cut history but only shows students with cuts this week
    
    Returns:
        DataFrame with student info, cut dates this week, and semester cut count
    """
    # Filter to teacher and cuts (ALL SEMESTER, to get semester history)
    teacher_data = attendance_df[
        (attendance_df['Teacher'] == teacher) &
        (attendance_df['cutting?'] == True)
    ].copy()
    
    if len(teacher_data) == 0:
        return pd.DataFrame()
    
    # Aggregate by student-course to get all cut dates
    cut_summary = teacher_data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Pd', 'ClassGrade'
    ]).agg({
        'Date': lambda x: list(x),
        'cutting?': 'sum'
    }).reset_index()
    
    cut_summary = cut_summary.rename(columns={'cutting?': 'SemesterCuts'})
    
    # Separate this week vs prior cuts
    def split_dates(dates_list):
        this_week = [d for d in dates_list if d in selected_week_dates]
        prior = [d for d in dates_list if d not in selected_week_dates]
        return this_week, prior
    
    cut_summary['ThisWeekCuts'] = cut_summary['Date'].apply(
        lambda x: ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in split_dates(x)[0]])
    )
    cut_summary['PriorCuts'] = cut_summary['Date'].apply(
        lambda x: ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in split_dates(x)[1]])
    )
    
    # Filter to only show students with cuts THIS WEEK
    cut_summary = cut_summary[cut_summary['ThisWeekCuts'] != ''].copy()
    
    if len(cut_summary) == 0:
        return pd.DataFrame()
    
    cut_summary = cut_summary.drop('Date', axis=1)
    
    # Sort by number of cuts descending
    cut_summary = cut_summary.sort_values('SemesterCuts', ascending=False)
    
    return cut_summary


def get_students_late_to_school(attendance_df, teacher, selected_week_dates):
    """
    Get students who were late to school and present in teacher's class
    
    Returns:
        DataFrame with student info and late dates
    """
    teacher_data = attendance_df[
        (attendance_df['Teacher'] == teacher) &
        (attendance_df['late_to_school?'] == True) &
        (attendance_df['Date'].isin(selected_week_dates))
    ].copy()
    
    if len(teacher_data) == 0:
        return pd.DataFrame()
    
    late_summary = teacher_data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Pd'
    ]).agg({
        'Date': lambda x: ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in x])
    }).reset_index()
    
    late_summary = late_summary.rename(columns={'Date': 'DatesLate'})
    
    return late_summary


def get_attendance_errors(attendance_df, teacher, selected_week_dates):
    """
    Get potential attendance errors (present in only 1 period)
    
    Returns:
        DataFrame with student info and dates of errors
    """
    teacher_data = attendance_df[
        (attendance_df['Teacher'] == teacher) &
        (attendance_df['attd_error'] == True) &
        (attendance_df['Date'].isin(selected_week_dates))
    ].copy()
    
    if len(teacher_data) == 0:
        return pd.DataFrame()
    
    error_summary = teacher_data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Pd'
    ]).agg({
        'Date': lambda x: ', '.join([pd.to_datetime(d).strftime('%m/%d') for d in x]),
        'Type': 'first'
    }).reset_index()
    
    error_summary = error_summary.rename(columns={
        'Date': 'DatesWithError',
        'Type': 'AttendanceMark'
    })
    
    return error_summary


def get_students_absent_all_week(attendance_df, teacher, selected_week_dates):
    """
    Get students absent all week from teacher's classes (or all classes if teacher is None)
    
    Returns:
        DataFrame with student info
    """
    if teacher is not None:
        teacher_data = attendance_df[
            (attendance_df['Teacher'] == teacher) &
            (attendance_df['Date'].isin(selected_week_dates))
        ].copy()
    else:
        # For counselor/attendance teacher sheets, use all courses
        teacher_data = attendance_df[
            attendance_df['Date'].isin(selected_week_dates)
        ].copy()
    
    # Count days absent per student-course
    absence_counts = teacher_data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Pd'
    ]).agg({
        'in_school?': lambda x: sum(~x),  # Count False (absent) days
        'Date': 'nunique'
    }).reset_index()
    
    absence_counts = absence_counts.rename(columns={
        'in_school?': 'DaysAbsent',
        'Date': 'TotalDays'
    })
    
    # Filter to students absent all week
    all_absent = absence_counts[
        absence_counts['DaysAbsent'] >= absence_counts['TotalDays']
    ].copy()
    
    if len(all_absent) == 0:
        return pd.DataFrame()
    
    return all_absent[['StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Pd']]


def calculate_most_improved_by_section(weekly_stats, selected_week_id):
    """
    Calculate most improved student per course section
    Based on attendance trend and recent improvement
    
    Returns:
        DataFrame with one student per course section (includes Period column)
    """
    # Filter to data up through selected week
    data = weekly_stats[weekly_stats['week_id'] <= selected_week_id].copy()
    
    # Need at least 3 weeks of data
    week_counts = data.groupby(['StudentID', 'Course', 'Section']).size()
    valid_students = week_counts[week_counts >= 3].index
    
    data = data[data.set_index(['StudentID', 'Course', 'Section']).index.isin(valid_students)]
    
    if len(data) == 0:
        return pd.DataFrame()
    
    # Calculate baseline (first 4 weeks) vs recent (last 3 weeks)
    min_week = data['week_id'].min()
    max_week = selected_week_id
    baseline_cutoff = min_week + 4
    recent_cutoff = max_week - 2
    
    improvement_scores = []
    
    # Store period information from the groupby
    print(data.columns)
    print(data)
    for (sid, lname, fname, course, section, period, teacher), group in data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Course', 'Section', 'Period', 'Teacher'
    ]):
        baseline = group[group['week_id'] < baseline_cutoff]
        recent = group[group['week_id'] >= recent_cutoff]
        
        if len(baseline) == 0 or len(recent) == 0:
            continue
        
        baseline_rate = baseline['attendance_rate_smooth'].mean()
        recent_rate = recent['attendance_rate_smooth'].mean()
        
        # Must show improvement and not already excellent
        if recent_rate > baseline_rate and baseline_rate < 0.95:
            improvement = recent_rate - baseline_rate
            trend = group['attendance_trend'].iloc[-1] if len(group) > 0 else 0
            
            score = improvement + (trend * 0.5)  # Weight improvement more than trend
            
            improvement_scores.append({
                'StudentID': sid,
                'LastName': lname,
                'FirstName': fname,
                'Course': course,
                'Section': section,
                'Period': period,
                'Teacher': teacher,
                'BaselineRate': baseline_rate,
                'RecentRate': recent_rate,
                'Improvement': improvement,
                'Score': score
            })
    
    if len(improvement_scores) == 0:
        return pd.DataFrame()
    
    improvement_df = pd.DataFrame(improvement_scores)
    
    # Get top student per section
    improvement_df['Rank'] = improvement_df.groupby(['Course', 'Section'])['Score'].rank(
        ascending=False, method='first'
    )
    
    top_per_section = improvement_df[improvement_df['Rank'] == 1].copy()
    
    # Sort by Period (extract numeric part)
    # top_per_section['_sort_period'] = top_per_section['Period'].str.extract('(\d+)', expand=False).fillna('99').astype(int)
    top_per_section = top_per_section.sort_values(['Teacher', 'Period', 'Course', 'Section'])
    
    return top_per_section


def calculate_most_improved_by_counselor(weekly_stats, selected_week_id, top_n=10):
    """
    Calculate top N most improved students per counselor
    
    Returns:
        DataFrame with top students per counselor
    """
    # Similar to section calculation but across all courses
    data = weekly_stats[weekly_stats['week_id'] <= selected_week_id].copy()
    
    # Get per-student summary across all courses
    student_summary = data.groupby([
        'StudentID', 'LastName', 'FirstName', 'Counselor', 'year_in_hs'
    ]).agg({
        'attendance_rate_smooth': 'mean',
        'attendance_trend': 'mean',
        'week_id': ['min', 'max']
    }).reset_index()
    
    student_summary.columns = [
        'StudentID', 'LastName', 'FirstName', 'Counselor', 'year_in_hs',
        'AvgAttendanceRate', 'AvgTrend', 'MinWeek', 'MaxWeek'
    ]
    
    # Need at least 3 weeks
    student_summary = student_summary[
        (student_summary['MaxWeek'] - student_summary['MinWeek']) >= 2
    ]
    
    # Calculate improvement score (positive trend + good recent rate)
    student_summary['ImprovementScore'] = (
        student_summary['AvgTrend'] * 10 + 
        student_summary['AvgAttendanceRate'] * 0.5
    )
    
    # Filter to improving students only
    improving = student_summary[student_summary['AvgTrend'] > 0].copy()
    
    if len(improving) == 0:
        return pd.DataFrame()
    
    # Get top N per counselor
    improving['Rank'] = improving.groupby('Counselor')['ImprovementScore'].rank(
        ascending=False, method='first'
    )
    
    top_per_counselor = improving[improving['Rank'] <= top_n].copy()
    top_per_counselor = top_per_counselor.sort_values(['Counselor', 'Rank'])
    
    return top_per_counselor


def calculate_weekly_summary_stats(attendance_df, weekly_stats, selected_week_dates, selected_week_id):
    """
    Calculate summary statistics comparing selected week to semester
    
    Returns:
        dict with various summary metrics
    """
    # Filter to selected week
    week_data = attendance_df[attendance_df['Date'].isin(selected_week_dates)].copy()
    
    # Overall stats for the week
    total_periods = len(week_data)
    present_periods = len(week_data[week_data['Type'].isin(['present', 'tardy'])])
    cut_periods = len(week_data[week_data['cutting?'] == True])
    late_to_school_instances = len(week_data[week_data['late_to_school?'] == True])
    
    week_attendance_rate = present_periods / total_periods if total_periods > 0 else 0
    
    # Semester stats (up to selected week)
    semester_data = weekly_stats[weekly_stats['week_id'] <= selected_week_id].copy()
    semester_attendance_rate = semester_data['attendance_rate'].mean() if len(semester_data) > 0 else 0
    
    # By year_in_hs
    week_by_year = week_data.groupby('year_in_hs').apply(
        lambda x: len(x[x['Type'].isin(['present', 'tardy'])]) / len(x) if len(x) > 0 else 0
    ).to_dict()
    
    semester_by_year = semester_data.groupby('year_in_hs')['attendance_rate'].mean().to_dict()
    
    # Count students by category
    unique_students_week = week_data['StudentID'].nunique()
    
    # Calculate chronic absent students properly
    chronic_absent_students = week_data.groupby('StudentID').apply(
        lambda x: (x['Type'] == 'unexcused').sum() / len(x) > 0.1
    )
    chronic_absent_week = chronic_absent_students.sum()
    
    return {
        'week_attendance_rate': week_attendance_rate,
        'semester_attendance_rate': semester_attendance_rate,
        'week_cut_count': cut_periods,
        'week_late_count': late_to_school_instances,
        'total_students': unique_students_week,
        'chronic_absent_count': chronic_absent_week,
        'week_by_year': week_by_year,
        'semester_by_year': semester_by_year,
    }