import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict


def get_department_from_course_code(course_code):
    """
    Extract department from course code.
    Uses first letter: E=English, M=Math, S=Science, H=Social Studies, P=PE/Health, else=CTE
    
    Args:
        course_code: Course code string
    
    Returns:
        Department name string
    """
    if pd.isna(course_code) or course_code == "":
        return "Unknown"
    
    first_letter = str(course_code)[0].upper()
    
    dept_map = {
        'E': 'English',
        'M': 'Math',
        'S': 'Science',
        'H': 'Social Studies',
        'P': 'PE/Health'
    }
    
    return dept_map.get(first_letter, 'CTE')


def calculate_composite_score(cuts, absences, tardies):
    """
    Calculate composite attendance concern score.
    Weighting: 5x cuts, 2x absences, 1x tardies
    
    Args:
        cuts: Number of cuts
        absences: Number of absences (unexcused absences from school)
        tardies: Number of tardies
    
    Returns:
        Composite score
    """
    return (5 * cuts) + (2 * absences) + (1 * tardies)


def calculate_mtss_tiers(df, score_column='composite_score'):
    """
    Calculate MTSS tiers based on composite scores.
    Tier 3: Top 5%, Tier 2: Next 15%, Tier 1: Remaining 80%
    
    Args:
        df: DataFrame with student data
        score_column: Column name containing composite scores
    
    Returns:
        DataFrame with added 'MTSS_Tier' column
    """
    df = df.copy()
    
    # Students with 0 score are automatically Tier 1
    df['MTSS_Tier'] = 'Tier 1'
    
    # Only calculate percentiles for students with scores > 0
    students_with_concerns = df[df[score_column] > 0].copy()
    
    if len(students_with_concerns) > 0:
        # Calculate percentile thresholds
        tier3_threshold = students_with_concerns[score_column].quantile(0.95)
        tier2_threshold = students_with_concerns[score_column].quantile(0.80)
        
        # Assign tiers
        df.loc[df[score_column] >= tier3_threshold, 'MTSS_Tier'] = 'Tier 3'
        df.loc[(df[score_column] >= tier2_threshold) & (df[score_column] < tier3_threshold), 'MTSS_Tier'] = 'Tier 2'
    
    return df


def calculate_rolling_averages(attd_df, window_days=20):
    """
    Calculate rolling averages for attendance metrics.
    
    Args:
        attd_df: Attendance DataFrame with Date, StudentID, cutting?, late_to_school?
        window_days: Number of school days for rolling window
    
    Returns:
        DataFrame with rolling average metrics per student
    """
    # Get unique dates to determine school days
    school_dates = sorted(attd_df['Date'].unique())
    
    results = []
    
    for student_id in attd_df['StudentID'].unique():
        student_data = attd_df[attd_df['StudentID'] == student_id].copy()
        student_data = student_data.sort_values('Date')
        
        # Group by date to get daily metrics
        daily_metrics = student_data.groupby('Date').agg({
            'cutting?': 'sum',
            'late_to_school?': lambda x: x.any(),  # Any late to school that day
            'in_school?': 'first'  # Whether they were in school
        }).reset_index()
        
        daily_metrics['absent?'] = ~daily_metrics['in_school?']
        
        # Calculate rolling averages
        daily_metrics['cuts_rolling_20day'] = daily_metrics['cutting?'].rolling(window=min(window_days, len(daily_metrics)), min_periods=1).mean()
        daily_metrics['lates_rolling_20day'] = daily_metrics['late_to_school?'].rolling(window=min(window_days, len(daily_metrics)), min_periods=1).mean()
        daily_metrics['absences_rolling_20day'] = daily_metrics['absent?'].rolling(window=min(window_days, len(daily_metrics)), min_periods=1).mean()
        
        # Get most recent values
        if len(daily_metrics) > 0:
            latest = daily_metrics.iloc[-1]
            results.append({
                'StudentID': student_id,
                'cuts_per_day_20day_avg': latest['cuts_rolling_20day'],
                'lates_per_day_20day_avg': latest['lates_rolling_20day'],
                'absences_per_day_20day_avg': latest['absences_rolling_20day']
            })
    
    return pd.DataFrame(results)


def calculate_trend_metrics(attd_df, days_into_semester):
    """
    Calculate trend metrics: early vs recent behavior, acceleration, projections.
    
    Args:
        attd_df: Attendance DataFrame
        days_into_semester: Number of school days elapsed in semester
    
    Returns:
        DataFrame with trend metrics per student
    """
    # Get unique dates
    school_dates = sorted(attd_df['Date'].unique())
    
    if len(school_dates) < 10:  # Need at least 10 days for meaningful trends
        return pd.DataFrame()
    
    # Split into early and recent periods
    midpoint = len(school_dates) // 2
    early_dates = school_dates[:midpoint]
    recent_dates = school_dates[midpoint:]
    
    results = []
    
    for student_id in attd_df['StudentID'].unique():
        student_data = attd_df[attd_df['StudentID'] == student_id].copy()
        
        # Early period metrics
        early_data = student_data[student_data['Date'].isin(early_dates)]
        early_cuts = early_data['cutting?'].sum()
        early_lates = early_data['late_to_school?'].sum()
        early_absences = (~early_data.groupby('Date')['in_school?'].first()).sum()
        early_days = len(early_dates)
        
        # Recent period metrics
        recent_data = student_data[student_data['Date'].isin(recent_dates)]
        recent_cuts = recent_data['cutting?'].sum()
        recent_lates = recent_data['late_to_school?'].sum()
        recent_absences = (~recent_data.groupby('Date')['in_school?'].first()).sum()
        recent_days = len(recent_dates)
        
        # Calculate rates
        early_rate = calculate_composite_score(early_cuts, early_absences, early_lates) / early_days if early_days > 0 else 0
        recent_rate = calculate_composite_score(recent_cuts, recent_lates, recent_absences) / recent_days if recent_days > 0 else 0
        
        # Acceleration (difference in rates)
        acceleration = recent_rate - early_rate
        
        # Projection to end of semester (90 days total)
        days_remaining = 90 - days_into_semester
        current_total_composite = calculate_composite_score(
            student_data['cutting?'].sum(),
            (~student_data.groupby('Date')['in_school?'].first()).sum(),
            student_data['late_to_school?'].sum()
        )
        
        if days_into_semester > 0:
            projected_semester_end = current_total_composite + (recent_rate * days_remaining)
        else:
            projected_semester_end = 0
        
        results.append({
            'StudentID': student_id,
            'early_composite_rate': early_rate,
            'recent_composite_rate': recent_rate,
            'acceleration': acceleration,
            'projected_semester_composite': projected_semester_end,
            'trend_flag': 'Accelerating' if acceleration > 0.5 else ('Improving' if acceleration < -0.5 else 'Stable')
        })
    
    return pd.DataFrame(results)


def find_cutting_together_pairs(attd_df, min_occurrences=3):
    """
    Identify students who are frequently absent from the same class together.
    
    Args:
        attd_df: Attendance DataFrame with StudentID, Date, Course, Section, Pd
        min_occurrences: Minimum number of times students must be absent together
    
    Returns:
        DataFrame with pairs of students and their co-absence patterns
    """
    try:
        # Focus on absences (cuts and unexcused)
        absent_df = attd_df[attd_df['Type'].isin(['unexcused', 'excused']) | attd_df['cutting?']].copy()
        
        if len(absent_df) == 0:
            return pd.DataFrame()
        
        # Ensure we have the necessary columns
        required_cols = ['Date', 'Course', 'Section', 'Pd', 'StudentID']
        missing_cols = [col for col in required_cols if col not in absent_df.columns]
        if missing_cols:
            print(f"Missing columns: {missing_cols}")
            return pd.DataFrame()
        
        # Group by class session (Date, Course, Section, Pd)
        results = []
        
        grouped = absent_df.groupby(['Date', 'Course', 'Section', 'Pd'], dropna=False)
        
        for group_keys, group in grouped:
            # Unpack the tuple - using 'period' for period number to avoid conflict with pandas 'pd'
            if isinstance(group_keys, tuple):
                date, course, section, period = group_keys
            else:
                continue
                
            students = group['StudentID'].unique().tolist()
            
            # Find all pairs of students absent together
            if len(students) >= 2:
                teacher_val = group['Teacher'].iloc[0] if 'Teacher' in group.columns else ''
                
                for student1, student2 in combinations(sorted(students), 2):
                    results.append({
                        'Student1': int(student1) if pd.notna(student1) else student1,
                        'Student2': int(student2) if pd.notna(student2) else student2,
                        'Date': date,
                        'Course': str(course) if pd.notna(course) else '',
                        'Section': str(section) if pd.notna(section) else '',
                        'Pd': int(period) if pd.notna(period) else period,
                        'Teacher': str(teacher_val) if pd.notna(teacher_val) else ''
                    })
        
        if not results:
            return pd.DataFrame()
        
        pairs_df = pd.DataFrame(results)
    
    except Exception as e:
        print(f"Error in find_cutting_together_pairs: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    
    # Count occurrences for each pair
    pair_counts = pairs_df.groupby(['Student1', 'Student2']).agg({
        'Date': 'count',
        'Course': lambda x: ', '.join(sorted(set(x))),
        'Teacher': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    
    pair_counts.columns = ['Student1', 'Student2', 'times_absent_together', 'courses', 'teachers']
    
    # Filter by minimum occurrences
    pair_counts = pair_counts[pair_counts['times_absent_together'] >= min_occurrences]
    pair_counts = pair_counts.sort_values('times_absent_together', ascending=False)
    
    return pair_counts


def analyze_by_teacher_period_course(attd_df):
    """
    Analyze attendance patterns by teacher, period, course, and department.
    
    Args:
        attd_df: Attendance DataFrame
    
    Returns:
        DataFrame with analysis by teacher/course/period
    """
    # Add department column
    attd_df = attd_df.copy()
    attd_df['Department'] = attd_df['Course'].apply(get_department_from_course_code)
    
    # Calculate metrics for each class
    class_metrics = []
    
    for (teacher, course, section, period, dept), group in attd_df.groupby(['Teacher', 'Course', 'Section', 'Pd', 'Department']):
        total_records = len(group)
        unique_students = group['StudentID'].nunique()
        unique_dates = group['Date'].nunique()
        
        cuts = group['cutting?'].sum()
        absences = group[~group['in_school?']].groupby(['StudentID', 'Date']).ngroups
        tardies = group[group['Type'] == 'tardy'].shape[0]
        lates_to_school = group['late_to_school?'].sum()
        
        # Calculate rates
        expected_attendances = unique_students * unique_dates
        if expected_attendances > 0:
            cut_rate = cuts / expected_attendances
            tardy_rate = tardies / expected_attendances
            late_to_school_rate = lates_to_school / expected_attendances
        else:
            cut_rate = tardy_rate = late_to_school_rate = 0
        
        composite_score = calculate_composite_score(cuts, absences, tardies)
        
        class_metrics.append({
            'Teacher': teacher,
            'Course': course,
            'Section': section,
            'Pd': period,
            'Department': dept,
            'num_students': unique_students,
            'num_dates': unique_dates,
            'total_cuts': cuts,
            'total_absences': absences,
            'total_tardies': tardies,
            'total_late_to_school': lates_to_school,
            'cut_rate': cut_rate,
            'tardy_rate': tardy_rate,
            'late_to_school_rate': late_to_school_rate,
            'composite_score': composite_score,
            'avg_composite_per_student': composite_score / unique_students if unique_students > 0 else 0
        })
    
    return pd.DataFrame(class_metrics)


def analyze_by_department(class_analysis_df):
    """
    Aggregate class-level analysis to department level.
    
    Args:
        class_analysis_df: DataFrame from analyze_by_teacher_period_course
    
    Returns:
        DataFrame with department-level metrics
    """
    dept_metrics = class_analysis_df.groupby('Department').agg({
        'num_students': 'sum',
        'total_cuts': 'sum',
        'total_absences': 'sum',
        'total_tardies': 'sum',
        'total_late_to_school': 'sum',
        'composite_score': 'sum',
        'Course': 'count'  # Number of classes
    }).reset_index()
    
    dept_metrics.columns = ['Department', 'total_students', 'total_cuts', 'total_absences', 
                            'total_tardies', 'total_late_to_school', 'composite_score', 'num_classes']
    
    # Calculate rates
    dept_metrics['avg_composite_per_student'] = dept_metrics['composite_score'] / dept_metrics['total_students']
    dept_metrics['cut_rate'] = dept_metrics['total_cuts'] / dept_metrics['total_students']
    dept_metrics['tardy_rate'] = dept_metrics['total_tardies'] / dept_metrics['total_students']
    
    dept_metrics = dept_metrics.sort_values('composite_score', ascending=False)
    
    return dept_metrics


def analyze_by_period(attd_df):
    """
    Analyze attendance patterns by period across the school.
    
    Args:
        attd_df: Attendance DataFrame
    
    Returns:
        DataFrame with period-level metrics
    """
    period_metrics = []
    
    for period_num, group in attd_df.groupby('Pd'):
        unique_students = group['StudentID'].nunique()
        unique_dates = group['Date'].nunique()
        
        cuts = group['cutting?'].sum()
        absences = group[~group['in_school?']].groupby(['StudentID', 'Date']).ngroups
        tardies = group[group['Type'] == 'tardy'].shape[0]
        lates_to_school = group['late_to_school?'].sum()
        
        composite_score = calculate_composite_score(cuts, absences, tardies)
        
        period_metrics.append({
            'Period': period_num,
            'num_students': unique_students,
            'total_cuts': cuts,
            'total_absences': absences,
            'total_tardies': tardies,
            'total_late_to_school': lates_to_school,
            'composite_score': composite_score,
            'avg_composite_per_student': composite_score / unique_students if unique_students > 0 else 0
        })
    
    return pd.DataFrame(period_metrics).sort_values('Period')