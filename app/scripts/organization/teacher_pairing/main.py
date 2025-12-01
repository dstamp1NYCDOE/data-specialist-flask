import pandas as pd
from collections import defaultdict
import io
from flask import session
import app.scripts.utils as utils
from app.scripts import files_df


def main(request, form):
    """
    Flask route handler for generating teacher groupings for PD session.
    
    Parameters:
    -----------
    request : Flask request object
    form : Flask form object with:
        - 'teacher_emails' field (textarea, one email per line)
        - 'group_size' field (integer, desired group size)
    
    Returns:
    --------
    Excel file as download with multiple sheets
    """
    # Get teacher emails from form (one per line)
    teacher_emails_input = form.get('teacher_emails', '').strip()
    teacher_emails = [email.strip().lower() for email in teacher_emails_input.split('\n') if email.strip()]
    
    # Get desired group size (default to 2 for backwards compatibility)
    group_size = int(form.get('group_size', 2))
    
    if not teacher_emails:
        return "Error: Please enter at least one teacher email address"
    
    if group_size < 2:
        return "Error: Group size must be at least 2"
    
    # Get the data
    schedule_df = get_teacher_student_schedule()
    
    # Filter to only PD attendees
    schedule_df = schedule_df[schedule_df['TeacherEmail'].isin(teacher_emails)]
    
    if len(schedule_df) == 0:
        return f"Error: No matching teachers found for the provided emails. Check that emails match the format in the system."
    
    # Get all unique teachers who were found
    found_teachers = schedule_df['TeacherEmail'].unique().tolist()
    missing_teachers = [email for email in teacher_emails if email not in found_teachers]
    
    # Find shared students
    shared_students = find_shared_students(schedule_df)
    
    # Create teacher matrix showing shared student counts
    teacher_matrix = create_teacher_matrix(schedule_df, shared_students)
    
    # Create groupings
    groupings = create_teacher_groups(shared_students, schedule_df, group_size)
    
    # Generate Excel file with multiple sheets
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Groupings
        if groupings:
            groupings_df = create_groupings_dataframe(groupings)
            groupings_df.to_excel(writer, sheet_name='Groupings', index=False)
        else:
            pd.DataFrame({'Message': ['No groupings could be created']}).to_excel(
                writer, sheet_name='Groupings', index=False
            )
        
        # Sheet 2: Teacher Matrix
        teacher_matrix.to_excel(writer, sheet_name='Teacher Matrix')
        
        # Sheet 3: Missing Teachers Info
        missing_info = create_missing_teachers_info(missing_teachers)
        missing_info.to_excel(writer, sheet_name='Missing Teachers', index=False)
        
        # Sheet 4: Summary Stats
        summary_stats = create_summary_stats_flexible(
            teacher_emails, found_teachers, missing_teachers, 
            groupings, shared_students, group_size
        )
        summary_stats.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 5: All Shared Students (with teacher count)
        all_shared_students_df = create_all_shared_students_list(shared_students, schedule_df)
        all_shared_students_df.to_excel(writer, sheet_name='All Shared Students', index=False)
        
        # Sheet 6: Students by Group (wide format)
        students_by_group_wide = create_students_by_group_wide(groupings, schedule_df)
        students_by_group_wide.to_excel(writer, sheet_name='Students by Group (Wide)', index=False)
        
        # Sheet 7: Students by Group (long format)
        students_by_group_long = create_students_by_group_long(groupings, schedule_df)
        students_by_group_long.to_excel(writer, sheet_name='Students by Group (Long)', index=False)
        
        # Sheet 8: Teacher Group Assignments
        teacher_assignments = create_teacher_assignments(groupings)
        teacher_assignments.to_excel(writer, sheet_name='Teacher Group Assignments', index=False)
    
    excel_data = output.getvalue()
    return excel_data


def create_teacher_groups(shared_students, schedule_df, group_size):
    """
    Create teacher groupings of specified size where teachers share students.
    Uses a greedy algorithm that prioritizes teachers with fewer pairing options.
    Avoids grouping co-teachers together unless necessary.
    Ensures all teachers are assigned to a group (even if undersized).
    
    Parameters:
    -----------
    shared_students : dict of students shared by multiple teachers
    schedule_df : DataFrame with teacher-student relationships
    group_size : int, desired number of teachers per group
    
    Returns:
    --------
    list of dicts with grouping information
    """
    # Get all unique teachers
    all_teachers = set(schedule_df['TeacherEmail'].unique())
    
    # Identify co-teacher pairs
    co_teacher_pairs = identify_co_teachers(schedule_df)
    
    # Build graph of teacher connections (who shares students with whom)
    teacher_connections = defaultdict(lambda: defaultdict(list))
    
    for student_id, info in shared_students.items():
        teachers = info['teachers']
        # Connect all pairs of teachers who share this student
        for i in range(len(teachers)):
            for j in range(i + 1, len(teachers)):
                teacher_connections[teachers[i]][teachers[j]].append(student_id)
                teacher_connections[teachers[j]][teachers[i]].append(student_id)
    
    # Track used teachers and groups
    used_teachers = set()
    groupings = []
    
    # Main grouping loop
    while len(used_teachers) < len(all_teachers):
        available_teachers = all_teachers - used_teachers
        
        if not available_teachers:
            break
        
        # Find the best seed teacher (one with fewest remaining connections)
        seed_teacher = min(
            available_teachers,
            key=lambda t: len([p for p in teacher_connections[t].keys() if p in available_teachers])
        )
        
        # Build a group starting with this seed teacher
        group = [seed_teacher]
        group_shared_students = set()
        
        # Try to fill the group to desired size
        while len(group) < group_size and len(available_teachers) > len(group):
            # Find best candidate to add to group
            candidates = []
            
            for candidate in available_teachers:
                if candidate in group:
                    continue
                
                # Calculate how many students this candidate shares with the group
                shared_with_group = set()
                is_co_teacher_with_any = False
                
                for group_member in group:
                    if candidate in teacher_connections[group_member]:
                        shared_with_group.update(teacher_connections[group_member][candidate])
                    
                    # Check if co-teachers
                    pair = tuple(sorted([candidate, group_member]))
                    if pair in co_teacher_pairs:
                        is_co_teacher_with_any = True
                
                if shared_with_group:  # Only consider if they share students
                    # Count remaining options for this candidate
                    remaining_options = len([
                        t for t in teacher_connections[candidate].keys() 
                        if t in available_teachers and t not in group
                    ])
                    
                    candidates.append({
                        'teacher': candidate,
                        'shared_students': shared_with_group,
                        'shared_count': len(shared_with_group),
                        'remaining_options': remaining_options,
                        'is_co_teacher': is_co_teacher_with_any
                    })
            
            if not candidates:
                break
            
            # Sort candidates: prioritize those with fewer options, avoid co-teachers, prefer more shared students
            candidates.sort(key=lambda x: (x['remaining_options'], x['is_co_teacher'], -x['shared_count']))
            
            best_candidate = candidates[0]
            group.append(best_candidate['teacher'])
            group_shared_students.update(best_candidate['shared_students'])
        
        # If we couldn't form a group of desired size, check if we should add remaining teachers
        if len(group) < group_size:
            remaining = available_teachers - set(group)
            if remaining and len(remaining) < group_size:
                # Add all remaining teachers to this group rather than leaving them unpaired
                for teacher in remaining:
                    # Check if they share any students with the group
                    shares_students = False
                    for group_member in group:
                        if teacher in teacher_connections[group_member]:
                            group_shared_students.update(teacher_connections[group_member][teacher])
                            shares_students = True
                    
                    if shares_students or len(remaining) == len(available_teachers) - len(group):
                        group.append(teacher)
        
        # Create grouping record
        if group:
            grouping = create_grouping_record(group, group_shared_students, schedule_df, shared_students, co_teacher_pairs)
            groupings.append(grouping)
            used_teachers.update(group)
    
    return groupings


def create_grouping_record(group, group_shared_students, schedule_df, shared_students, co_teacher_pairs):
    """
    Create a record for a teacher group with all relevant information.
    """
    # Get teacher info
    teacher_info = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    student_info = schedule_df[['StudentID', 'StudentName']].drop_duplicates().set_index('StudentID')['StudentName'].to_dict()
    
    grouping = {
        'group_id': None,  # Will be set later
        'group_size': len(group),
        'teachers': group,
        'teacher_names': [teacher_info.get(t, 'Unknown') for t in group],
        'shared_students': list(group_shared_students),
        'shared_students_count': len(group_shared_students),
    }
    
    # Check if any pair in the group are co-teachers
    has_co_teachers = False
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            pair = tuple(sorted([group[i], group[j]]))
            if pair in co_teacher_pairs:
                has_co_teachers = True
                break
    
    grouping['has_co_teachers'] = has_co_teachers
    
    # Select representative students (up to 3)
    if group_shared_students:
        student_priorities = []
        for student_id in group_shared_students:
            if student_id in shared_students:
                num_teachers = len(shared_students[student_id]['teachers'])
                student_priorities.append((student_id, num_teachers))
        
        student_priorities.sort(key=lambda x: x[1])
        representative_students = [s[0] for s in student_priorities[:3]]
        
        grouping['representative_student_ids'] = representative_students
        grouping['representative_student_names'] = [
            student_info.get(s, 'Unknown') for s in representative_students
        ]
    else:
        grouping['representative_student_ids'] = []
        grouping['representative_student_names'] = []
    
    return grouping


def create_groupings_dataframe(groupings):
    """
    Convert groupings list into a DataFrame for Excel export.
    """
    rows = []
    
    for idx, grouping in enumerate(groupings, 1):
        # Create base row
        row = {
            'Group_ID': idx,
            'Group_Size': grouping['group_size'],
            'Has_Co_Teachers': grouping['has_co_teachers'],
            'Shared_Students_Count': grouping['shared_students_count'],
        }
        
        # Add teacher columns (dynamically based on group size)
        for i, (email, name) in enumerate(zip(grouping['teachers'], grouping['teacher_names']), 1):
            row[f'Teacher{i}_Name'] = name
            row[f'Teacher{i}_Email'] = email
        
        # Add representative student columns
        for i, (student_id, student_name) in enumerate(
            zip(grouping['representative_student_ids'], grouping['representative_student_names']), 1
        ):
            row[f'Student{i}_ID'] = student_id
            row[f'Student{i}_Name'] = student_name
        
        # Add all shared students as comma-separated list
        row['All_Shared_Students'] = ', '.join([str(s) for s in grouping['shared_students']])
        
        rows.append(row)
    
    return pd.DataFrame(rows)


def create_summary_stats_flexible(teacher_emails, found_teachers, missing_teachers, 
                                  groupings, shared_students, group_size):
    """
    Create summary statistics for the grouping process.
    """
    total_teachers_in_groups = sum(g['group_size'] for g in groupings)
    
    stats = [
        {'Metric': 'Desired group size', 'Value': group_size},
        {'Metric': 'Total teachers provided', 'Value': len(teacher_emails)},
        {'Metric': 'Teachers found in system', 'Value': len(found_teachers)},
        {'Metric': 'Teachers NOT found in system', 'Value': len(missing_teachers)},
        {'Metric': 'Teachers assigned to groups', 'Value': total_teachers_in_groups},
        {'Metric': 'Total groups created', 'Value': len(groupings)},
        {'Metric': 'Students with 2+ PD teachers', 'Value': len(shared_students)},
    ]
    
    # Add group size distribution
    size_distribution = defaultdict(int)
    for g in groupings:
        size_distribution[g['group_size']] += 1
    
    for size in sorted(size_distribution.keys()):
        stats.append({
            'Metric': f'Groups of size {size}',
            'Value': size_distribution[size]
        })
    
    return pd.DataFrame(stats)


def create_students_by_group_wide(groupings, schedule_df):
    """
    Create a list of students for each group (wide format).
    """
    rows = []
    
    for idx, grouping in enumerate(groupings, 1):
        for student_id in grouping['shared_students']:
            student_row = schedule_df[schedule_df['StudentID'] == student_id].iloc[0]
            student_name = student_row['StudentName']
            
            if ', ' in student_name:
                last_name, first_name = student_name.split(', ', 1)
            else:
                last_name = student_name
                first_name = ''
            
            row = {
                'Group_ID': idx,
                'StudentID': student_id,
                'LastName': last_name,
                'FirstName': first_name,
            }
            
            # Add all teachers in the group
            for i, (email, name) in enumerate(zip(grouping['teachers'], grouping['teacher_names']), 1):
                row[f'Teacher{i}_Name'] = name
                row[f'Teacher{i}_Email'] = email
            
            rows.append(row)
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['Group_ID', 'LastName', 'FirstName'])
    
    return df


def create_students_by_group_long(groupings, schedule_df):
    """
    Create a list of students for each group (long format).
    Each student appears once per teacher in their group.
    """
    rows = []
    
    for idx, grouping in enumerate(groupings, 1):
        for student_id in grouping['shared_students']:
            student_row = schedule_df[schedule_df['StudentID'] == student_id].iloc[0]
            student_name = student_row['StudentName']
            
            if ', ' in student_name:
                last_name, first_name = student_name.split(', ', 1)
            else:
                last_name = student_name
                first_name = ''
            
            # Create a row for each teacher in the group
            for email, name in zip(grouping['teachers'], grouping['teacher_names']):
                # Get other teachers in group
                other_teachers = [n for n in grouping['teacher_names'] if n != name]
                
                rows.append({
                    'Group_ID': idx,
                    'StudentID': student_id,
                    'LastName': last_name,
                    'FirstName': first_name,
                    'TeacherName': name,
                    'TeacherEmail': email,
                    'Other_Teachers_In_Group': ', '.join(other_teachers)
                })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['Group_ID', 'TeacherName', 'LastName', 'FirstName'])
    
    return df


def create_missing_teachers_info(missing_teachers):
    """
    Create information about teachers not found in the system.
    """
    if not missing_teachers:
        return pd.DataFrame({'Message': ['All teachers were found in the system']})
    
    info = []
    for email in missing_teachers:
        info.append({
            'teacher_email': email,
            'status': 'Not found in system'
        })
    
    return pd.DataFrame(info)


# Keep existing helper functions
def get_teacher_student_schedule():
    """Get teacher-student-course relationships from student schedules."""
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    student_schedules_df = utils.return_file_as_df(filename).fillna("")
    
    filename = utils.return_most_recent_report_by_semester(
        files_df, "6_42", year_and_semester=year_and_semester
    )
    teacher_reference_df = utils.return_file_as_df(filename)
    
    teacher_reference_df["TeacherName"] = (
        teacher_reference_df["LastName"]
        + " "
        + teacher_reference_df["FirstName"].str[0]
    )
    teacher_reference_df["Mail"] = teacher_reference_df["Mail"].str.lower().str.strip()
    
    schedule_with_teachers = process_student_teacher_pairs(student_schedules_df, teacher_reference_df)
    
    return schedule_with_teachers


def process_student_teacher_pairs(student_schedules_df, teacher_reference_df):
    """Process student schedules to handle both Teacher1 and Teacher2."""
    student_schedules_df["StudentName"] = (
        student_schedules_df["LastName"] + ", " + student_schedules_df["FirstName"]
    )
    
    teacher1_df = student_schedules_df[
        ["StudentID", "StudentName", "Course", "Section", "Teacher1"]
    ].copy()
    teacher1_df = teacher1_df.rename(columns={"Teacher1": "Teacher"})
    
    teacher2_df = student_schedules_df[
        student_schedules_df["Teacher2"].notna() & (student_schedules_df["Teacher2"] != "")
    ][["StudentID", "StudentName", "Course", "Section", "Teacher2"]].copy()
    teacher2_df = teacher2_df.rename(columns={"Teacher2": "Teacher"})
    
    all_teachers_df = pd.concat([teacher1_df, teacher2_df], ignore_index=True)
    
    schedule_with_teachers = all_teachers_df.merge(
        teacher_reference_df[["Teacher", "Mail", "TeacherName"]],
        on="Teacher",
        how="inner"
    )
    
    schedule_with_teachers = schedule_with_teachers.rename(columns={"Mail": "TeacherEmail"})
    schedule_with_teachers = schedule_with_teachers[
        ["StudentID", "StudentName", "TeacherEmail", "TeacherName", "Course", "Section"]
    ]
    
    schedule_with_teachers = schedule_with_teachers.drop_duplicates()
    
    return schedule_with_teachers


def find_shared_students(schedule_df):
    """Find all students who have multiple teachers from the schedule."""
    student_teachers = defaultdict(lambda: {'name': '', 'teachers': []})
    
    for _, row in schedule_df.iterrows():
        student_id = row['StudentID']
        if not student_teachers[student_id]['name']:
            student_teachers[student_id]['name'] = row['StudentName']
        if row['TeacherEmail'] not in student_teachers[student_id]['teachers']:
            student_teachers[student_id]['teachers'].append(row['TeacherEmail'])
    
    shared_students = {
        student_id: info
        for student_id, info in student_teachers.items() 
        if len(info['teachers']) >= 2
    }
    
    return shared_students


def create_teacher_matrix(schedule_df, shared_students):
    """Create an n x n matrix showing shared student counts between teachers."""
    teachers = sorted(schedule_df['TeacherEmail'].unique())
    teacher_names = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    teacher_labels = [f"{teacher_names.get(t, 'Unknown')} <{t}>" for t in teachers]
    
    matrix = pd.DataFrame(0, index=teacher_labels, columns=teacher_labels)
    
    for student_id, info in shared_students.items():
        teachers_list = info['teachers']
        for i in range(len(teachers_list)):
            for j in range(len(teachers_list)):
                if i != j:
                    teacher_i = teachers_list[i]
                    teacher_j = teachers_list[j]
                    label_i = f"{teacher_names.get(teacher_i, 'Unknown')} <{teacher_i}>"
                    label_j = f"{teacher_names.get(teacher_j, 'Unknown')} <{teacher_j}>"
                    matrix.loc[label_i, label_j] += 1
    
    return matrix


def identify_co_teachers(schedule_df):
    """Identify pairs of teachers who co-teach the same course/section."""
    co_teacher_pairs = set()
    
    for (course, section), group in schedule_df.groupby(['Course', 'Section']):
        teachers = group['TeacherEmail'].unique().tolist()
        
        if len(teachers) > 1:
            for i in range(len(teachers)):
                for j in range(i + 1, len(teachers)):
                    pair = tuple(sorted([teachers[i], teachers[j]]))
                    co_teacher_pairs.add(pair)
    
    return co_teacher_pairs


def create_all_shared_students_list(shared_students, schedule_df):
    """Create a list of all students with multiple teachers."""
    student_info = []
    
    for student_id, info in shared_students.items():
        student_name = info['name']
        if ', ' in student_name:
            last_name, first_name = student_name.split(', ', 1)
        else:
            last_name = student_name
            first_name = ''
        
        student_info.append({
            'StudentID': student_id,
            'LastName': last_name,
            'FirstName': first_name,
            'NumTeachers': len(info['teachers'])
        })
    
    df = pd.DataFrame(student_info)
    df = df.sort_values(['NumTeachers', 'LastName', 'FirstName'], ascending=[False, True, True])
    
    return df


def create_teacher_assignments(groupings):
    """
    Create a simple list of all teachers with their group assignments.
    
    Returns:
    --------
    DataFrame with Teacher_Name, Email_Address, Group_ID
    """
    rows = []
    
    for idx, grouping in enumerate(groupings, 1):
        for email, name in zip(grouping['teachers'], grouping['teacher_names']):
            rows.append({
                'Teacher_Name': name,
                'Email_Address': email,
                'Group_ID': idx
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['Group_ID', 'Teacher_Name'])
    
    return df