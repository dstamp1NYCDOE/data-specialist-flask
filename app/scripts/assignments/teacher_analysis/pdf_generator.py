"""
PDF generation for teacher gradebook analysis
Save as: app/scripts/assignments/teacher_analysis/pdf_generator.py
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import pandas as pd


def generate_pdf_report(analysis_results, scope):
    """Generate PDF report with tables and visualizations"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    scope_text = scope.capitalize()
    title = Paragraph(f"Gradebook Analysis Report - {scope_text} Level", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    # Section 1: Assignment Counts
    story.append(Paragraph("Assignment Counts by Marking Period", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    counts_table = create_table_from_df(
        analysis_results['assignment_counts']['by_mp'].head(30),
        "No assignment count data available"
    )
    if counts_table:
        story.append(counts_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 2: Grade Distribution Box Plots
    story.append(Paragraph("Grade Distribution Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    if 'raw' in analysis_results['grade_distributions']:
        box_plot_img = create_grade_distribution_boxplot(
            analysis_results['grade_distributions']['raw'],
            scope
        )
        if box_plot_img:
            story.append(box_plot_img)
            story.append(Spacer(1, 0.2*inch))
    
    # Grade distribution summary table
    dist_table = create_table_from_df(
        analysis_results['grade_distributions']['summary'],
        "No grade distribution data available"
    )
    if dist_table:
        story.append(dist_table)
    
    story.append(PageBreak())
    
    # Section 3: Teacher Comparisons
    if 'teacher_vs_peers' in analysis_results['comparisons']:
        story.append(Paragraph("Teacher vs Peer Comparison", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        comp_table = create_table_from_df(
            analysis_results['comparisons']['teacher_vs_peers'].head(25),
            "No comparison data available"
        )
        if comp_table:
            story.append(comp_table)
        story.append(PageBreak())
    
    # Section 4: Due Date Analysis
    story.append(Paragraph("Assignment Due Date Patterns", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    # Day of week chart
    if 'by_day_of_week' in analysis_results['due_date_analysis']:
        dow_chart = create_day_of_week_chart(
            analysis_results['due_date_analysis']['by_day_of_week']
        )
        if dow_chart:
            story.append(dow_chart)
            story.append(Spacer(1, 0.2*inch))
    
    # Clustering table
    if 'clustering_by_date' in analysis_results['due_date_analysis']:
        story.append(Paragraph("High-Volume Assignment Dates", styles['Heading3']))
        story.append(Spacer(1, 0.1*inch))
        cluster_table = create_table_from_df(
            analysis_results['due_date_analysis']['clustering_by_date'].head(20),
            "No clustering data available"
        )
        if cluster_table:
            story.append(cluster_table)
    
    story.append(PageBreak())
    
    # Section 5: Category Balance
    story.append(Paragraph("Assignment Category Balance", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    balance_table = create_table_from_df(
        analysis_results['category_balance'].head(30),
        "No category balance data available"
    )
    if balance_table:
        story.append(balance_table)
    
    story.append(Spacer(1, 0.2*inch))
    
    # Section 6: Special Marks
    story.append(Paragraph("Special Marks Breakdown", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    marks_table = create_table_from_df(
        analysis_results['special_marks'].head(30),
        "No special marks data available"
    )
    if marks_table:
        story.append(marks_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def create_table_from_df(df, empty_message="No data available"):
    """Convert DataFrame to ReportLab Table"""
    if df is None or len(df) == 0:
        return Paragraph(empty_message, getSampleStyleSheet()['Normal'])
    
    # Limit columns for readability
    if len(df.columns) > 10:
        df = df.iloc[:, :10]
    
    # Convert to list format
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Format numbers
    for i in range(1, len(data)):
        for j in range(len(data[i])):
            val = data[i][j]
            if isinstance(val, float):
                data[i][j] = f"{val:.2f}"
            elif pd.isna(val):
                data[i][j] = "N/A"
    
    # Create table
    table = Table(data)
    
    # Style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ])
    
    table.setStyle(style)
    return table


def create_grade_distribution_boxplot(assignments_df, scope):
    """Create box and whisker plot for grade distributions"""
    try:
        if scope == 'teacher':
            # Box plot by teacher
            fig = go.Figure()
            
            teachers = assignments_df['Teacher'].unique()[:20]  # Limit to 20 teachers
            for teacher in teachers:
                teacher_data = assignments_df[assignments_df['Teacher'] == teacher]['Percent']
                fig.add_trace(go.Box(
                    y=teacher_data,
                    name=teacher,
                    boxmean='sd'
                ))
            
            fig.update_layout(
                title="Grade Distribution by Teacher",
                yaxis_title="Grade (%)",
                xaxis_title="Teacher",
                height=400,
                width=800,
                showlegend=False
            )
            
        elif scope == 'department':
            # Box plot by department
            fig = px.box(
                assignments_df,
                x='Department',
                y='Percent',
                title="Grade Distribution by Department",
                labels={'Percent': 'Grade (%)', 'Department': 'Department'}
            )
            fig.update_layout(height=400, width=800)
            
        else:  # school
            # Single box plot for entire school
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=assignments_df['Percent'],
                name='School-Wide',
                boxmean='sd'
            ))
            
            fig.update_layout(
                title="School-Wide Grade Distribution",
                yaxis_title="Grade (%)",
                height=400,
                width=800
            )
        
        # Convert to image
        img_bytes = fig.to_image(format="png", width=800, height=400)
        img_buffer = BytesIO(img_bytes)
        
        return Image(img_buffer, width=7*inch, height=3.5*inch)
    
    except Exception as e:
        print(f"Error creating boxplot: {e}")
        return None


def create_day_of_week_chart(day_df):
    """Create bar chart for assignments by day of week"""
    try:
        fig = px.bar(
            day_df,
            x='DayOfWeek',
            y='Count',
            title="Assignment Distribution by Day of Week",
            labels={'Count': 'Number of Assignments', 'DayOfWeek': 'Day of Week'},
            color='Count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            height=400,
            width=800,
            showlegend=False
        )
        
        # Convert to image
        img_bytes = fig.to_image(format="png", width=800, height=400)
        img_buffer = BytesIO(img_bytes)
        
        return Image(img_buffer, width=7*inch, height=3.5*inch)
    
    except Exception as e:
        print(f"Error creating day of week chart: {e}")
        return None