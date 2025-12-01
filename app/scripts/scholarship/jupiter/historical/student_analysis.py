"""
Student Grade Trajectory Analysis Module

Calculates term-by-term grade trajectories using z-scores (standard deviations from mean)
and weighted linear regression to emphasize recent performance.
"""

import pandas as pd
import numpy as np
from typing import Tuple
from sklearn.linear_model import LinearRegression


def analyze_student_trajectories(grades_df: pd.DataFrame, students_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates term-by-term grade trajectories using z-scores and weighted regression.
    
    Methodology:
    1. Calculates z-scores for each course grade (normalized by curriculum/term)
    2. Aggregates z-scores by student-term to show relative performance
    3. Uses weighted linear regression (recent terms weighted more heavily)
    4. Tracks time-sequenced trajectory showing improvement/decline patterns
    
    Args:
        grades_df: DataFrame with columns [StudentID, Course, Section, Teacher1, Teacher2, Term, Pct]
        students_df: Optional DataFrame with columns [StudentID, LastName, FirstName, GEC, still_enrolled]
    
    Returns:
        Tuple of (student_summary_df, student_term_detail_df)
        - student_summary: Overall trajectory metrics per student
        - student_term_detail: Term-by-term z-score data
    """
    # Validate input data
    required_cols = ['StudentID', 'Course', 'Term', 'Pct']
    missing_cols = set(required_cols) - set(grades_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Create working copy
    df = grades_df.copy()
    df['Term'] = df['Term'].astype(str)
    
    # Extract curriculum (first letter for subject area, or custom logic)
    df['Curriculum'] = df['Course'].apply(_return_curriculum)
    
    # Extract Year and Term number from Term string (format: "YYYY-T")
    df[['Year', 'TermNum']] = df['Term'].str.split('-', expand=True)
    df['Year'] = df['Year'].astype(int)
    df['TermNum'] = df['TermNum'].astype(int)
    
    # Calculate statistics by curriculum, year, and term
    stats_df = _calculate_curriculum_stats(df)
    
    # Merge stats back to grades
    df = df.merge(stats_df, on=['Year', 'TermNum', 'Curriculum'], how='left')
    
    # Calculate z-scores for each grade
    df['z_score'] = df.apply(_calculate_z_score, axis=1)
    
    # Calculate student average z-score by term
    student_term_zscores = pd.pivot_table(
        df,
        index=['StudentID', 'Year', 'TermNum', 'Term'],
        values='z_score',
        aggfunc='mean'
    ).reset_index()
    
    # Sort by student and term to ensure proper time sequencing
    student_term_zscores = student_term_zscores.sort_values(['StudentID', 'Year', 'TermNum'])
    
    # Create term-level detail dataframe
    detail_df = student_term_zscores.copy()
    detail_df = detail_df.rename(columns={'z_score': 'AvgZScore'})
    
    # Merge student info if provided
    if students_df is not None:
        detail_df = detail_df.merge(
            students_df[['StudentID', 'LastName', 'FirstName', 'GEC', 'still_enrolled']], 
            on='StudentID', 
            how='left'
        )
    
    # Calculate student-level summary with weighted regression
    summary_df = _calculate_student_summary(student_term_zscores, students_df)
    
    return summary_df, detail_df


def _return_curriculum(course: str) -> str:
    """
    Extracts curriculum/subject area from course code.
    
    Args:
        course: Course code string
    
    Returns:
        Curriculum identifier
    """
    if not course or len(course) == 0:
        return 'UNKNOWN'
    
    # Foreign language courses
    if course[0] == 'F':
        return 'LOTE'
    
    # English courses (use first 5 characters for granularity)
    if course[0] == 'E':
        return course[0:5] if len(course) >= 5 else course
    
    # All other courses (Math, Science, History, etc.)
    return course[0:5] if len(course) >= 5 else course


def _calculate_curriculum_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates mean and standard deviation by curriculum, year, and term.
    
    Args:
        df: Grade data with Curriculum, Year, TermNum, and Pct columns
    
    Returns:
        DataFrame with mean and std for each curriculum-term combination
    """
    stats_df = pd.pivot_table(
        df,
        index=['Year', 'TermNum', 'Curriculum'],
        values='Pct',
        aggfunc=['mean', 'std']
    ).fillna(0).reset_index()
    
    # Flatten column names
    stats_df.columns = ['Year', 'TermNum', 'Curriculum', 'curriculum_mean', 'curriculum_std']
    
    return stats_df


def _calculate_z_score(row) -> float:
    """
    Calculates z-score for a student's grade relative to curriculum mean/std.
    
    Args:
        row: DataFrame row with curriculum_mean, curriculum_std, and Pct
    
    Returns:
        Z-score (standard deviations from mean)
    """
    curriculum_mean = row['curriculum_mean']
    curriculum_std = row['curriculum_std']
    student_grade = row['Pct']
    
    # Handle cases where std is 0 (all students got same grade)
    if curriculum_std == 0 or pd.isna(curriculum_std):
        return 0.0
    
    return (student_grade - curriculum_mean) / curriculum_std


def _calculate_student_summary(student_term_zscores: pd.DataFrame, students_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculates student-level summary using weighted linear regression.
    
    Args:
        student_term_zscores: Term-by-term z-score data
        students_df: Optional student info DataFrame
    
    Returns:
        DataFrame with summary metrics per student
    """
    summary_stats = []
    
    for student_id in student_term_zscores['StudentID'].unique():
        student_data = student_term_zscores[student_term_zscores['StudentID'] == student_id].copy()
        student_data = student_data.sort_values(['Year', 'TermNum'])
        
        # Get z-score list (time-ordered)
        z_score_list = student_data['z_score'].tolist()
        
        if len(z_score_list) == 0:
            continue
        
        # Calculate weighted trajectory (slope) using linear regression
        trajectory_slope = _determine_weighted_slope(z_score_list)
        
        # Calculate overall average z-score
        avg_z_score = np.mean(z_score_list)
        
        # Most recent term z-score
        most_recent_z_score = z_score_list[-1]
        
        # Determine trend
        trend = _determine_trend(trajectory_slope, z_score_list)
        
        # Create sparkline data
        sparkline_data = z_score_list
        
        # Count terms above/below average (z-score > 0 or < 0)
        terms_above_avg = sum(1 for z in z_score_list if z > 0)
        terms_below_avg = sum(1 for z in z_score_list if z < 0)
        
        # Get student info if available
        student_info = {}
        if students_df is not None:
            student_match = students_df[students_df['StudentID'] == student_id]
            if len(student_match) > 0:
                student_info = {
                    'LastName': student_match.iloc[0]['LastName'],
                    'FirstName': student_match.iloc[0]['FirstName'],
                    'GEC': student_match.iloc[0]['GEC'],
                    'still_enrolled': student_match.iloc[0]['still_enrolled']
                }
        
        summary_stats.append({
            'StudentID': student_id,
            **student_info,
            'FirstTerm': student_data['Term'].iloc[0],
            'LastTerm': student_data['Term'].iloc[-1],
            'TermsAnalyzed': len(z_score_list),
            'TrajectorySlope': trajectory_slope,
            'AvgZScore': avg_z_score,
            'MostRecentZScore': most_recent_z_score,
            'Trend': trend,
            'TermsAboveAvg': terms_above_avg,
            'TermsBelowAvg': terms_below_avg,
            'SparklineData': sparkline_data
        })
    
    summary_df = pd.DataFrame(summary_stats)
    
    # Sort by trajectory slope (descending) - students improving most
    summary_df = summary_df.sort_values('TrajectorySlope', ascending=False)
    
    return summary_df


def _determine_weighted_slope(z_score_list: list) -> float:
    """
    Calculates weighted linear regression slope with recent terms weighted more heavily.
    
    Args:
        z_score_list: Time-ordered list of z-scores
    
    Returns:
        Slope coefficient (rate of change per term)
    """
    if len(z_score_list) < 2:
        return 0.0
    
    # Create DataFrame for regression
    df = pd.DataFrame({'ZScore': z_score_list})
    df['X'] = df.index + 1  # Time sequence (1, 2, 3, ...)
    df['sample_weights'] = df.index + 1  # Weight increases with time (recent terms matter more)
    
    # Fit weighted linear regression
    regr = LinearRegression()
    regr.fit(df[['X']], df[['ZScore']], sample_weight=df['sample_weights'])
    
    return regr.coef_[0][0]


def _determine_trend(slope: float, z_score_list: list) -> str:
    """
    Determines overall trend category based on slope and z-scores.
    
    Args:
        slope: Trajectory slope from weighted regression
        z_score_list: Time-ordered z-scores
    
    Returns:
        Trend category string
    """
    if len(z_score_list) < 3:
        return "Insufficient Data"
    
    avg_z_score = np.mean(z_score_list)
    
    # Categorize based on slope magnitude and direction
    if abs(slope) < 0.1:
        # Stable trajectory
        if avg_z_score > 0.5:
            return "Consistently High"
        elif avg_z_score < -0.5:
            return "Consistently Low"
        else:
            return "Stable Average"
    elif slope > 0.3:
        return "Strongly Improving"
    elif slope > 0.1:
        return "Improving"
    elif slope < -0.3:
        return "Strongly Declining"
    elif slope < -0.1:
        return "Declining"
    else:
        return "Stable"


def _create_empty_student_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Creates empty DataFrames with correct structure when no data is available.
    
    Returns:
        Tuple of (empty student_summary_df, empty student_detail_df)
    """
    summary_df = pd.DataFrame(columns=[
        'StudentID', 'LastName', 'FirstName', 'GEC', 'still_enrolled',
        'FirstTerm', 'LastTerm', 'TermsAnalyzed', 'TrajectorySlope',
        'AvgZScore', 'MostRecentZScore', 'Trend', 'TermsAboveAvg',
        'TermsBelowAvg', 'SparklineData'
    ])
    
    detail_df = pd.DataFrame(columns=[
        'StudentID', 'Year', 'TermNum', 'Term', 'AvgZScore',
        'LastName', 'FirstName', 'GEC', 'still_enrolled'
    ])
    
    return summary_df, detail_df