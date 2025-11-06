"""
Utility functions for teacher gradebook analysis
Save as: app/scripts/assignments/teacher_analysis/utils.py
"""
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_grade_distributions(assignments_df, scope):
    """Calculate grade distribution statistics"""
    group_cols = ['Teacher', 'Course']
    
    if scope == 'school':
        group_cols = []
    elif scope == 'department':
        group_cols = ['Department']
    
    if group_cols:
        stats = assignments_df.groupby(group_cols).agg({
            'Percent': ['mean', 'median', 'std', 'min', 'max'],
            'IsFailure': 'sum',
            'IsMissing': 'sum',
            'Assignment': 'nunique'  # Count unique assignments, not rows
        }).reset_index()
    else:
        stats = pd.DataFrame([{
            'Percent_mean': assignments_df['Percent'].mean(),
            'Percent_median': assignments_df['Percent'].median(),
            'Percent_std': assignments_df['Percent'].std(),
            'Percent_min': assignments_df['Percent'].min(),
            'Percent_max': assignments_df['Percent'].max(),
            'IsFailure_sum': assignments_df['IsFailure'].sum(),
            'IsMissing_sum': assignments_df['IsMissing'].sum(),
            'Assignment_nunique': assignments_df['Assignment'].nunique()
        }])
    
    # Flatten columns if needed
    if group_cols:
        stats.columns = ['_'.join(col).strip('_') for col in stats.columns]
    
    # Calculate percentages - use total student submissions for rates
    # but keep unique assignment count separate
    total_submissions = len(assignments_df) if not group_cols else assignments_df.groupby(group_cols).size()
    
    if group_cols:
        stats = stats.merge(
            total_submissions.reset_index(name='Total_Submissions'),
            on=group_cols
        )
        stats['Failure_Rate'] = (stats['IsFailure_sum'] / stats['Total_Submissions'] * 100).round(2)
        stats['Missing_Rate'] = (stats['IsMissing_sum'] / stats['Total_Submissions'] * 100).round(2)
    else:
        stats['Total_Submissions'] = len(assignments_df)
        stats['Failure_Rate'] = (stats['IsFailure_sum'] / stats['Total_Submissions'] * 100).round(2)
        stats['Missing_Rate'] = (stats['IsMissing_sum'] / stats['Total_Submissions'] * 100).round(2)
    
    # Rename columns for clarity
    rename_map = {
        'Percent_mean': 'Avg_Grade',
        'Percent_median': 'Median_Grade',
        'Percent_std': 'StdDev_Grade',
        'Percent_min': 'Min_Grade',
        'Percent_max': 'Max_Grade',
        'IsFailure_sum': 'Num_Failures',
        'IsMissing_sum': 'Num_Missing',
        'Assignment_nunique': 'Num_Unique_Assignments'
    }
    stats = stats.rename(columns=rename_map)
    
    return {'summary': stats, 'raw': assignments_df}


def compare_teacher_to_peers(assignments_df, scope):
    """Compare each teacher to peers teaching the same course and to school average"""
    results = {}
    
    if scope == 'teacher':
        # Teacher vs peers teaching same course
        teacher_stats = assignments_df.groupby(['Teacher', 'Course']).agg({
            'Percent': 'mean',
            'IsFailure': lambda x: (x.sum() / len(x) * 100),
            'IsMissing': lambda x: (x.sum() / len(x) * 100)
        }).reset_index()
        teacher_stats.columns = ['Teacher', 'Course', 'Teacher_Avg', 'Teacher_Fail_Rate', 'Teacher_Missing_Rate']
        
        # Course averages (excluding current teacher)
        course_stats = []
        for _, row in teacher_stats.iterrows():
            course_data = assignments_df[
                (assignments_df['Course'] == row['Course']) & 
                (assignments_df['Teacher'] != row['Teacher'])
            ]
            if len(course_data) > 0:
                course_avg = course_data['Percent'].mean()
                course_fail = (course_data['IsFailure'].sum() / len(course_data) * 100)
                course_missing = (course_data['IsMissing'].sum() / len(course_data) * 100)
            else:
                course_avg = np.nan
                course_fail = np.nan
                course_missing = np.nan
            
            course_stats.append({
                'Teacher': row['Teacher'],
                'Course': row['Course'],
                'Peer_Avg': course_avg,
                'Peer_Fail_Rate': course_fail,
                'Peer_Missing_Rate': course_missing
            })
        
        peer_comparison = pd.merge(
            teacher_stats,
            pd.DataFrame(course_stats),
            on=['Teacher', 'Course']
        )
        peer_comparison['Diff_vs_Peers'] = (
            peer_comparison['Teacher_Avg'] - peer_comparison['Peer_Avg']
        ).round(2)
        
        results['teacher_vs_peers'] = peer_comparison
        
        # Teacher vs school average
        school_avg = assignments_df['Percent'].mean()
        school_fail = (assignments_df['IsFailure'].sum() / len(assignments_df) * 100)
        school_missing = (assignments_df['IsMissing'].sum() / len(assignments_df) * 100)
        
        teacher_stats['School_Avg'] = school_avg
        teacher_stats['School_Fail_Rate'] = school_fail
        teacher_stats['School_Missing_Rate'] = school_missing
        teacher_stats['Diff_vs_School'] = (
            teacher_stats['Teacher_Avg'] - school_avg
        ).round(2)
        
        results['teacher_vs_school'] = teacher_stats
    
    return results


def analyze_due_date_patterns(assignments_df, student_df, scope):
    """Analyze when assignments are due"""
    results = {}
    
    # Day of week distribution
    day_counts = assignments_df.groupby('DayOfWeek').size().reset_index(name='Count')
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts['DayOfWeek'] = pd.Categorical(day_counts['DayOfWeek'], categories=day_order, ordered=True)
    day_counts = day_counts.sort_values('DayOfWeek')
    results['by_day_of_week'] = day_counts
    
    # Assignments by date
    date_counts = assignments_df.groupby('DueDate').agg({
        'Assignment': 'count',
        'Course': 'nunique',
        'Teacher': 'nunique'
    }).reset_index()
    date_counts.columns = ['DueDate', 'Num_Assignments', 'Num_Courses', 'Num_Teachers']
    date_counts = date_counts.sort_values('Num_Assignments', ascending=False)
    results['clustering_by_date'] = date_counts.head(50)  # Top 50 busiest dates
    
    # Distribution across marking period
    mp_distribution = assignments_df.groupby(['MP', 'DueDate']).size().reset_index(name='Count')
    # Calculate day within MP (1-based)
    for mp in mp_distribution['MP'].unique():
        mp_data = mp_distribution[mp_distribution['MP'] == mp].copy()
        if len(mp_data) > 0:
            min_date = mp_data['DueDate'].min()
            mp_distribution.loc[mp_distribution['MP'] == mp, 'Day_in_MP'] = (
                (mp_data['DueDate'] - min_date).dt.days + 1
            )
    results['distribution_across_mp'] = mp_distribution
    
    # Grade level clustering (students taking same classes)
    if 'year_in_hs' in student_df.columns and 'StudentID' in assignments_df.columns:
        # Merge to get student grade levels
        assignments_with_grade = assignments_df.merge(
            student_df[['StudentID', 'year_in_hs']],
            on='StudentID',
            how='left'
        )
        
        # Find dates with high assignment counts for same grade level
        grade_clusters = assignments_with_grade.groupby(['DueDate', 'year_in_hs']).agg({
            'Assignment': 'count',
            'Course': lambda x: ', '.join(x.unique()[:5])  # Top 5 courses
        }).reset_index()
        grade_clusters.columns = ['DueDate', 'Grade_Level', 'Num_Assignments', 'Courses']
        grade_clusters = grade_clusters[grade_clusters['Num_Assignments'] >= 3]  # 3+ assignments
        grade_clusters = grade_clusters.sort_values('Num_Assignments', ascending=False)
        results['grade_level_clustering'] = grade_clusters.head(50)
    
    return results


def analyze_assignment_balance(assignments_df, categories, scope):
    """Analyze balance between assignment categories"""
    group_cols = ['Teacher', 'Course', 'MP']
    
    if scope == 'school':
        group_cols = ['MP']
    elif scope == 'department':
        group_cols = ['Department', 'MP']
    
    # Count assignments by category
    balance = assignments_df.groupby(group_cols + ['Category']).size().reset_index(name='Count')
    
    # Pivot to get categories as columns
    balance_pivot = balance.pivot_table(
        index=group_cols,
        columns='Category',
        values='Count',
        fill_value=0
    ).reset_index()
    
    # Calculate ratios if we have exactly 2 categories
    if len(categories) == 2:
        cat1, cat2 = categories[0], categories[1]
        if cat1 in balance_pivot.columns and cat2 in balance_pivot.columns:
            balance_pivot['Ratio'] = (
                balance_pivot[cat1] / (balance_pivot[cat2] + 0.001)  # Avoid division by zero
            ).round(2)
    
    # Add total
    balance_pivot['Total_Assignments'] = balance_pivot[categories].sum(axis=1)
    
    return balance_pivot


def analyze_student_performance(assignments_df, student_df, scope):
    """Analyze student performance patterns"""
    if 'StudentID' not in assignments_df.columns:
        return None
    
    # Calculate average grade by student and course
    student_course_avg = assignments_df.groupby(['StudentID', 'Course', 'Teacher']).agg({
        'Percent': 'mean'
    }).reset_index()
    student_course_avg.columns = ['StudentID', 'Course', 'Teacher', 'Avg_Grade']
    
    # Calculate student's overall average
    student_overall = assignments_df.groupby('StudentID').agg({
        'Percent': 'mean'
    }).reset_index()
    student_overall.columns = ['StudentID', 'Overall_Avg']
    
    # Merge
    performance = student_course_avg.merge(student_overall, on='StudentID')
    performance['Diff_from_Overall'] = (
        performance['Avg_Grade'] - performance['Overall_Avg']
    ).round(2)
    
    # Add student info
    if 'year_in_hs' in student_df.columns:
        performance = performance.merge(
            student_df[['StudentID', 'year_in_hs']],
            on='StudentID',
            how='left'
        )
    
    # Identify students performing significantly better/worse
    performance['Performance_Category'] = pd.cut(
        performance['Diff_from_Overall'],
        bins=[-100, -10, -5, 5, 10, 100],
        labels=['Much Worse', 'Worse', 'Average', 'Better', 'Much Better']
    )
    
    return performance


def get_special_marks_breakdown(assignments_df, scope):
    """Get breakdown of special marks (F, \, ex, ng)"""
    group_cols = ['Teacher', 'Course']
    
    if scope == 'school':
        group_cols = []
    elif scope == 'department':
        group_cols = ['Department']
    
    if group_cols:
        marks = assignments_df.groupby(group_cols).agg({
            'IsFailure': 'sum',
            'IsMissing': 'sum',
            'IsExcused': 'sum',
            'IsNotGraded': 'sum',
            'Assignment': 'nunique'  # Count unique assignments
        }).reset_index()
        
        # Also get total submissions for percentage calculations
        total_submissions = assignments_df.groupby(group_cols).size().reset_index(name='Total_Submissions')
        marks = marks.merge(total_submissions, on=group_cols)
    else:
        marks = pd.DataFrame([{
            'IsFailure': assignments_df['IsFailure'].sum(),
            'IsMissing': assignments_df['IsMissing'].sum(),
            'IsExcused': assignments_df['IsExcused'].sum(),
            'IsNotGraded': assignments_df['IsNotGraded'].sum(),
            'Assignment': assignments_df['Assignment'].nunique(),
            'Total_Submissions': len(assignments_df)
        }])
    
    # Calculate percentages based on total submissions
    marks['Failure_Pct'] = (marks['IsFailure'] / marks['Total_Submissions'] * 100).round(2)
    marks['Missing_Pct'] = (marks['IsMissing'] / marks['Total_Submissions'] * 100).round(2)
    marks['Excused_Pct'] = (marks['IsExcused'] / marks['Total_Submissions'] * 100).round(2)
    marks['NotGraded_Pct'] = (marks['IsNotGraded'] / marks['Total_Submissions'] * 100).round(2)
    
    # Rename columns
    rename_map = {
        'IsFailure': 'Num_Failures',
        'IsMissing': 'Num_Missing',
        'IsExcused': 'Num_Excused',
        'IsNotGraded': 'Num_NotGraded',
        'Assignment': 'Num_Unique_Assignments'
    }
    marks = marks.rename(columns=rename_map)
    
    return marks