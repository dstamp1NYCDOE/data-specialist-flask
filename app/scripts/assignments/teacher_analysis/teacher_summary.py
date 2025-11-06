"""
One-page teacher summary reports
Save as: app/scripts/assignments/teacher_analysis/teacher_summary.py
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import pandas as pd
import numpy as np


def generate_teacher_summaries(assignments_df, student_df, selected_department=None):
    """
    Generate one-page summary for each teacher (or filtered by department)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.3*inch, leftMargin=0.3*inch,
                           topMargin=0.3*inch, bottomMargin=0.3*inch)
    
    story = []
    
    # Filter by department if specified
    if selected_department:
        assignments_df = assignments_df[assignments_df['Department'] == selected_department]
    
    # Get list of teachers
    teachers = sorted(assignments_df['Teacher'].unique())
    
    # Generate a page for each teacher
    for idx, teacher in enumerate(teachers):
        teacher_data = assignments_df[assignments_df['Teacher'] == teacher]
        
        # Generate the teacher's summary page
        teacher_story = create_teacher_summary_page(teacher, teacher_data, assignments_df)
        story.extend(teacher_story)
        
        # Add page break unless it's the last teacher
        if idx < len(teachers) - 1:
            story.append(PageBreak())
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def create_teacher_summary_page(teacher_name, teacher_df, all_assignments_df):
    """Create a single summary page for one teacher"""
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TeacherTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=3,
        spaceBefore=6
    )
    
    # Title
    story.append(Paragraph(f"Teacher Gradebook Summary: {teacher_name}", title_style))
    story.append(Spacer(1, 0.05*inch))
    
    # Get teacher's courses
    courses = teacher_df['Course'].unique()
    
    # Process each course
    for course in courses:
        course_data = teacher_df[teacher_df['Course'] == course]
        
        # Section: Course name
        story.append(Paragraph(f"Course: {course}", section_style))
        
        # 1. Assignment Structure Table (more compact)
        structure_table = create_assignment_structure_table(course_data, all_assignments_df, course)
        if structure_table:
            story.append(structure_table)
            story.append(Spacer(1, 0.08*inch))
        
        # 2. Due Date Timeline Chart (NEW)
        due_date_chart = create_due_date_timeline_chart(course_data, teacher_name, course)
        if due_date_chart:
            story.append(due_date_chart)
            story.append(Spacer(1, 0.08*inch))
        
        # 3. Grade Distribution Comparison (more compact)
        grade_comparison = create_grade_comparison_table(course_data, all_assignments_df, course)
        if grade_comparison:
            story.append(grade_comparison)
            story.append(Spacer(1, 0.05*inch))
    
    return story


def create_assignment_structure_table(teacher_course_df, all_df, course):
    """Create table showing assignment counts by category compared to peers"""
    
    # Teacher's assignment counts by category and MP
    teacher_stats = teacher_course_df.groupby(['Category', 'MP']).agg({
        'Assignment': 'nunique',
        'WorthPoints': 'sum'
    }).reset_index()
    
    # Pivot to show MPs as columns
    teacher_counts = teacher_stats.pivot_table(
        index='Category',
        columns='MP',
        values='Assignment',
        fill_value=0
    )
    
    teacher_points = teacher_stats.pivot_table(
        index='Category',
        columns='MP',
        values='WorthPoints',
        fill_value=0
    )
    
    # Get peer averages (same course, different teachers)
    peer_course_df = all_df[(all_df['Course'] == course) & 
                            (all_df['Teacher'] != teacher_course_df['Teacher'].iloc[0])]
    
    if len(peer_course_df) > 0:
        peer_stats = peer_course_df.groupby(['Teacher', 'Category', 'MP']).agg({
            'Assignment': 'nunique'
        }).reset_index()
        
        peer_avg = peer_stats.groupby(['Category', 'MP'])['Assignment'].mean().reset_index()
        peer_counts = peer_avg.pivot_table(
            index='Category',
            columns='MP',
            values='Assignment',
            fill_value=0
        )
    else:
        peer_counts = None
    
    # Get department averages
    dept = teacher_course_df['Department'].iloc[0]
    dept_df = all_df[all_df['Department'] == dept]
    dept_stats = dept_df.groupby(['Teacher', 'Category', 'MP']).agg({
        'Assignment': 'nunique'
    }).reset_index()
    dept_avg = dept_stats.groupby(['Category', 'MP'])['Assignment'].mean().reset_index()
    dept_counts = dept_avg.pivot_table(
        index='Category',
        columns='MP',
        values='Assignment',
        fill_value=0
    )
    
    # Build comparison table
    data = [['Category', 'MP', 'Teacher\nCount', 'Peer Avg', 'Dept Avg', 'School Avg']]
    
    mps = sorted(teacher_counts.columns)
    categories = teacher_counts.index.tolist()
    
    # School average
    school_stats = all_df.groupby(['Teacher', 'Category', 'MP']).agg({
        'Assignment': 'nunique'
    }).reset_index()
    school_avg = school_stats.groupby(['Category', 'MP'])['Assignment'].mean().reset_index()
    school_counts = school_avg.pivot_table(
        index='Category',
        columns='MP',
        values='Assignment',
        fill_value=0
    )
    
    for category in categories:
        for mp in mps:
            teacher_val = teacher_counts.loc[category, mp] if mp in teacher_counts.columns else 0
            peer_val = peer_counts.loc[category, mp] if peer_counts is not None and category in peer_counts.index and mp in peer_counts.columns else 0
            dept_val = dept_counts.loc[category, mp] if category in dept_counts.index and mp in dept_counts.columns else 0
            school_val = school_counts.loc[category, mp] if category in school_counts.index and mp in school_counts.columns else 0
            
            data.append([
                category,
                f"MP{mp}",
                f"{int(teacher_val)}",
                f"{peer_val:.1f}" if peer_val > 0 else "N/A",
                f"{dept_val:.1f}",
                f"{school_val:.1f}"
            ])
    
    # Create table
    table = Table(data, colWidths=[1.0*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (1, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
    ])
    
    table.setStyle(style)
    return table


def create_due_date_timeline_chart(course_df, teacher_name, course):
    """Create timeline bar chart showing when assignments are due by date"""
    
    try:
        # Group assignments by due date and category
        date_assignments = course_df.groupby(['DueDate', 'Category']).agg({
            'Assignment': 'nunique'
        }).reset_index()
        
        # Get all unique dates and sort
        date_assignments = date_assignments.sort_values('DueDate')
        
        print(f"Creating due date chart for {teacher_name} - {course}")
        print(f"Date range: {date_assignments['DueDate'].min()} to {date_assignments['DueDate'].max()}")
        print(f"Total date points: {len(date_assignments)}")
        
        # Create figure with bars for each category
        categories = date_assignments['Category'].unique()
        colors_palette = ['#1f4788', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6']
        
        fig = go.Figure()
        
        for idx, category in enumerate(categories):
            cat_data = date_assignments[date_assignments['Category'] == category]
            
            fig.add_trace(go.Bar(
                name=category,
                x=cat_data['DueDate'],
                y=cat_data['Assignment'],
                marker_color=colors_palette[idx % len(colors_palette)],
                hovertemplate='<b>%{x|%b %d}</b><br>Assignments: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title=f"Assignment Due Dates - {course}",
            xaxis_title="Date",
            yaxis_title="Number of Assignments Due",
            barmode='stack',
            height=180,
            width=650,
            showlegend=True,
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=1.02, 
                xanchor="right", 
                x=1,
                font=dict(size=8)
            ),
            margin=dict(l=40, r=10, t=50, b=40),
            xaxis=dict(
                tickformat='%b %d',
                tickangle=-45,
                tickfont=dict(size=8)
            ),
            yaxis=dict(
                tickfont=dict(size=8)
            ),
            font=dict(size=9)
        )
        
        # Convert to image
        img_bytes = fig.to_image(format="png", width=650, height=180)
        img_buffer = BytesIO(img_bytes)
        
        print(f"Successfully created due date chart for {course}")
        return Image(img_buffer, width=6.5*inch, height=1.8*inch)
        
    except Exception as e:
        print(f"Error creating due date timeline for {teacher_name} - {course}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_grade_comparison_table(teacher_course_df, all_df, course):
    """Create table comparing grade statistics to peers, department, and school"""
    
    # Teacher stats
    teacher_avg = teacher_course_df['Percent'].mean()
    teacher_median = teacher_course_df['Percent'].median()
    teacher_fail_rate = (teacher_course_df['IsFailure'].sum() / len(teacher_course_df) * 100)
    teacher_missing_rate = (teacher_course_df['IsMissing'].sum() / len(teacher_course_df) * 100)
    
    # Peer stats (same course)
    teacher_name = teacher_course_df['Teacher'].iloc[0]
    peer_df = all_df[(all_df['Course'] == course) & (all_df['Teacher'] != teacher_name)]
    
    if len(peer_df) > 0:
        peer_avg = peer_df['Percent'].mean()
        peer_median = peer_df['Percent'].median()
        peer_fail_rate = (peer_df['IsFailure'].sum() / len(peer_df) * 100)
        peer_missing_rate = (peer_df['IsMissing'].sum() / len(peer_df) * 100)
    else:
        peer_avg = peer_median = peer_fail_rate = peer_missing_rate = None
    
    # Department stats
    dept = teacher_course_df['Department'].iloc[0]
    dept_df = all_df[all_df['Department'] == dept]
    dept_avg = dept_df['Percent'].mean()
    dept_median = dept_df['Percent'].median()
    dept_fail_rate = (dept_df['IsFailure'].sum() / len(dept_df) * 100)
    dept_missing_rate = (dept_df['IsMissing'].sum() / len(dept_df) * 100)
    
    # School stats
    school_avg = all_df['Percent'].mean()
    school_median = all_df['Percent'].median()
    school_fail_rate = (all_df['IsFailure'].sum() / len(all_df) * 100)
    school_missing_rate = (all_df['IsMissing'].sum() / len(all_df) * 100)
    
    # Build table
    data = [
        ['Metric', 'Teacher', 'Course Peers', 'Department', 'School'],
        ['Avg Grade', 
         f'{teacher_avg:.1f}%',
         f'{peer_avg:.1f}%' if peer_avg is not None else 'N/A',
         f'{dept_avg:.1f}%',
         f'{school_avg:.1f}%'],
        ['Median Grade',
         f'{teacher_median:.1f}%',
         f'{peer_median:.1f}%' if peer_median is not None else 'N/A',
         f'{dept_median:.1f}%',
         f'{school_median:.1f}%'],
        ['Failure Rate',
         f'{teacher_fail_rate:.1f}%',
         f'{peer_fail_rate:.1f}%' if peer_fail_rate is not None else 'N/A',
         f'{dept_fail_rate:.1f}%',
         f'{school_fail_rate:.1f}%'],
        ['Missing Rate',
         f'{teacher_missing_rate:.1f}%',
         f'{peer_missing_rate:.1f}%' if peer_missing_rate is not None else 'N/A',
         f'{dept_missing_rate:.1f}%',
         f'{school_missing_rate:.1f}%']
    ]
    
    table = Table(data, colWidths=[1.3*inch, 0.9*inch, 1.0*inch, 1.0*inch, 0.9*inch])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
    ])
    
    table.setStyle(style)
    return table