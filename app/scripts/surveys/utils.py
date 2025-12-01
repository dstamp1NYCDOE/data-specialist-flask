"""
Utility functions for survey analysis
"""
import pandas as pd
import numpy as np


def handle_multiple_responses(value):
    """
    Handle cases where students bubble multiple responses to same question.
    Returns average of multiple responses (e.g., "3,4" -> 3.5)
    
    Parameters:
    -----------
    value : various
        Survey response value (could be int, float, string with commas, or NaN)
        
    Returns:
    --------
    float
        Average value or NaN
    """
    if pd.isna(value):
        return np.nan
    
    # If already numeric, return as is
    if isinstance(value, (int, float)):
        return float(value)
    
    # If string with comma, parse and average
    if isinstance(value, str):
        value = value.strip()
        if ',' in value:
            try:
                values = [float(v.strip()) for v in value.split(',') if v.strip()]
                return np.mean(values) if values else np.nan
            except ValueError:
                return np.nan
        else:
            try:
                return float(value)
            except ValueError:
                return np.nan
    
    return np.nan


def preprocess_survey_responses(df, question_cols):
    """
    Preprocess survey responses to handle multiple bubbles.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Survey data
    question_cols : list
        List of question column names
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with cleaned numeric responses
    """
    df = df.copy()
    
    for col in question_cols:
        if col in df.columns:
            df[col] = df[col].apply(handle_multiple_responses)
    
    return df


def identify_missing_students(df, question_cols):
    """
    Identify students who have not completed the survey (all questions are NaN).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Full dataset
    question_cols : list
        List of question column names
        
    Returns:
    --------
    pd.DataFrame
        DataFrame of students missing survey responses
    """
    # Check which students have all NaN values for question columns
    existing_q_cols = [col for col in question_cols if col in df.columns]
    
    if not existing_q_cols:
        return pd.DataFrame()
    
    missing_mask = df[existing_q_cols].isna().all(axis=1)
    missing_students = df[missing_mask][['StudentID', 'FirstName', 'LastName', 'Counselor', 'year_in_hs']].copy()
    
    return missing_students


def calculate_weighted_scores(df, config):
    """
    Calculate total scores and weighted risk scores based on config.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Working dataset with question responses
    config : object
        Survey configuration object
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added score columns
    """
    question_cols = config.get_question_columns()
    weighted_questions = config.get_weighted_questions()
    
    # Calculate total score (sum of all questions)
    existing_q_cols = [col for col in question_cols if col in df.columns]
    df['Total_Score'] = df[existing_q_cols].sum(axis=1)
    
    # Calculate weighted risk score
    weighted_score = 0
    
    for q_col in existing_q_cols:
        if q_col in weighted_questions:
            # Apply weight multiplier
            weight = weighted_questions[q_col]
            weighted_score += df[q_col] * weight
        else:
            # No multiplier
            weighted_score += df[q_col]
    
    df['Weighted_Risk_Score'] = weighted_score
    
    return df


def assign_risk_profiles(df, config):
    """
    Assign risk profiles to students based on config criteria.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with question scores
    config : object
        Survey configuration object
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added profile columns
    """
    profile_functions = config.get_profile_functions()
    
    for profile_name, profile_func in profile_functions.items():
        df[f'Profile_{profile_name}'] = df.apply(profile_func, axis=1)
    
    # Count number of profiles each student meets
    profile_cols = [col for col in df.columns if col.startswith('Profile_')]
    df['Num_Profiles'] = df[profile_cols].sum(axis=1)
    
    return df


def assign_tiers(df, config):
    """
    Assign MTSS tiers based on percentiles within counselor groups.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with scores and profiles
    config : object
        Survey configuration object
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added Tier column
    """
    tier_thresholds = config.get_tier_thresholds()
    tier_overrides = config.get_tier_overrides()
    
    # Initialize tier column
    df['Tier'] = 'Tier 1'
    
    # Calculate percentiles within each counselor group
    df['Score_Percentile'] = df.groupby('Counselor')['Weighted_Risk_Score'].rank(pct=True) * 100
    
    # Assign tiers based on percentiles (lower scores = higher risk = higher tier)
    # Note: We invert percentiles since lower scores indicate higher risk
    df['Risk_Percentile'] = 100 - df['Score_Percentile']
    
    # Tier 3: Bottom X% (highest risk)
    tier3_threshold = tier_thresholds.get('tier3_percentile', 5)
    df.loc[df['Risk_Percentile'] >= (100 - tier3_threshold), 'Tier'] = 'Tier 3'
    
    # Tier 2: Next Y%
    tier2_low = tier_thresholds.get('tier2_percentile_low', 6)
    tier2_high = tier_thresholds.get('tier2_percentile_high', 15)
    tier2_mask = (df['Risk_Percentile'] >= (100 - tier2_high)) & (df['Risk_Percentile'] < (100 - tier2_low))
    df.loc[tier2_mask, 'Tier'] = 'Tier 2'
    
    # Apply tier overrides based on profiles
    for override_rule in tier_overrides:
        condition_func = override_rule['condition']
        target_tier = override_rule['tier']
        
        override_mask = df.apply(condition_func, axis=1)
        df.loc[override_mask, 'Tier'] = target_tier
    
    # Additional override: Students with 2+ profiles go to at least Tier 2
    df.loc[(df['Num_Profiles'] >= 2) & (df['Tier'] == 'Tier 1'), 'Tier'] = 'Tier 2'
    
    return df


def rank_students_within_tiers(df, config):
    """
    Rank students within their assigned tier for prioritization.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with tier assignments
    config : object
        Survey configuration object
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added Tier_Rank column
    """
    # Get ranking criteria from config
    ranking_criteria = config.get_ranking_criteria()
    
    # Create composite ranking key
    def create_rank_key(row):
        key = []
        
        for criterion in ranking_criteria:
            if criterion['type'] == 'score':
                # Lower score = higher priority (rank 1)
                key.append(row[criterion['column']])
            elif criterion['type'] == 'count':
                # More profiles = higher priority (rank 1)
                key.append(-row[criterion['column']])
            elif criterion['type'] == 'flag':
                # Has flag = higher priority (rank 1)
                key.append(0 if row[criterion['column']] else 1)
            elif criterion['type'] == 'grade':
                # Specific grades get priority
                priority_grades = criterion.get('priority_grades', [])
                if row[criterion['column']] in priority_grades:
                    key.append(0)
                else:
                    key.append(1)
        
        return tuple(key)
    
    # Rank within each tier
    df['_rank_key'] = df.apply(create_rank_key, axis=1)
    df['Tier_Rank'] = df.groupby('Tier')['_rank_key'].rank(method='min')
    df = df.drop('_rank_key', axis=1)
    
    return df


def create_diverging_bar_data(df, question_cols, question_text_map=None):
    """
    Create data for diverging stacked bar charts.
    Rounds decimal responses to nearest integer for chart bucketing.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with question responses
    question_cols : list
        List of question column names
    question_text_map : dict, optional
        Mapping of question numbers to full text
        
    Returns:
    --------
    pd.DataFrame
        Data formatted for diverging bar chart with percentages
    """
    chart_data = []
    
    for q_col in question_cols:
        if q_col not in df.columns:
            continue
        
        # Round responses to nearest integer for charting
        rounded_responses = df[q_col].round()
        
        # Count responses
        value_counts = rounded_responses.value_counts()
        total = len(rounded_responses.dropna())
        
        if total == 0:
            continue
        
        # Calculate percentages for each response option
        strongly_disagree_pct = (value_counts.get(1, 0) / total) * 100
        disagree_pct = (value_counts.get(2, 0) / total) * 100
        agree_pct = (value_counts.get(3, 0) / total) * 100
        strongly_agree_pct = (value_counts.get(4, 0) / total) * 100
        
        # Get question text
        if question_text_map and q_col in question_text_map:
            question_text = question_text_map[q_col]
        else:
            question_text = q_col
        
        chart_data.append({
            'Question': question_text,
            'Question_Code': q_col,
            'Strongly_Disagree_%': strongly_disagree_pct,
            'Disagree_%': disagree_pct,
            'Agree_%': agree_pct,
            'Strongly_Agree_%': strongly_agree_pct,
            'Total_N': total,
            'Mean_Score': df[q_col].mean()
        })
    
    return pd.DataFrame(chart_data)


def calculate_dimension_scores(df, dimension_definitions):
    """
    Calculate dimension subscores based on question groupings.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with question scores
    dimension_definitions : dict
        Dictionary mapping dimension names to lists of question numbers
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with added dimension subscore columns
    """
    for dimension_name, question_numbers in dimension_definitions.items():
        question_cols = [f'Q{q}' for q in question_numbers if f'Q{q}' in df.columns]
        
        if question_cols:
            df[f'{dimension_name}_subscore'] = df[question_cols].sum(axis=1)
            df[f'{dimension_name}_max'] = len(question_cols) * 4  # Assuming 4-point scale
            df[f'{dimension_name}_pct'] = (df[f'{dimension_name}_subscore'] / df[f'{dimension_name}_max']) * 100
    
    return df