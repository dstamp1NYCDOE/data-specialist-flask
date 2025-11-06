"""
Main analysis function for student belongingness survey
"""
import pandas as pd
import numpy as np
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.datavalidation import DataValidation

from .utils import (
    identify_missing_students,
    calculate_weighted_scores,
    assign_risk_profiles,
    assign_tiers,
    rank_students_within_tiers,
    create_diverging_bar_data,
    calculate_relative_risk,
    preprocess_survey_responses
)


def analyze_survey(
    df,
    config,
    biographical_columns=None,
    handle_missing='flag',
    question_text_map=None
):
    """
    Main function to analyze survey data and generate Excel report.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Survey data with StudentID, FirstName, LastName, Counselor, year_in_hs, 
        FormID, and Q1-Q16 columns
    config : object
        Survey configuration object (e.g., from belongingness_config.py)
    biographical_columns : list, optional
        Additional biographical columns beyond Counselor and year_in_hs
    handle_missing : str, default 'flag'
        How to handle missing survey responses: 'flag' or 'impute'
    question_text_map : dict, optional
        Mapping of question numbers to full question text for charts
        
    Returns:
    --------
    BytesIO
        Excel file in memory ready to send via Flask response
    """
    
    # Initialize biographical columns
    if biographical_columns is None:
        biographical_columns = []
    
    # Core columns that should always be present
    core_bio_columns = ['Counselor', 'year_in_hs']
    all_bio_columns = core_bio_columns + biographical_columns
    
    # Validate required columns
    required_cols = ['StudentID', 'FirstName', 'LastName'] + core_bio_columns + ['FormID']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Identify question columns based on config
    question_cols = config.get_question_columns()
    
    # Preprocess survey responses to handle multiple bubbles
    df = preprocess_survey_responses(df, question_cols)
    
    # Identify missing students (all question responses are NaN)
    missing_students_df = identify_missing_students(df, question_cols)
    
    # Create working dataframe (exclude missing students if flagged)
    if handle_missing == 'flag':
        working_df = df[~df['StudentID'].isin(missing_students_df['StudentID'])].copy()
    else:
        working_df = df.copy()
    
    # Handle missing values for students with partial responses
    if handle_missing == 'impute':
        for col in question_cols:
            if col in working_df.columns:
                mean_val = working_df[col].mean()
                working_df[col].fillna(mean_val, inplace=True)
    
    # Calculate weighted risk scores
    working_df = calculate_weighted_scores(working_df, config)
    
    # Assign risk profiles
    working_df = assign_risk_profiles(working_df, config)
    
    # Assign MTSS tiers (by counselor)
    working_df = assign_tiers(working_df, config)
    
    # Rank students within tiers
    working_df = rank_students_within_tiers(working_df, config)
    
    # Create dimension subscores for analysis
    working_df = calculate_dimension_subscores(working_df, config)
    
    # Generate Excel workbook
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Raw analyzed data
        working_df.to_excel(writer, sheet_name='Analysis', index=False)
        
        # Sheet 2: Missing students
        if not missing_students_df.empty:
            missing_students_df.to_excel(writer, sheet_name='Missing Responses', index=False)
        
        # Sheet 3: Control Panel for interactive dashboard
        create_control_panel(writer, working_df, all_bio_columns, config)
        
        # Sheet 4-6: Tier lists
        create_tier_sheets(writer, working_df, config)
        
        # Sheet 7+: Visualization data
        viz_sheets = create_visualization_sheets(
            writer, 
            working_df, 
            all_bio_columns, 
            config,
            question_text_map
        )
        
        # Sheet: Relative Risk Analysis
        rr_sheet_name = create_relative_risk_sheet(writer, working_df, all_bio_columns, config)
    
    # Reload workbook to add charts and formatting
    output.seek(0)
    wb = load_workbook(output)
    
    # Add charts to visualization sheets
    add_diverging_bar_charts(wb, viz_sheets, config)
    
    # Add relative risk charts
    if rr_sheet_name:
        add_relative_risk_charts(wb, rr_sheet_name)
    
    # Format all sheets
    format_workbook(wb)
    
    # Save back to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


def calculate_dimension_subscores(df, config):
    """Calculate subscores for different dimensions of belongingness."""
    if hasattr(config, 'dimension_groups'):
        for dimension_name, questions in config.dimension_groups.items():
            cols = [f'Q{q}' for q in questions if f'Q{q}' in df.columns]
            if cols:
                df[f'{dimension_name}_subscore'] = df[cols].sum(axis=1)
                df[f'{dimension_name}_avg'] = df[cols].mean(axis=1)
    return df


def create_control_panel(writer, df, bio_columns, config):
    """Create an interactive control panel sheet for dashboard."""
    profiles = config.get_profile_list()
    
    # Create control panel data
    control_data = []
    
    # Header
    control_data.append(['INTERACTIVE CONTROL PANEL', ''])
    control_data.append(['', ''])
    
    # Profile selector
    control_data.append(['Select Profile for Analysis:', profiles[0]])
    control_data.append(['', ''])
    
    # Biographical variable selector
    control_data.append(['Select Biographical Variable:', bio_columns[0] if bio_columns else 'Counselor'])
    control_data.append(['', ''])
    
    # Instructions
    control_data.append(['INSTRUCTIONS:', ''])
    control_data.append(['1. Use dropdowns above to select profile and variable', ''])
    control_data.append(['2. Relative Risk sheet will update automatically', ''])
    control_data.append(['3. Charts will show data for selected combinations', ''])
    control_data.append(['', ''])
    
    # Available options reference
    control_data.append(['Available Profiles:', ''])
    for profile in profiles:
        profile_name = config.get_profile_name(profile) if hasattr(config, 'get_profile_name') else f'Profile {profile}'
        control_data.append([f'  Profile_{profile}', profile_name])
    
    control_data.append(['', ''])
    control_data.append(['Available Biographical Variables:', ''])
    for bio_var in bio_columns:
        control_data.append([f'  {bio_var}', ''])
    
    control_df = pd.DataFrame(control_data)
    control_df.to_excel(writer, sheet_name='Control Panel', index=False, header=False)


def create_tier_sheets(writer, df, config):
    """Create separate sheets for each tier with full student details."""
    tiers = ['Tier 3', 'Tier 2', 'Tier 1']
    
    for tier in tiers:
        tier_df = df[df['Tier'] == tier].copy()
        
        if not tier_df.empty:
            # Sort by rank
            tier_df = tier_df.sort_values('Tier_Rank')
            
            # Select columns to display
            display_cols = [
                'Tier_Rank', 'StudentID', 'FirstName', 'LastName', 
                'Counselor', 'year_in_hs', 'FormID',
                'Weighted_Risk_Score', 'Total_Score'
            ]
            
            # Add risk profile columns
            profile_cols = [col for col in tier_df.columns if col.startswith('Profile_')]
            display_cols.extend(profile_cols)
            
            # Add question scores
            question_cols = [col for col in tier_df.columns if col.startswith('Q') and col[1:].isdigit()]
            display_cols.extend(sorted(question_cols, key=lambda x: int(x[1:])))
            
            # Add dimension subscores if they exist
            subscore_cols = [col for col in tier_df.columns if '_subscore' in col or '_avg' in col]
            display_cols.extend(subscore_cols)
            
            # Filter to existing columns
            display_cols = [col for col in display_cols if col in tier_df.columns]
            
            # Add suggested interventions column
            tier_df['Suggested_Interventions'] = tier_df.apply(
                lambda row: config.get_intervention_suggestions(row), 
                axis=1
            )
            display_cols.append('Suggested_Interventions')
            
            tier_df[display_cols].to_excel(writer, sheet_name=tier, index=False)


def create_visualization_sheets(writer, df, bio_columns, config, question_text_map):
    """Create sheets with diverging bar chart data."""
    question_cols = config.get_question_columns()
    viz_sheets = []
    
    # Overall diverging bar data for each question
    overall_data = create_diverging_bar_data(df, question_cols, question_text_map)
    overall_data.to_excel(writer, sheet_name='Overall Distribution', index=False)
    viz_sheets.append(('Overall Distribution', 'overall'))
    
    # By biographical variables
    for bio_col in bio_columns:
        if bio_col in df.columns:
            bio_data = []
            for group_value in df[bio_col].dropna().unique():
                group_df = df[df[bio_col] == group_value]
                group_bar_data = create_diverging_bar_data(
                    group_df, 
                    question_cols, 
                    question_text_map
                )
                group_bar_data['Group'] = group_value
                bio_data.append(group_bar_data)
            
            if bio_data:
                combined_bio_data = pd.concat(bio_data, ignore_index=True)
                sheet_name = f'By {bio_col}'[:31]  # Excel sheet name limit
                combined_bio_data.to_excel(writer, sheet_name=sheet_name, index=False)
                viz_sheets.append((sheet_name, bio_col))
    
    # By dimension subscores if available
    if hasattr(config, 'dimension_groups'):
        dimension_data = []
        for dimension_name, questions in config.dimension_groups.items():
            dim_cols = [f'Q{q}' for q in questions if f'Q{q}' in df.columns]
            if dim_cols:
                dim_bar_data = create_diverging_bar_data(df, dim_cols, question_text_map)
                dim_bar_data['Dimension'] = dimension_name
                dimension_data.append(dim_bar_data)
        
        if dimension_data:
            combined_dim_data = pd.concat(dimension_data, ignore_index=True)
            combined_dim_data.to_excel(writer, sheet_name='By Dimension', index=False)
            viz_sheets.append(('By Dimension', 'dimension'))
    
    return viz_sheets


def create_relative_risk_sheet(writer, df, bio_columns, config):
    """Create sheet with relative risk calculations, sorted by highest RR."""
    profiles = config.get_profile_list()
    
    rr_data = []
    
    for profile in profiles:
        profile_col = f'Profile_{profile}'
        if profile_col not in df.columns:
            continue
            
        for bio_col in bio_columns:
            if bio_col not in df.columns:
                continue
                
            rr_results = calculate_relative_risk(df, profile_col, bio_col)
            
            for result in rr_results:
                rr_data.append({
                    'Profile': profile,
                    'Biographical_Variable': bio_col,
                    'Reference_Group': result['reference_group'],
                    'Comparison_Group': result['comparison_group'],
                    'Relative_Risk': result['relative_risk'],
                    'Risk_Difference': result['risk_difference'],
                    'Reference_N': result['reference_n'],
                    'Comparison_N': result['comparison_n'],
                    'Reference_Rate': result['reference_rate'],
                    'Comparison_Rate': result['comparison_rate']
                })
    
    if rr_data:
        rr_df = pd.DataFrame(rr_data)
        # Sort by highest relative risk
        rr_df = rr_df.sort_values('Relative_Risk', ascending=False)
        rr_df.to_excel(writer, sheet_name='Relative Risk', index=False)
        return 'Relative Risk'
    
    return None


def add_diverging_bar_charts(wb, viz_sheets, config):
    """Add diverging stacked bar charts to visualization sheets."""
    for sheet_name, viz_type in viz_sheets:
        if sheet_name not in wb.sheetnames:
            continue
            
        ws = wb[sheet_name]
        
        # Find the data range
        max_row = ws.max_row
        if max_row < 2:
            continue
        
        # Create chart for each group (if grouped data)
        if viz_type == 'overall':
            create_single_diverging_chart(ws, 2, max_row, config)
        elif viz_type == 'dimension':
            create_dimension_charts(ws, max_row, config)
        else:
            create_grouped_charts(ws, max_row, viz_type)


def create_single_diverging_chart(ws, start_row, end_row, config):
    """Create a single diverging bar chart."""
    chart = BarChart()
    chart.type = "bar"
    chart.style = 10
    chart.title = "Response Distribution (Diverging Stacked Bar)"
    chart.y_axis.title = "Questions"
    chart.x_axis.title = "Percentage"
    chart.height = max(10, (end_row - start_row + 1) * 0.5)
    chart.width = 20
    
    # Data for disagree categories (negative)
    disagree_data = Reference(ws, min_col=3, min_row=start_row-1, max_row=end_row, max_col=4)
    chart.add_data(disagree_data, titles_from_data=True)
    
    # Data for agree categories (positive)
    agree_data = Reference(ws, min_col=5, min_row=start_row-1, max_row=end_row, max_col=6)
    chart.add_data(agree_data, titles_from_data=True)
    
    # Categories (questions)
    cats = Reference(ws, min_col=1, min_row=start_row, max_row=end_row)
    chart.set_categories(cats)
    
    # Place chart
    ws.add_chart(chart, f"J2")


def create_dimension_charts(ws, max_row, config):
    """Create separate charts for each dimension."""
    # Group by dimension and create charts
    pass  # Implementation for dimension-specific charts


def create_grouped_charts(ws, max_row, group_col):
    """Create charts grouped by biographical variable."""
    pass  # Implementation for grouped charts


def add_relative_risk_charts(wb, sheet_name):
    """Add bar charts showing relative risk comparisons."""
    if sheet_name not in wb.sheetnames:
        return
    
    ws = wb[sheet_name]
    max_row = ws.max_row
    
    if max_row < 2:
        return
    
    # Create bar chart for relative risk
    chart = BarChart()
    chart.type = "col"
    chart.style = 11
    chart.title = "Relative Risk by Group (Sorted Highest to Lowest)"
    chart.y_axis.title = "Relative Risk"
    chart.x_axis.title = "Comparison Group"
    chart.height = 15
    chart.width = 25
    
    # RR data is in column E (5th column)
    data = Reference(ws, min_col=5, min_row=1, max_row=min(max_row, 20))  # Limit to top 20
    chart.add_data(data, titles_from_data=True)
    
    # Categories from Comparison_Group column
    cats = Reference(ws, min_col=4, min_row=2, max_row=min(max_row, 20))
    chart.set_categories(cats)
    
    ws.add_chart(chart, "L2")


def format_workbook(wb):
    """Apply formatting to all sheets in workbook."""
    
    # Define styles
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    
    tier3_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    tier2_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    tier1_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        # Format headers
        if ws.max_row > 0:
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Add conditional formatting for tier sheets
        if sheet_name in ['Tier 3', 'Tier 2', 'Tier 1']:
            format_tier_sheet(ws, sheet_name)
        
        # Format Control Panel
        if sheet_name == 'Control Panel':
            format_control_panel(ws, wb)
        
        # Format Relative Risk sheet
        if sheet_name == 'Relative Risk':
            format_relative_risk_sheet(ws)


def format_tier_sheet(ws, tier_name):
    """Apply tier-specific formatting."""
    if tier_name == 'Tier 3':
        fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    elif tier_name == 'Tier 2':
        fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    else:
        fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    
    # Highlight rank column
    if ws.max_row > 1:
        for row in range(2, ws.max_row + 1):
            ws.cell(row=row, column=1).fill = fill
            ws.cell(row=row, column=1).font = Font(bold=True)


def format_control_panel(ws, wb):
    """Format the control panel with dropdowns and styling."""
    # Style the title
    ws['A1'].font = Font(bold=True, size=14, color="366092")
    
    # Get profile and bio column lists
    try:
        analysis_sheet = wb['Analysis']
        
        # Find profile columns
        profile_cols = [cell.value for cell in analysis_sheet[1] if cell.value and 'Profile_' in str(cell.value)]
        profiles = [col.replace('Profile_', '') for col in profile_cols]
        
        # Find bio columns - look for Counselor and year_in_hs
        bio_cols = []
        for cell in analysis_sheet[1]:
            if cell.value in ['Counselor', 'year_in_hs']:
                bio_cols.append(cell.value)
        
        # Add data validation for profile selection (cell B3)
        if profiles and ws.max_row >= 3:
            profile_dv = DataValidation(type="list", formula1=f'"{",".join(profiles)}"', allow_blank=False)
            profile_dv.error = 'Please select a valid profile'
            profile_dv.errorTitle = 'Invalid Profile'
            ws.add_data_validation(profile_dv)
            profile_dv.add(ws['B3'])
            ws['B3'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        # Add data validation for bio variable selection (cell B5)
        if bio_cols and ws.max_row >= 5:
            bio_dv = DataValidation(type="list", formula1=f'"{",".join(bio_cols)}"', allow_blank=False)
            bio_dv.error = 'Please select a valid biographical variable'
            bio_dv.errorTitle = 'Invalid Variable'
            ws.add_data_validation(bio_dv)
            bio_dv.add(ws['B5'])
            ws['B5'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        
        # Bold the labels
        for row in [3, 5]:
            if ws.max_row >= row:
                ws.cell(row=row, column=1).font = Font(bold=True)
        
    except Exception as e:
        print(f"Warning: Could not add data validation to Control Panel: {e}")


def format_relative_risk_sheet(ws):
    """Format relative risk sheet with conditional formatting."""
    from openpyxl.formatting.rule import ColorScaleRule
    
    if ws.max_row < 2:
        return
    
    # Find the Relative_Risk column (column E)
    rr_col = 'E'
    
    # Add color scale formatting for RR values
    color_scale = ColorScaleRule(
        start_type='num', start_value=0.5, start_color='63BE7B',  # Green for low RR
        mid_type='num', mid_value=1, mid_color='FFFFFF',          # White for RR = 1
        end_type='num', end_value=3, end_color='F8696B'           # Red for high RR
    )
    
    ws.conditional_formatting.add(f'{rr_col}2:{rr_col}{ws.max_row}', color_scale)
    
    # Bold high RR values (> 2.0)
    for row in range(2, ws.max_row + 1):
        cell = ws[f'{rr_col}{row}']
        if cell.value and isinstance(cell.value, (int, float)) and cell.value > 2.0:
            cell.font = Font(bold=True, color="C00000")
        
        # Format as number with 2 decimals
        if cell.value and isinstance(cell.value, (int, float)):
            cell.number_format = '0.00'
    
    # Format rate columns as percentages
    for col in ['I', 'J']:  # Reference_Rate and Comparison_Rate columns
        for row in range(2, ws.max_row + 1):
            cell = ws[f'{col}{row}']
            if cell.value and isinstance(cell.value, (int, float)):
                cell.number_format = '0.0%'