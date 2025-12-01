"""
Teacher Impact Analysis Module - Peer Comparison Method

Analyzes teacher impact by comparing students who had a teacher to similar peers
who didn't have that teacher. This controls for regression to the mean and 
course difficulty progression.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from scipy import stats


def analyze_teacher_impact(grades_df: pd.DataFrame, students_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Analyzes teacher impact using peer comparison methodology.
    
    Methodology:
    1. Calculates z-scores for all grades (normalized by curriculum/term)
    2. For each teacher, identifies students who had them
    3. Finds comparable peer students who didn't have that teacher
    4. Compares post-teacher z-scores: (students with teacher) - (peers without teacher)
    5. This controls for regression to mean and course difficulty
    
    Args:
        grades_df: DataFrame with columns [StudentID, Course, Section, Teacher1, Teacher2, Term, Pct]
        students_df: Optional DataFrame with columns [StudentID, LastName, FirstName, GEC, still_enrolled]
    
    Returns:
        Tuple of (teacher_summary_df, teacher_detail_df, diagnostics_df)
    """
    # Validate input data
    required_cols = ['StudentID', 'Course', 'Term', 'Pct']
    missing_cols = set(required_cols) - set(grades_df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    print("Starting teacher impact analysis with peer comparison...")
    
    # Create working copy
    df = grades_df.copy()
    df['Term'] = df['Term'].astype(str)
    df = df.sort_values(['StudentID', 'Term'])
    
    # Extract curriculum and term components
    df['Curriculum'] = df['Course'].apply(_return_curriculum)
    df[['Year', 'TermNum']] = df['Term'].str.split('-', expand=True)
    df['Year'] = df['Year'].astype(int)
    df['TermNum'] = df['TermNum'].astype(int)
    
    # Calculate curriculum statistics and z-scores
    print("Calculating z-scores...")
    stats_df = _calculate_curriculum_stats(df)
    df = df.merge(stats_df, on=['Year', 'TermNum', 'Curriculum'], how='left')
    df['z_score'] = df.apply(_calculate_z_score, axis=1)
    
    # Extract content area
    df['ContentArea'] = df['Course'].str[0]
    
    # Merge student cohort info if available
    if students_df is not None:
        df = df.merge(students_df[['StudentID', 'GEC']], on='StudentID', how='left')
    else:
        df['GEC'] = None
    
    # Create long-form teacher data
    print("Building teacher-student records...")
    teacher_records = _create_teacher_records(df)
    
    # Pre-calculate student z-score histories
    print("Pre-calculating student performance histories...")
    student_histories = _precalculate_student_histories(df)
    
    # Calculate teacher impact using peer comparison
    print("Calculating teacher impacts with peer comparison...")
    impact_details, diagnostics_data = _calculate_teacher_impacts_with_peers(
        df, teacher_records, student_histories
    )
    
    if not impact_details:
        return _create_empty_teacher_dataframes()
    
    detail_df = pd.DataFrame(impact_details)
    diagnostics_df = pd.DataFrame(diagnostics_data)
    
    # Merge student info if provided
    if students_df is not None:
        detail_df = detail_df.merge(
            students_df[['StudentID', 'LastName', 'FirstName', 'GEC', 'still_enrolled']], 
            on='StudentID', 
            how='left'
        )
    
    # Calculate teacher-level summary statistics
    print("Calculating teacher-level summaries...")
    summary_df = _calculate_teacher_summary(detail_df)
    
    print(f"Analysis complete! Processed {len(detail_df)} teacher-student pairs")
    
    return summary_df, detail_df, diagnostics_df


def _return_curriculum(course: str) -> str:
    """Extracts curriculum/subject area from course code."""
    if not course or len(course) == 0:
        return 'UNKNOWN'
    
    if course[0] == 'F':
        return 'LOTE'
    
    if course[0] == 'E':
        return course[0:5] if len(course) >= 5 else course
    
    return course[0:5] if len(course) >= 5 else course


def _calculate_curriculum_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates mean and standard deviation by curriculum, year, and term."""
    stats_df = pd.pivot_table(
        df,
        index=['Year', 'TermNum', 'Curriculum'],
        values='Pct',
        aggfunc=['mean', 'std']
    ).fillna(0).reset_index()
    
    stats_df.columns = ['Year', 'TermNum', 'Curriculum', 'curriculum_mean', 'curriculum_std']
    
    return stats_df


def _calculate_z_score(row) -> float:
    """Calculates z-score for a student's grade relative to curriculum mean/std."""
    curriculum_mean = row['curriculum_mean']
    curriculum_std = row['curriculum_std']
    student_grade = row['Pct']
    
    if curriculum_std == 0 or pd.isna(curriculum_std):
        return 0.0
    
    return (student_grade - curriculum_mean) / curriculum_std


def _create_teacher_records(df: pd.DataFrame) -> pd.DataFrame:
    """Creates long-form teacher records, treating Teacher1 and Teacher2 independently."""
    # Teacher1 records
    teacher1_df = df[['StudentID', 'Course', 'ContentArea', 'Teacher1', 'Term', 'GEC', 'z_score']].copy()
    teacher1_df = teacher1_df[teacher1_df['Teacher1'].notna() & (teacher1_df['Teacher1'] != '')]
    teacher1_df = teacher1_df.rename(columns={'Teacher1': 'Teacher'})
    
    # Teacher2 records
    teacher2_df = df[['StudentID', 'Course', 'ContentArea', 'Teacher2', 'Term', 'GEC', 'z_score']].copy()
    teacher2_df = teacher2_df[teacher2_df['Teacher2'].notna() & (teacher2_df['Teacher2'] != '')]
    teacher2_df = teacher2_df.rename(columns={'Teacher2': 'Teacher'})
    
    teacher_records = pd.concat([teacher1_df, teacher2_df], ignore_index=True)
    
    return teacher_records


def _precalculate_student_histories(df: pd.DataFrame) -> Dict:
    """Pre-calculates baseline and post-teacher z-scores for all student-term combinations."""
    histories = {}
    
    df_sorted = df.sort_values(['StudentID', 'Term']).copy()
    students = df_sorted['StudentID'].unique()
    
    for i, student_id in enumerate(students):
        if i % 500 == 0:
            print(f"  Processing student {i+1}/{len(students)}")
        
        student_data = df_sorted[df_sorted['StudentID'] == student_id]
        terms = student_data['Term'].unique()
        
        # Get student's cohort (GEC) - check if column exists and has data
        student_gec = None
        if 'GEC' in student_data.columns and len(student_data) > 0:
            student_gec = student_data['GEC'].iloc[0] if pd.notna(student_data['GEC'].iloc[0]) else None
        
        for term in terms:
            # Baseline: all courses before this term
            prior_data = student_data[student_data['Term'] < term]
            if len(prior_data) > 0:
                baseline_z = prior_data['z_score'].mean()
                baseline_courses = len(prior_data)
            else:
                baseline_z = None
                baseline_courses = 0
            
            # Post: all courses after this term
            post_data = student_data[student_data['Term'] > term]
            if len(post_data) > 0:
                post_z = post_data['z_score'].mean()
                post_courses = len(post_data)
                terms_after = post_data['Term'].nunique()
                
                # By content area
                post_by_content = {}
                for content_area in post_data['ContentArea'].unique():
                    same_content = post_data[post_data['ContentArea'] == content_area]
                    cross_content = post_data[post_data['ContentArea'] != content_area]
                    
                    if len(same_content) > 0:
                        post_by_content[f'same_{content_area}'] = same_content['z_score'].mean()
                    if len(cross_content) > 0:
                        post_by_content[f'cross_{content_area}'] = cross_content['z_score'].mean()
            else:
                post_z = None
                post_courses = 0
                terms_after = 0
                post_by_content = {}
            
            histories[(student_id, term)] = {
                'baseline_z': baseline_z,
                'baseline_courses': baseline_courses,
                'post_z': post_z,
                'post_courses': post_courses,
                'terms_after': terms_after,
                'gec': student_gec,
                **post_by_content
            }
    
    return histories


def _calculate_teacher_impacts_with_peers(
    df: pd.DataFrame,
    teacher_records: pd.DataFrame,
    student_histories: Dict
) -> Tuple[List[Dict], List[Dict]]:
    """
    Calculates teacher impact using peer comparison.
    
    For each teacher-student pair:
    1. Get student's post-teacher z-score
    2. Find similar peers who didn't have that teacher
    3. Calculate peer average post z-score
    4. Impact = student post z - peer post z
    """
    impact_details = []
    diagnostics_data = []
    
    # Get all students and their complete teacher sets
    student_teachers = teacher_records.groupby('StudentID')['Teacher'].apply(set).to_dict()
    
    for teacher in teacher_records['Teacher'].unique():
        if pd.isna(teacher) or teacher == '':
            continue
        
        teacher_df = teacher_records[teacher_records['Teacher'] == teacher]
        
        for _, row in teacher_df.iterrows():
            student_id = row['StudentID']
            term = row['Term']
            content_area = row['ContentArea']
            student_gec = row['GEC']
            
            # Get student's history
            history = student_histories.get((student_id, term))
            if history is None or history['baseline_z'] is None or history['post_z'] is None:
                continue
            
            # Find comparable peers who DIDN'T have this teacher
            peer_post_z = _find_peer_comparison(
                df, student_histories, student_teachers,
                student_id, term, teacher, student_gec, history['baseline_z']
            )
            
            if peer_post_z is None:
                continue  # No suitable peers found
            
            # Calculate impact as difference from peers
            overall_impact = history['post_z'] - peer_post_z
            
            # Same/cross content impacts
            same_content_z = history.get(f'same_{content_area}')
            cross_content_z = history.get(f'cross_{content_area}')
            
            same_content_impact = same_content_z - peer_post_z if same_content_z is not None else None
            cross_content_impact = cross_content_z - peer_post_z if cross_content_z is not None else None
            
            impact_details.append({
                'Teacher': teacher,
                'StudentID': student_id,
                'TeacherTerm': term,
                'ContentArea': content_area,
                'BaselineZScore': history['baseline_z'],
                'PostTeacherZScore': history['post_z'],
                'PeerPostZScore': peer_post_z,
                'SameContentPostZScore': same_content_z,
                'CrossContentPostZScore': cross_content_z,
                'OverallImpact': overall_impact,
                'SameContentImpact': same_content_impact,
                'CrossContentImpact': cross_content_impact,
                'TermsAnalyzed': history['terms_after'],
                'CoursesAnalyzed': history['post_courses'],
                'BaselineCoursesCount': history['baseline_courses'],
                'PostCoursesCount': history['post_courses']
            })
            
            diagnostics_data.append({
                'Teacher': teacher,
                'StudentID': student_id,
                'TeacherTerm': term,
                'BaselineZScore': history['baseline_z'],
                'PostTeacherZScore': history['post_z'],
                'PeerPostZScore': peer_post_z,
                'Impact': overall_impact,
                'BaselineCoursesCount': history['baseline_courses'],
                'PostCoursesCount': history['post_courses'],
                'TermsAfter': history['terms_after']
            })
    
    return impact_details, diagnostics_data


def _find_peer_comparison(
    df: pd.DataFrame,
    student_histories: Dict,
    student_teachers: Dict,
    student_id: str,
    term: str,
    teacher: str,
    student_gec: str,
    baseline_z: float,
    baseline_tolerance: float = 0.5
) -> float:
    """
    Finds comparable peers who didn't have the target teacher.
    
    Peers must:
    - NOT have had the target teacher at any point
    - Have similar baseline z-score (within tolerance)
    - Ideally be in same cohort (GEC)
    - Have data for the same time period
    """
    peer_post_scores = []
    
    for other_student_id, (other_term) in student_histories.keys():
        if other_student_id == student_id:
            continue
        
        if other_term != term:
            continue
        
        # Check if this student had the target teacher
        if teacher in student_teachers.get(other_student_id, set()):
            continue
        
        other_history = student_histories[(other_student_id, other_term)]
        
        # Must have baseline and post data
        if other_history['baseline_z'] is None or other_history['post_z'] is None:
            continue
        
        # Similar baseline z-score
        if abs(other_history['baseline_z'] - baseline_z) > baseline_tolerance:
            continue
        
        # Prefer same cohort (but don't require it)
        if student_gec is not None and other_history.get('gec') == student_gec:
            peer_post_scores.append(other_history['post_z'])
        elif student_gec is None or len(peer_post_scores) < 3:
            # If no cohort info, or not enough same-cohort peers, include others
            peer_post_scores.append(other_history['post_z'])
    
    if len(peer_post_scores) == 0:
        return None
    
    return np.mean(peer_post_scores)


def _calculate_teacher_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates aggregate teacher-level metrics from student-level details."""
    summary_stats = []
    
    for teacher in detail_df['Teacher'].unique():
        teacher_data = detail_df[detail_df['Teacher'] == teacher]
        
        same_content_data = teacher_data['SameContentImpact'].dropna()
        cross_content_data = teacher_data['CrossContentImpact'].dropna()
        overall_impact_data = teacher_data['OverallImpact'].dropna()
        
        # Statistical significance
        overall_pvalue = None
        if len(overall_impact_data) > 1:
            t_stat, overall_pvalue = stats.ttest_1samp(overall_impact_data, 0)
        
        confidence = _calculate_confidence_level(len(overall_impact_data), overall_pvalue)
        
        summary_stats.append({
            'Teacher': teacher,
            'TotalStudents': len(teacher_data),
            'AvgBaselineZScore': teacher_data['BaselineZScore'].mean(),
            'AvgPostTeacherZScore': teacher_data['PostTeacherZScore'].mean(),
            'AvgPeerPostZScore': teacher_data['PeerPostZScore'].mean(),
            'OverallImpact': overall_impact_data.mean() if len(overall_impact_data) > 0 else None,
            'SameContentImpact': same_content_data.mean() if len(same_content_data) > 0 else None,
            'CrossContentImpact': cross_content_data.mean() if len(cross_content_data) > 0 else None,
            'SameContentStudents': len(same_content_data),
            'CrossContentStudents': len(cross_content_data),
            'AvgTermsAnalyzed': teacher_data['TermsAnalyzed'].mean(),
            'StdDevImpact': overall_impact_data.std() if len(overall_impact_data) > 0 else None,
            'PValue': overall_pvalue,
            'Confidence': confidence
        })
    
    summary_df = pd.DataFrame(summary_stats)
    summary_df = summary_df.sort_values('OverallImpact', ascending=False, na_position='last')
    
    return summary_df


def _calculate_confidence_level(sample_size: int, p_value: float) -> str:
    """Determines confidence level based on sample size and statistical significance."""
    if sample_size < 5:
        return "Insufficient"
    elif sample_size < 15:
        confidence = "Low"
    elif sample_size < 30:
        confidence = "Medium"
    else:
        confidence = "High"
    
    if p_value is not None and p_value > 0.05 and confidence == "High":
        confidence = "Medium"
    
    return confidence


def _create_empty_teacher_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Creates empty DataFrames with correct structure when no data is available."""
    summary_df = pd.DataFrame(columns=[
        'Teacher', 'TotalStudents', 'AvgBaselineZScore', 'AvgPostTeacherZScore',
        'AvgPeerPostZScore', 'OverallImpact', 'SameContentImpact', 'CrossContentImpact',
        'SameContentStudents', 'CrossContentStudents', 'AvgTermsAnalyzed',
        'StdDevImpact', 'PValue', 'Confidence'
    ])
    
    detail_df = pd.DataFrame(columns=[
        'Teacher', 'StudentID', 'TeacherTerm', 'ContentArea', 'BaselineZScore',
        'PostTeacherZScore', 'PeerPostZScore', 'SameContentPostZScore', 'CrossContentPostZScore',
        'OverallImpact', 'SameContentImpact', 'CrossContentImpact',
        'TermsAnalyzed', 'CoursesAnalyzed', 'BaselineCoursesCount', 'PostCoursesCount'
    ])
    
    diagnostics_df = pd.DataFrame(columns=[
        'Teacher', 'StudentID', 'TeacherTerm', 'BaselineZScore', 'PostTeacherZScore',
        'PeerPostZScore', 'Impact', 'BaselineCoursesCount', 'PostCoursesCount', 'TermsAfter'
    ])
    
    return summary_df, detail_df, diagnostics_df