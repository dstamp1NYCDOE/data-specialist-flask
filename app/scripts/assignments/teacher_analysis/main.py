"""
Main analysis logic for teacher gradebook reports
Save as: app/scripts/assignments/teacher_analysis/main.py
"""
from flask import session
import pandas as pd
import numpy as np
from io import BytesIO
import datetime as dt
from app.scripts import scripts, files_df
import app.scripts.utils as utils
from app.scripts.date_to_marking_period import return_mp_from_date
from app.scripts.assignments.teacher_analysis.utils import (
    calculate_grade_distributions,
    analyze_due_date_patterns,
    compare_teacher_to_peers,
    analyze_student_performance,
    get_special_marks_breakdown,
    analyze_assignment_balance
)
from app.scripts.assignments.teacher_analysis.pdf_generator import generate_pdf_report


def generate_gradebook_report(output_format="excel", report_scope="school", selected_department=None):
    """
    Generate comprehensive gradebook analysis report
    
    Args:
        output_format: 'excel' or 'pdf'
        report_scope: 'school', 'department', 'teacher', or 'teacher_summary'
        selected_department: Department code for filtering (for teacher_summary by dept)
    
    Returns:
        tuple: (file_object, filename)
    """
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    
    # Load student info
    cr_3_07_filename = utils.return_most_recent_report_by_semester(
        files_df, "3_07", year_and_semester=year_and_semester
    )
    cr_3_07_df = utils.return_file_as_df(cr_3_07_filename)
    cr_3_07_df["year_in_hs"] = cr_3_07_df["GEC"].apply(
        utils.return_year_in_hs, args=(school_year,)
    )
    
    # Load assignments
    filename = utils.return_most_recent_report_by_semester(
        files_df, "assignments", year_and_semester=year_and_semester
    )
    assignments_df = utils.return_file_as_df(filename)
    
    # Clean and prepare data
    assignments_df = prepare_assignments_data(assignments_df, school_year)
    
    # Get unique categories dynamically
    categories = assignments_df['Category'].unique().tolist()
    
    # Generate all analysis components
    analysis_results = {
        'assignment_counts': create_assignment_counts(assignments_df, report_scope),
        'grade_distributions': calculate_grade_distributions(assignments_df, report_scope),
        'comparisons': compare_teacher_to_peers(assignments_df, report_scope),
        'due_date_analysis': analyze_due_date_patterns(assignments_df, cr_3_07_df, report_scope),
        'category_balance': analyze_assignment_balance(assignments_df, categories, report_scope),
        'student_performance': analyze_student_performance(assignments_df, cr_3_07_df, report_scope),
        'special_marks': get_special_marks_breakdown(assignments_df, report_scope),
        'raw_data': create_raw_data_pivots(assignments_df, school_year)
    }
    
    # Generate output based on format
    date_str = dt.datetime.now().strftime("%Y-%m-%d")
    
    if report_scope == 'teacher_summary':
        # Generate one-page summaries for each teacher
        from app.scripts.assignments.teacher_analysis.teacher_summary import generate_teacher_summaries
        f = generate_teacher_summaries(assignments_df, cr_3_07_df, selected_department)
        dept_suffix = f"_{selected_department}" if selected_department else "_all"
        filename = f"teacher_summaries{dept_suffix}_{date_str}.pdf"
    elif output_format == "pdf":
        f = generate_pdf_report(analysis_results, report_scope)
        filename = f"gradebook_analysis_{report_scope}_{date_str}.pdf"
    else:
        f = generate_excel_report(analysis_results, report_scope)
        filename = f"gradebook_analysis_{report_scope}_{date_str}.xlsx"
    
    return f, filename


def prepare_assignments_data(assignments_df, school_year):
    """Clean and prepare assignments data"""
    # Handle dates
    assignments_df['DueDate'] = assignments_df['DueDate'].ffill()
    assignments_df['DueDate'] = pd.to_datetime(assignments_df['DueDate'], errors='coerce')
    assignments_df['MP'] = assignments_df['DueDate'].apply(
        return_mp_from_date, args=(school_year,)
    )
    
    # Filter out empty courses
    assignments_df = assignments_df[assignments_df["Course"] != ""]
    
    # Drop assignments worth zero (keep rows with RawScore even if it's special marks)
    assignments_df = assignments_df[assignments_df["WorthPoints"] != 0]
    
    # Drop non-credit bearing classes
    non_credit_prefixes = ['G', 'Z', 'R']
    for prefix in non_credit_prefixes:
        assignments_df = assignments_df[assignments_df["Course"].str[0] != prefix]
    
    # Add department column
    assignments_df['Department'] = assignments_df['Course'].str[0].apply(map_department)
    
    # Add day of week
    assignments_df['DayOfWeek'] = assignments_df['DueDate'].dt.day_name()
    
    # Identify special marks (using RawScore column)
    if 'RawScore' in assignments_df.columns:
        # RawScore can contain special marks like 'F', '\', 'ex', 'ng'
        assignments_df['IsFailure'] = assignments_df['RawScore'].astype(str).str.upper() == 'F'
        assignments_df['IsMissing'] = assignments_df['RawScore'].astype(str) == '\\'
        assignments_df['IsExcused'] = assignments_df['RawScore'].astype(str).str.lower() == 'ex'
        assignments_df['IsNotGraded'] = assignments_df['RawScore'].astype(str).str.lower() == 'ng'
    else:
        # Fallback if RawScore doesn't exist
        assignments_df['IsFailure'] = False
        assignments_df['IsMissing'] = False
        assignments_df['IsExcused'] = False
        assignments_df['IsNotGraded'] = False
    
    # Also check the Missing column if it exists (Y/N values)
    if 'Missing' in assignments_df.columns:
        assignments_df['IsMissing'] = assignments_df['IsMissing'] | (assignments_df['Missing'] == 'Y')
    
    # Now drop rows without numeric RawScore (but after identifying special marks)
    # Keep only rows where we can calculate grades or have special marks
    assignments_df = assignments_df[
        (pd.to_numeric(assignments_df['RawScore'], errors='coerce').notna()) |
        assignments_df['IsFailure'] |
        assignments_df['IsMissing'] |
        assignments_df['IsExcused'] |
        assignments_df['IsNotGraded']
    ]
    
    return assignments_df


def map_department(course_prefix):
    """Map course prefix to department name"""
    dept_map = {
        'M': 'Math',
        'S': 'Science',
        'E': 'English',
        'H': 'Social Studies',
        'P': 'Health/PE'
    }
    return dept_map.get(course_prefix, 'CTE')


def create_assignment_counts(assignments_df, scope):
    """Create assignment counts by teacher/course/category/MP"""
    group_cols = ['Teacher', 'Course', 'Category', 'MP']
    
    if scope == 'school':
        group_cols = ['Category', 'MP']
    elif scope == 'department':
        group_cols = ['Department', 'Category', 'MP']
    
    counts = assignments_df.groupby(group_cols).agg({
        'Assignment': 'count',
        'WorthPoints': 'sum'
    }).rename(columns={
        'Assignment': 'NumAssignments',
        'WorthPoints': 'TotalPoints'
    }).reset_index()
    
    # Add totals by category
    category_totals = assignments_df.groupby(
        group_cols[:-1]  # Exclude MP for totals
    ).agg({
        'Assignment': 'count',
        'WorthPoints': 'sum'
    }).rename(columns={
        'Assignment': 'TotalAssignments',
        'WorthPoints': 'CategoryTotalPoints'
    }).reset_index()
    
    return {
        'by_mp': counts,
        'totals': category_totals
    }


def create_raw_data_pivots(assignments_df, school_year):
    """Create the original pivot tables for reference"""
    assignment_pvt = pd.pivot_table(
        assignments_df,
        index=["Teacher", "Course", "Category", "Assignment", "DueDate", "MP"],
        aggfunc={"CategoryWeight": "max", "WorthPoints": "max", "Percent": "mean"},
    ).reset_index()
    
    category_pvt = pd.pivot_table(
        assignment_pvt,
        index=["Teacher", "Course", "Category"],
        aggfunc={"WorthPoints": "sum"},
    )
    category_pvt.columns = ["TotalWorth"]
    category_pvt = category_pvt.reset_index()
    
    category_by_mp_pvt = pd.pivot_table(
        assignment_pvt,
        index=["Teacher", "Course", "Category"],
        columns=['MP'],
        aggfunc={"WorthPoints": "sum"},
    ).fillna(0)
    
    # Flatten the MultiIndex columns
    category_by_mp_pvt.columns = ['_'.join([str(c) for c in col]).strip('_') for col in category_by_mp_pvt.columns.values]
    category_by_mp_pvt = category_by_mp_pvt.reset_index()
    
    # Calculate total across all MPs
    worth_cols = [col for col in category_by_mp_pvt.columns if col.startswith('WorthPoints')]
    category_by_mp_pvt['TotalWorth'] = category_by_mp_pvt[worth_cols].sum(axis=1)
    
    assignment_pvt = assignment_pvt.merge(
        category_pvt, on=["Teacher", "Course", "Category"], how="left"
    )
    
    assignment_pvt["category_net"] = (
        assignment_pvt["WorthPoints"] / assignment_pvt["TotalWorth"]
    )
    assignment_pvt["overall_net"] = (
        assignment_pvt["category_net"] * assignment_pvt["CategoryWeight"] / 100
    )
    
    return {
        'assignment_details': assignment_pvt,
        'category_by_mp': category_by_mp_pvt
    }


def generate_excel_report(analysis_results, scope):
    """Generate Excel report with multiple sheets"""
    f = BytesIO()
    writer = pd.ExcelWriter(f, engine='xlsxwriter')
    
    # Sheet 1: Assignment Counts
    analysis_results['assignment_counts']['by_mp'].to_excel(
        writer, sheet_name='Assignment Counts by MP', index=False
    )
    analysis_results['assignment_counts']['totals'].to_excel(
        writer, sheet_name='Assignment Totals', index=False
    )
    
    # Sheet 2: Grade Distributions
    analysis_results['grade_distributions']['summary'].to_excel(
        writer, sheet_name='Grade Distributions', index=False
    )
    
    # Sheet 3: Teacher Comparisons
    if 'teacher_vs_peers' in analysis_results['comparisons']:
        analysis_results['comparisons']['teacher_vs_peers'].to_excel(
            writer, sheet_name='Teacher vs Peers', index=False
        )
    if 'teacher_vs_school' in analysis_results['comparisons']:
        analysis_results['comparisons']['teacher_vs_school'].to_excel(
            writer, sheet_name='Teacher vs School', index=False
        )
    
    # Sheet 4: Due Date Analysis
    sheet_name_map = {
        'by_day_of_week': 'Due Dates - Day of Week',
        'clustering_by_date': 'Due Dates - Clustering',
        'distribution_across_mp': 'Due Dates - Across MP',
        'grade_level_clustering': 'Due Dates - Grade Level'
    }
    
    for key, df in analysis_results['due_date_analysis'].items():
        sheet_name = sheet_name_map.get(key, f"Due Dates - {key[:15]}")
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Sheet 5: Category Balance
    analysis_results['category_balance'].to_excel(
        writer, sheet_name='Category Balance', index=False
    )
    
    # Sheet 6: Student Performance
    if analysis_results['student_performance'] is not None:
        analysis_results['student_performance'].to_excel(
            writer, sheet_name='Student Performance', index=False
        )
    
    # Sheet 7: Special Marks
    analysis_results['special_marks'].to_excel(
        writer, sheet_name='Special Marks', index=False
    )
    
    # Sheet 8-9: Raw Data
    analysis_results['raw_data']['assignment_details'].to_excel(
        writer, sheet_name='Raw - Assignment Details', index=False
    )
    analysis_results['raw_data']['category_by_mp'].to_excel(
        writer, sheet_name='Raw - Category by MP', index=False
    )
    
    writer.close()
    f.seek(0)
    return f