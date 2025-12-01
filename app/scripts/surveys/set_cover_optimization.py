"""
Set cover optimization for selecting high-leverage class sections
"""
import pandas as pd
import numpy as np
from collections import defaultdict


def calculate_set_cover_recommendations(analysis_df, config, threshold=2.0):
    """
    Use weighted greedy set cover to identify top 10 sections per dimension
    that maximize coverage of at-risk students while minimizing redundancy.
    
    Parameters:
    -----------
    analysis_df : pd.DataFrame
        Student-section data with dimension scores
    config : object
        Survey configuration
    threshold : float
        Threshold for "at-risk" status (dimension avg <= threshold)
        
    Returns:
    --------
    dict
        Mapping of (dimension, section_id) -> recommendation_rank (1-10)
    """

    print(analysis_df)
    recommendations = {}
    
    # Only process the 5 named dimensions
    if not hasattr(config, 'dimension_groups'):
        return recommendations
    
    dimension_groups = config.dimension_groups
    
    for dimension_name, questions in dimension_groups.items():
        # Calculate dimension average for each student
        dim_cols = [f'Q{q}' for q in questions if f'Q{q}' in analysis_df.columns]
        if not dim_cols:
            continue
        
        # Get dimension average (should already exist from main analysis)
        dim_avg_col = f'{dimension_name}_dim_avg'
        if dim_avg_col not in analysis_df.columns:
            numeric_cols = analysis_df[dim_cols].apply(pd.to_numeric, errors='coerce')
            analysis_df[dim_avg_col] = numeric_cols.mean(axis=1)
        
        # Identify at-risk students for this dimension
        at_risk_df = analysis_df[
            pd.to_numeric(analysis_df[dim_avg_col], errors='coerce') <= threshold
        ].copy()
        
        if at_risk_df.empty:
            continue
        
        at_risk_students = set(at_risk_df['StudentID'].unique())
        
        # Build section -> student mapping
        section_students = defaultdict(set)
        section_priority = {}  # Store priority scores for tie-breaking
        
        for section_id in analysis_df['Section_ID'].unique():
            section_df = analysis_df[analysis_df['Section_ID'] == section_id]
            
            # Get at-risk students in this section
            section_at_risk = set(section_df['StudentID']) & at_risk_students
            
            if section_at_risk:
                section_students[section_id] = section_at_risk
                
                # Calculate priority score for this section-dimension combo
                # (will be used for tie-breaking)
                section_at_risk_df = section_df[
                    section_df['StudentID'].isin(section_at_risk)
                ]
                
                if len(section_at_risk_df) > 0:
                    scores = pd.to_numeric(
                        section_at_risk_df[dim_avg_col], 
                        errors='coerce'
                    ).dropna()
                    
                    if len(scores) > 0:
                        # Priority based on: number of at-risk students + severity
                        n_at_risk = len(section_at_risk)
                        avg_severity = (threshold - scores.mean()) / threshold
                        section_priority[section_id] = n_at_risk + avg_severity
                    else:
                        section_priority[section_id] = len(section_at_risk)
        
        # Run weighted greedy set cover to select top 10 sections
        selected_sections = weighted_greedy_set_cover(
            section_students,
            section_priority,
            max_sections=10
        )
        
        # Store recommendations with ranks
        for rank, section_id in enumerate(selected_sections, 1):
            recommendations[(dimension_name, section_id)] = rank
    
    return recommendations


def weighted_greedy_set_cover(section_students, section_priority, max_sections=10):
    """
    Weighted greedy set cover algorithm with partial credit for overlap.
    
    Parameters:
    -----------
    section_students : dict
        Mapping of section_id -> set of student IDs
    section_priority : dict
        Mapping of section_id -> priority score (for tie-breaking)
    max_sections : int
        Maximum number of sections to select
        
    Returns:
    --------
    list
        Ordered list of selected section IDs (ranked 1 to max_sections)
    """
    if not section_students:
        return []
    
    selected = []
    student_coverage_count = defaultdict(int)  # Track how many times each student is covered
    
    for _ in range(max_sections):
        if not section_students:
            break
        
        best_section = None
        best_score = -1
        
        for section_id, students in section_students.items():
            if section_id in selected:
                continue
            
            # Calculate weighted coverage score
            # Give full credit for uncovered students, partial credit for already-covered
            coverage_score = 0
            for student in students:
                if student_coverage_count[student] == 0:
                    coverage_score += 1.0  # Full credit for new coverage
                else:
                    # Diminishing returns: 1/(n+1) where n is current coverage count
                    coverage_score += 1.0 / (student_coverage_count[student] + 1)
            
            # Break ties using priority score
            composite_score = (coverage_score, section_priority.get(section_id, 0))
            
            if composite_score > best_score:
                best_score = composite_score
                best_section = section_id
        
        if best_section is None:
            break
        
        # Select this section
        selected.append(best_section)
        
        # Update coverage counts
        for student in section_students[best_section]:
            student_coverage_count[student] += 1
    
    return selected


def add_recommendations_to_section_analysis(section_analysis_df, recommendations, config):
    """
    Add recommendation ranks to the section analysis dataframe.
    
    Parameters:
    -----------
    section_analysis_df : pd.DataFrame
        Section analysis results
    recommendations : dict
        Mapping of (dimension, section_id) -> rank
    config : object
        Survey configuration (used to get dimension names)
        
    Returns:
    --------
    pd.DataFrame
        Updated dataframe with Recommendation_Rank column
    """
    section_analysis_df = section_analysis_df.copy()
    
    # Create Section_ID if it doesn't exist
    if 'Section_ID' not in section_analysis_df.columns:
        section_analysis_df['Section_ID'] = (
            section_analysis_df['Course'] + ' - ' + section_analysis_df['Section']
        )
    
    # Build dimension mapping from config
    dimension_map = {}
    if hasattr(config, 'dimension_groups'):
        for internal_name in config.dimension_groups.keys():
            display_name = internal_name.replace('_', ' ')
            dimension_map[display_name] = internal_name
    
    # Add recommendation rank
    def get_recommendation_rank(row):
        dimension = row['Dimension']
        section_id = row.get('Section_ID', '')
        
        # Convert dimension display name back to internal name
        internal_dimension = dimension_map.get(dimension, dimension)
        rank = recommendations.get((internal_dimension, section_id), None)
        
        return rank if rank is not None else ''
    
    section_analysis_df['Recommendation_Rank'] = section_analysis_df.apply(
        get_recommendation_rank, 
        axis=1
    )
    
    return section_analysis_df


def create_coverage_summary(analysis_df, recommendations, config, threshold=2.0):
    """
    Create a summary showing coverage statistics for the recommended sections.
    
    Parameters:
    -----------
    analysis_df : pd.DataFrame
        Student-section data
    recommendations : dict
        Recommendation mappings
    config : object
        Survey configuration
    threshold : float
        At-risk threshold
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics per dimension
    """
    summary_data = []
    
    if not hasattr(config, 'dimension_groups'):
        return pd.DataFrame()
    
    for dimension_name, questions in config.dimension_groups.items():
        dim_cols = [f'Q{q}' for q in questions if f'Q{q}' in analysis_df.columns]
        if not dim_cols:
            continue
        
        dim_avg_col = f'{dimension_name}_dim_avg'
        if dim_avg_col not in analysis_df.columns:
            continue
        
        # Get at-risk students
        at_risk_df = analysis_df[
            pd.to_numeric(analysis_df[dim_avg_col], errors='coerce') <= threshold
        ]
        total_at_risk = len(at_risk_df['StudentID'].unique())
        
        if total_at_risk == 0:
            continue
        
        # Get recommended sections for this dimension
        recommended_sections = [
            section_id for (dim, section_id), rank in recommendations.items()
            if dim == dimension_name
        ]
        
        if not recommended_sections:
            continue
        
        # Calculate coverage
        covered_students = set()
        duplicate_coverage_count = 0
        
        for section_id in recommended_sections:
            section_students = set(
                analysis_df[
                    (analysis_df['Section_ID'] == section_id) &
                    (analysis_df['StudentID'].isin(at_risk_df['StudentID']))
                ]['StudentID']
            )
            
            # Track duplicates
            already_covered = covered_students & section_students
            duplicate_coverage_count += len(already_covered)
            
            covered_students.update(section_students)
        
        coverage_pct = (len(covered_students) / total_at_risk * 100) if total_at_risk > 0 else 0
        avg_coverage_per_student = (len(covered_students) + duplicate_coverage_count) / len(covered_students) if len(covered_students) > 0 else 0
        
        summary_data.append({
            'Dimension': dimension_name.replace('_', ' '),
            'Total_At_Risk_Students': total_at_risk,
            'Students_Covered': len(covered_students),
            'Coverage_Pct': round(coverage_pct, 1),
            'Recommended_Sections': len(recommended_sections),
            'Avg_Coverage_Per_Student': round(avg_coverage_per_student, 2),
            'Total_Student_Interventions': len(covered_students) + duplicate_coverage_count
        })
    
    return pd.DataFrame(summary_data)