from io import BytesIO
import pandas as pd
from flask import session

from app.scripts.attendance.jupiter.process import process_local_file as process_jupiter
from app.scripts.attendance.jupiter.enhanced_analysis import (
    calculate_composite_score,
    calculate_mtss_tiers,
    calculate_rolling_averages,
    calculate_trend_metrics,
    find_cutting_together_pairs,
    analyze_by_teacher_period_course,
    analyze_by_department,
    analyze_by_period,
    get_department_from_course_code
)


def main():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"

    # Get processed attendance data
    student_period_attendance_df = process_jupiter()

    # Calculate days into semester
    unique_dates = student_period_attendance_df['Date'].nunique()
    days_into_semester = unique_dates

    f = BytesIO()
    writer = pd.ExcelWriter(f)

    # ========== EXISTING REPORTS (with enhancements) ==========
    
    # Raw cuts data
    cuts_df = student_period_attendance_df[student_period_attendance_df["cutting?"]]
    cuts_df.to_excel(writer, sheet_name="cuts_raw", index=False)

    # Cuts pivot with grades and teachers
    cuts_pvt = pd.pivot_table(
        cuts_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc='count',
    ).fillna("")
    cuts_pvt.columns = [f"Pd_{col}_cuts" for col in cuts_pvt.columns] 
    cuts_pvt = cuts_pvt.reset_index()

    class_grades_pvt = pd.pivot_table(
        student_period_attendance_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="ClassGrade",
        aggfunc="max",
    ).fillna("")
    class_grades_pvt.columns = [f"Pd_{col}_Grade" for col in class_grades_pvt.columns] 
    class_grades_pvt = class_grades_pvt.reset_index()

    teacher_pvt = pd.pivot_table(
        student_period_attendance_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc="max",
    ).fillna("")
    teacher_pvt.columns = [f"Pd_{col}_Teacher" for col in teacher_pvt.columns] 
    teacher_pvt = teacher_pvt.reset_index()

    cuts_pvt = cuts_pvt.merge(class_grades_pvt, on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"], how="right")
    cuts_pvt = cuts_pvt.merge(teacher_pvt, on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"], how="right")

    num_of_cuts_df = student_period_attendance_df[
        ["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs", "num_of_cuts"]
    ].drop_duplicates()
    cuts_pvt = num_of_cuts_df.merge(
        cuts_pvt,
        on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        how="right",
    )
    cuts_pvt = cuts_pvt.sort_values(by=["num_of_cuts"], ascending=[False])
    cuts_pvt.to_excel(writer, sheet_name="cuts", index=False)

    # Attendance errors
    attendance_errors_df = student_period_attendance_df[
        student_period_attendance_df["attd_error"]
    ]
    cols = [
        "Teacher",
        "Date",
        "Course",
        "Section",
        "Pd",
        "Type",
        "LastName",
        "FirstName",
    ]
    attendance_errors_df = attendance_errors_df[cols].sort_values(
        by=["Teacher", "Pd", "Course", "Section"]
    )
    attendance_errors_df.to_excel(writer, sheet_name="attd_errors", index=False)

    # Cutting by teacher by class
    cutting_by_teacher_by_class_pvt = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Teacher", "Course", "Section", "Pd"],
            columns=["Type", "cutting?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    cutting_by_teacher_by_class_pvt.to_excel(
        writer, sheet_name="attd_by_teacher_and_course"
    )

    # Attendance by day and period
    attd_by_day_and_pd = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Date", "Pd"],
            columns=["Type", "cutting?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    attd_by_day_and_pd.to_excel(writer, sheet_name="attd_by_date_and_period")

    # Attendance by date
    attd_by_date = (
        pd.pivot_table(
            student_period_attendance_df,
            index=["Date"],
            columns=["Type", "cutting?","late_to_school?"],
            values="StudentID",
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    attd_by_date.to_excel(writer, sheet_name="attd_by_date")

    # Late to school
    late_to_school_df = student_period_attendance_df[
        student_period_attendance_df["late_to_school?"]
        & (~student_period_attendance_df["Type"].isin(["tardy"]))
    ]
    late_to_school_pvt = pd.pivot_table(
        late_to_school_df,
        index=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        columns="Pd",
        values="Teacher",
        aggfunc="count",
    ).fillna("")
    late_to_school_pvt = late_to_school_pvt.reset_index()

    num_of_late_to_school_df = student_period_attendance_df[
        [
            "StudentID",
            "LastName",
            "FirstName",
            "Counselor",
            "year_in_hs",
            "num_of_late_to_school",
        ]
    ].drop_duplicates()
    late_to_school_pvt = num_of_late_to_school_df.merge(
        late_to_school_pvt,
        on=["StudentID", "LastName", "FirstName", "Counselor", "year_in_hs"],
        how="right",
    )
    late_to_school_pvt = late_to_school_pvt.sort_values(
        by=["num_of_late_to_school"], ascending=[False]
    )
    late_to_school_pvt.to_excel(writer, sheet_name="late_to_school", index=False)

    # ========== NEW ENHANCED REPORTS ==========
    
    # 1. Student Trend Analysis with MTSS Tiers
    student_summary = student_period_attendance_df.groupby(
        ['StudentID', 'LastName', 'FirstName', 'Counselor', 'year_in_hs']
    ).agg({
        'cutting?': 'sum',
        'num_of_cuts': 'first',
        'num_of_days_absent': 'first',
        'num_of_late_to_school': 'first',
        'Date': 'nunique'
    }).reset_index()
    
    student_summary.columns = ['StudentID', 'LastName', 'FirstName', 'Counselor', 
                                'year_in_hs', 'total_cuts', 'num_of_cuts', 
                                'total_absences', 'total_tardies', 'days_with_data']
    
    # Calculate composite score
    student_summary['composite_score'] = student_summary.apply(
        lambda x: calculate_composite_score(x['total_cuts'], x['total_absences'], x['total_tardies']),
        axis=1
    )
    
    # Add MTSS tiers
    student_summary = calculate_mtss_tiers(student_summary, 'composite_score')
    
    # Add rolling averages
    rolling_avg_df = calculate_rolling_averages(student_period_attendance_df, window_days=20)
    student_summary = student_summary.merge(rolling_avg_df, on='StudentID', how='left')
    
    # Add trend metrics
    trend_df = calculate_trend_metrics(student_period_attendance_df, days_into_semester)
    student_summary = student_summary.merge(trend_df, on='StudentID', how='left')
    
    # Calculate projection rates
    student_summary['days_into_semester'] = days_into_semester
    student_summary['days_remaining'] = 90 - days_into_semester
    
    # Sort by composite score
    student_summary = student_summary.sort_values('composite_score', ascending=False)
    
    student_summary.to_excel(writer, sheet_name='student_trends_mtss', index=False)
    
    # 2. High Priority Students (Tier 2 & 3)
    high_priority = student_summary[student_summary['MTSS_Tier'].isin(['Tier 2', 'Tier 3'])].copy()
    high_priority = high_priority.sort_values(['MTSS_Tier', 'composite_score'], ascending=[True, False])
    high_priority.to_excel(writer, sheet_name='high_priority_students', index=False)
    
    # 3. Students Showing Acceleration
    if not trend_df.empty:
        accelerating = student_summary[student_summary['trend_flag'] == 'Accelerating'].copy()
        accelerating = accelerating.sort_values('acceleration', ascending=False)
        accelerating.to_excel(writer, sheet_name='accelerating_concerns', index=False)
    
    # 4. Cutting Together Analysis
    cutting_pairs = find_cutting_together_pairs(student_period_attendance_df, min_occurrences=3)
    if not cutting_pairs.empty:
        # Add student names
        student_names = student_period_attendance_df[['StudentID', 'LastName', 'FirstName']].drop_duplicates()
        cutting_pairs = cutting_pairs.merge(
            student_names.rename(columns={'StudentID': 'Student1', 'LastName': 'LastName1', 'FirstName': 'FirstName1'}),
            on='Student1',
            how='left'
        )
        cutting_pairs = cutting_pairs.merge(
            student_names.rename(columns={'StudentID': 'Student2', 'LastName': 'LastName2', 'FirstName': 'FirstName2'}),
            on='Student2',
            how='left'
        )
        
        # Reorder columns
        cols = ['Student1', 'LastName1', 'FirstName1', 'Student2', 'LastName2', 'FirstName2',
                'times_absent_together', 'courses', 'teachers']
        cutting_pairs = cutting_pairs[cols]
        cutting_pairs.to_excel(writer, sheet_name='cutting_together', index=False)
    
    # 5. Teacher/Course Analysis
    class_analysis = analyze_by_teacher_period_course(student_period_attendance_df)
    class_analysis = class_analysis.sort_values('composite_score', ascending=False)
    class_analysis.to_excel(writer, sheet_name='teacher_course_analysis', index=False)
    
    # 6. Department Analysis
    dept_analysis = analyze_by_department(class_analysis)
    dept_analysis.to_excel(writer, sheet_name='department_analysis', index=False)
    
    # 7. Period Analysis
    period_analysis = analyze_by_period(student_period_attendance_df)
    period_analysis.to_excel(writer, sheet_name='period_analysis', index=False)
    
    # 8. Classes Needing Support (highest concern scores)
    classes_needing_support = class_analysis.nlargest(50, 'composite_score').copy()
    classes_needing_support.to_excel(writer, sheet_name='classes_needing_support', index=False)
    
    # 9. Weekly Trends
    student_period_attendance_df['week_number'] = pd.to_datetime(student_period_attendance_df['Date']).dt.isocalendar().week
    
    weekly_summary = []
    for week, group in student_period_attendance_df.groupby('week_number'):
        week_dates = group['Date'].unique()
        num_days = len(week_dates)
        
        cuts = group['cutting?'].sum()
        absences = group[~group['in_school?']].groupby(['StudentID', 'Date']).ngroups
        tardies = group[group['Type'] == 'tardy'].shape[0]
        lates_to_school = group['late_to_school?'].sum()
        
        composite = calculate_composite_score(cuts, absences, tardies)
        
        weekly_summary.append({
            'week_number': week,
            'start_date': min(week_dates),
            'end_date': max(week_dates),
            'school_days': num_days,
            'total_cuts': cuts,
            'total_absences': absences,
            'total_tardies': tardies,
            'total_late_to_school': lates_to_school,
            'composite_score': composite,
            'avg_cuts_per_day': cuts / num_days if num_days > 0 else 0,
            'avg_composite_per_day': composite / num_days if num_days > 0 else 0
        })
    
    weekly_df = pd.DataFrame(weekly_summary).sort_values('week_number')
    weekly_df.to_excel(writer, sheet_name='weekly_trends', index=False)
    
    # 10. Monthly Trends
    student_period_attendance_df['month'] = pd.to_datetime(student_period_attendance_df['Date']).dt.to_period('M')
    
    monthly_summary = []
    for month, group in student_period_attendance_df.groupby('month'):
        month_dates = group['Date'].unique()
        num_days = len(month_dates)
        
        cuts = group['cutting?'].sum()
        absences = group[~group['in_school?']].groupby(['StudentID', 'Date']).ngroups
        tardies = group[group['Type'] == 'tardy'].shape[0]
        lates_to_school = group['late_to_school?'].sum()
        
        composite = calculate_composite_score(cuts, absences, tardies)
        
        monthly_summary.append({
            'month': str(month),
            'start_date': min(month_dates),
            'end_date': max(month_dates),
            'school_days': num_days,
            'total_cuts': cuts,
            'total_absences': absences,
            'total_tardies': tardies,
            'total_late_to_school': lates_to_school,
            'composite_score': composite,
            'avg_cuts_per_day': cuts / num_days if num_days > 0 else 0,
            'avg_composite_per_day': composite / num_days if num_days > 0 else 0
        })
    
    monthly_df = pd.DataFrame(monthly_summary).sort_values('month')
    monthly_df.to_excel(writer, sheet_name='monthly_trends', index=False)
    
    # 11. Summary Dashboard
    dashboard_data = {
        'Metric': [
            'Total School Days',
            'Days into Semester',
            'Days Remaining',
            'Total Students',
            'Total Cuts',
            'Total Absences',
            'Total Tardies',
            'Total Late to School',
            'Composite Score',
            'Tier 3 Students (Top 5%)',
            'Tier 2 Students (Next 15%)',
            'Tier 1 Students (Remaining 80%)',
            'Students Accelerating',
            'Avg Cuts per Day',
            'Avg Composite per Day'
        ],
        'Value': [
            days_into_semester,
            days_into_semester,
            90 - days_into_semester,
            student_summary['StudentID'].nunique(),
            student_summary['total_cuts'].sum(),
            student_summary['total_absences'].sum(),
            student_summary['total_tardies'].sum(),
            student_period_attendance_df['late_to_school?'].sum(),
            student_summary['composite_score'].sum(),
            len(student_summary[student_summary['MTSS_Tier'] == 'Tier 3']),
            len(student_summary[student_summary['MTSS_Tier'] == 'Tier 2']),
            len(student_summary[student_summary['MTSS_Tier'] == 'Tier 1']),
            len(student_summary[student_summary['trend_flag'] == 'Accelerating']) if 'trend_flag' in student_summary.columns else 0,
            student_summary['total_cuts'].sum() / days_into_semester if days_into_semester > 0 else 0,
            student_summary['composite_score'].sum() / days_into_semester if days_into_semester > 0 else 0
        ]
    }
    
    dashboard_df = pd.DataFrame(dashboard_data)
    dashboard_df.to_excel(writer, sheet_name='dashboard_summary', index=False)

    writer.close()
    f.seek(0)

    download_name = f"JupiterCutReport-{year_and_semester}.xlsx"
    return f, download_name