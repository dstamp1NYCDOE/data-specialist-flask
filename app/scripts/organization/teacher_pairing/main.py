import pandas as pd
from collections import defaultdict
import io
from flask import session
import app.scripts.utils as utils
from app.scripts import files_df


def main(request, form):
    """
    Flask route handler for generating teacher pairings for PD session.
    
    Parameters:
    -----------
    request : Flask request object
    form : Flask form object with 'teacher_emails' field (textarea, one email per line)
    
    Returns:
    --------
    Excel file as download with multiple sheets
    """
    # Get teacher emails from form (one per line)
    teacher_emails_input = form.get('teacher_emails', '').strip()
    teacher_emails = [email.strip().lower() for email in teacher_emails_input.split('\n') if email.strip()]
    
    if not teacher_emails:
        return "Error: Please enter at least one teacher email address"
    
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
    
    # Create pairings
    pairings, unpaired_teachers = create_teacher_pairs_with_unpaired(shared_students, schedule_df)
    
    # Generate Excel file with multiple sheets
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Pairings
        if pairings:
            pairings_df = pd.DataFrame(pairings)
            column_order = [
                'teacher1_name', 'teacher1_email', 
                'teacher2_name', 'teacher2_email',
                'are_co_teachers',
                'student1_id', 'student1_name',
                'student2_id', 'student2_name',
                'shared_students_count',
                'all_shared_students'
            ]
            pairings_df = pairings_df[column_order]
            pairings_df.to_excel(writer, sheet_name='Pairings', index=False)
        else:
            pd.DataFrame({'Message': ['No pairings could be created']}).to_excel(
                writer, sheet_name='Pairings', index=False
            )
        
        # Sheet 2: Teacher Matrix
        teacher_matrix.to_excel(writer, sheet_name='Teacher Matrix')
        
        # Sheet 3: Unpaired Teachers Debug Info
        unpaired_info = create_unpaired_debug_info(
            unpaired_teachers, missing_teachers, schedule_df, shared_students
        )
        unpaired_info.to_excel(writer, sheet_name='Unpaired Teachers', index=False)
        
        # Sheet 4: Summary Stats
        summary_stats = create_summary_stats(
            teacher_emails, found_teachers, missing_teachers, 
            pairings, unpaired_teachers, shared_students
        )
        summary_stats.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 5: All Shared Students (with teacher count)
        all_shared_students_df = create_all_shared_students_list(shared_students, schedule_df)
        all_shared_students_df.to_excel(writer, sheet_name='All Shared Students', index=False)
        
        # Sheet 6: Students by Pair (wide format - one row per student)
        students_by_pair_wide = create_students_by_pair_wide(pairings, schedule_df)
        students_by_pair_wide.to_excel(writer, sheet_name='Students by Pair (Wide)', index=False)
        
        # Sheet 7: Students by Pair (long format - one row per student-teacher)
        students_by_pair_long = create_students_by_pair_long(pairings, schedule_df)
        students_by_pair_long.to_excel(writer, sheet_name='Students by Pair (Long)', index=False)
    
    excel_data = output.getvalue()
    return excel_data


def get_teacher_student_schedule():
    """
    Get teacher-student-course relationships from student schedules.
    Simplified version that uses 1_01 (student schedules) and 6_42 (teacher reference).
    
    Returns:
    --------
    DataFrame with columns: StudentID, StudentName, TeacherEmail, TeacherName, Course, Section
    """
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    
    # Load student schedules (1_01) - has Course, Section, Teacher1, Teacher2
    filename = utils.return_most_recent_report_by_semester(
        files_df, "1_01", year_and_semester=year_and_semester
    )
    student_schedules_df = utils.return_file_as_df(filename).fillna("")
    
    # Load teacher reference (6_42) - has Teacher, Mail, FirstName, LastName
    filename = utils.return_most_recent_report_by_semester(
        files_df, "6_42", year_and_semester=year_and_semester
    )
    teacher_reference_df = utils.return_file_as_df(filename)
    
    # Create teacher name and normalize email
    teacher_reference_df["TeacherName"] = (
        teacher_reference_df["LastName"]
        + " "
        + teacher_reference_df["FirstName"].str[0]
    )
    teacher_reference_df["Mail"] = teacher_reference_df["Mail"].str.lower().str.strip()
    
    # Process student schedules to handle both Teacher1 and Teacher2
    schedule_with_teachers = process_student_teacher_pairs(student_schedules_df, teacher_reference_df)
    
    return schedule_with_teachers


def process_student_teacher_pairs(student_schedules_df, teacher_reference_df):
    """
    Melt student schedules so Teacher1 and Teacher2 become separate rows,
    then merge with teacher reference to get email addresses.
    
    Parameters:
    -----------
    student_schedules_df : DataFrame from 1_01 with StudentID, LastName, FirstName, Course, Section, Teacher1, Teacher2
    teacher_reference_df : DataFrame from 6_42 with Teacher, Mail, TeacherName
    
    Returns:
    --------
    DataFrame with StudentID, StudentName, TeacherEmail, TeacherName, Course, Section
    """
    # Create student name
    student_schedules_df["StudentName"] = (
        student_schedules_df["LastName"] + ", " + student_schedules_df["FirstName"]
    )
    
    # Get Teacher1 records
    teacher1_df = student_schedules_df[
        ["StudentID", "StudentName", "Course", "Section", "Teacher1"]
    ].copy()
    teacher1_df = teacher1_df.rename(columns={"Teacher1": "Teacher"})
    
    # Get Teacher2 records (only non-blank)
    teacher2_df = student_schedules_df[
        student_schedules_df["Teacher2"].notna() & (student_schedules_df["Teacher2"] != "")
    ][["StudentID", "StudentName", "Course", "Section", "Teacher2"]].copy()
    teacher2_df = teacher2_df.rename(columns={"Teacher2": "Teacher"})
    
    # Combine Teacher1 and Teacher2 records
    all_teachers_df = pd.concat([teacher1_df, teacher2_df], ignore_index=True)
    
    # Merge with teacher reference to get email and name
    schedule_with_teachers = all_teachers_df.merge(
        teacher_reference_df[["Teacher", "Mail", "TeacherName"]],
        on="Teacher",
        how="inner"  # Only keep records where teacher exists in reference
    )
    
    # Rename and select final columns
    schedule_with_teachers = schedule_with_teachers.rename(columns={"Mail": "TeacherEmail"})
    schedule_with_teachers = schedule_with_teachers[
        ["StudentID", "StudentName", "TeacherEmail", "TeacherName", "Course", "Section"]
    ]
    
    # Drop duplicates (in case same student-teacher-course appears multiple times)
    schedule_with_teachers = schedule_with_teachers.drop_duplicates()
    
    return schedule_with_teachers


def find_shared_students(schedule_df):
    """
    Find all students who have multiple teachers from the schedule.
    
    Returns:
    --------
    dict: {student_id: {'name': name, 'teachers': [list of teacher emails]}}
    """
    # Group by student to find their teachers
    student_teachers = defaultdict(lambda: {'name': '', 'teachers': []})
    
    for _, row in schedule_df.iterrows():
        student_id = row['StudentID']
        if not student_teachers[student_id]['name']:
            student_teachers[student_id]['name'] = row['StudentName']
        if row['TeacherEmail'] not in student_teachers[student_id]['teachers']:
            student_teachers[student_id]['teachers'].append(row['TeacherEmail'])
    
    # Only keep students with 2+ teachers
    shared_students = {
        student_id: info
        for student_id, info in student_teachers.items() 
        if len(info['teachers']) >= 2
    }
    
    return shared_students


def create_teacher_matrix(schedule_df, shared_students):
    """
    Create an n x n matrix showing how many students each teacher pair has in common.
    
    Returns:
    --------
    DataFrame: Matrix with teachers as both rows and columns, values are shared student counts
    """
    # Get unique teachers
    teachers = sorted(schedule_df['TeacherEmail'].unique())
    
    # Get teacher names for display
    teacher_names = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    
    # Create labels (Name <email>)
    teacher_labels = [f"{teacher_names.get(t, 'Unknown')} <{t}>" for t in teachers]
    
    # Initialize matrix
    matrix = pd.DataFrame(0, index=teacher_labels, columns=teacher_labels)
    
    # Fill in the matrix
    for student_id, info in shared_students.items():
        teachers_list = info['teachers']
        # For each pair of teachers who share this student
        for i in range(len(teachers_list)):
            for j in range(len(teachers_list)):
                if i != j:
                    teacher_i = teachers_list[i]
                    teacher_j = teachers_list[j]
                    label_i = f"{teacher_names.get(teacher_i, 'Unknown')} <{teacher_i}>"
                    label_j = f"{teacher_names.get(teacher_j, 'Unknown')} <{teacher_j}>"
                    matrix.loc[label_i, label_j] += 1
    
    return matrix


def create_unpaired_debug_info(unpaired_teachers, missing_teachers, schedule_df, shared_students):
    """
    Create debug information for teachers who weren't paired.
    
    Returns:
    --------
    DataFrame with teacher email, name, reason unpaired, student count, etc.
    """
    debug_info = []
    
    # Teachers who weren't in the system at all
    for email in missing_teachers:
        debug_info.append({
            'teacher_email': email,
            'teacher_name': 'NOT FOUND',
            'status': 'Not in system',
            'total_students': 0,
            'students_with_multiple_teachers': 0,
            'potential_partners': 'N/A'
        })
    
    # Teachers who were found but couldn't be paired
    teacher_names = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    
    for email in unpaired_teachers:
        # Count total students
        total_students = len(schedule_df[schedule_df['TeacherEmail'] == email]['StudentID'].unique())
        
        # Count students with multiple teachers
        students_with_multiple = 0
        potential_partners = set()
        
        for student_id, info in shared_students.items():
            if email in info['teachers']:
                students_with_multiple += 1
                # Find other teachers of this student
                for other_teacher in info['teachers']:
                    if other_teacher != email:
                        potential_partners.add(other_teacher)
        
        partner_names = [teacher_names.get(p, p) for p in potential_partners]
        
        debug_info.append({
            'teacher_email': email,
            'teacher_name': teacher_names.get(email, 'Unknown'),
            'status': 'Found but unpaired',
            'total_students': total_students,
            'students_with_multiple_teachers': students_with_multiple,
            'potential_partners': ', '.join(partner_names) if partner_names else 'None'
        })
    
    return pd.DataFrame(debug_info)


def create_summary_stats(teacher_emails, found_teachers, missing_teachers, 
                        pairings, unpaired_teachers, shared_students):
    """
    Create summary statistics for the pairing process.
    
    Returns:
    --------
    DataFrame with key stats
    """
    stats = [
        {'Metric': 'Total teachers provided', 'Value': len(teacher_emails)},
        {'Metric': 'Teachers found in system', 'Value': len(found_teachers)},
        {'Metric': 'Teachers NOT found in system', 'Value': len(missing_teachers)},
        {'Metric': 'Teachers successfully paired', 'Value': len(pairings) * 2},
        {'Metric': 'Teachers unpaired', 'Value': len(unpaired_teachers)},
        {'Metric': 'Total pairings created', 'Value': len(pairings)},
        {'Metric': 'Students with 2+ PD teachers', 'Value': len(shared_students)},
    ]
    
    return pd.DataFrame(stats)


def create_all_shared_students_list(shared_students, schedule_df):
    """
    Create a list of all students with multiple teachers, showing student info and teacher count.
    
    Returns:
    --------
    DataFrame with StudentID, LastName, FirstName, NumTeachers
    """
    student_info = []
    
    # Get student names from schedule_df
    student_names = schedule_df[['StudentID', 'StudentName']].drop_duplicates()
    
    for student_id, info in shared_students.items():
        # Parse student name (format is "LastName, FirstName")
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


def create_students_by_pair_wide(pairings, schedule_df):
    """
    Create a list of students for each teacher pair (wide format).
    Each student appears once with Teacher1 and Teacher2 as columns.
    
    Returns:
    --------
    DataFrame with StudentID, LastName, FirstName, Teacher1_Name, Teacher1_Email, Teacher2_Name, Teacher2_Email
    """
    rows = []
    
    for pairing in pairings:
        teacher1_email = pairing['teacher1_email']
        teacher2_email = pairing['teacher2_email']
        teacher1_name = pairing['teacher1_name']
        teacher2_name = pairing['teacher2_name']
        
        # Get all shared students (parse from the comma-separated string)
        shared_student_ids = [int(s.strip()) for s in pairing['all_shared_students'].split(',')]
        
        # Get student info
        for student_id in shared_student_ids:
            student_row = schedule_df[schedule_df['StudentID'] == student_id].iloc[0]
            student_name = student_row['StudentName']
            
            # Parse student name
            if ', ' in student_name:
                last_name, first_name = student_name.split(', ', 1)
            else:
                last_name = student_name
                first_name = ''
            
            rows.append({
                'StudentID': student_id,
                'LastName': last_name,
                'FirstName': first_name,
                'Teacher1_Name': teacher1_name,
                'Teacher1_Email': teacher1_email,
                'Teacher2_Name': teacher2_name,
                'Teacher2_Email': teacher2_email
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['Teacher1_Name', 'Teacher2_Name', 'LastName', 'FirstName'])
    
    return df


def create_students_by_pair_long(pairings, schedule_df):
    """
    Create a list of students for each teacher pair (long format).
    Each student appears twice - once for Teacher1 and once for Teacher2.
    
    Returns:
    --------
    DataFrame with StudentID, LastName, FirstName, TeacherName, TeacherEmail, PairPartner
    """
    rows = []
    
    for pairing in pairings:
        teacher1_email = pairing['teacher1_email']
        teacher2_email = pairing['teacher2_email']
        teacher1_name = pairing['teacher1_name']
        teacher2_name = pairing['teacher2_name']
        
        # Get all shared students
        shared_student_ids = [int(s.strip()) for s in pairing['all_shared_students'].split(',')]
        
        # Get student info
        for student_id in shared_student_ids:
            student_row = schedule_df[schedule_df['StudentID'] == student_id].iloc[0]
            student_name = student_row['StudentName']
            
            # Parse student name
            if ', ' in student_name:
                last_name, first_name = student_name.split(', ', 1)
            else:
                last_name = student_name
                first_name = ''
            
            # Add row for Teacher1
            rows.append({
                'StudentID': student_id,
                'LastName': last_name,
                'FirstName': first_name,
                'TeacherName': teacher1_name,
                'TeacherEmail': teacher1_email,
                'PairPartner': teacher2_name
            })
            
            # Add row for Teacher2
            rows.append({
                'StudentID': student_id,
                'LastName': last_name,
                'FirstName': first_name,
                'TeacherName': teacher2_name,
                'TeacherEmail': teacher2_email,
                'PairPartner': teacher1_name
            })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['TeacherName', 'LastName', 'FirstName'])
    
    return df


def identify_co_teachers(schedule_df):
    """
    Identify pairs of teachers who co-teach the same course/section.
    
    Returns:
    --------
    set of tuples: {(teacher1_email, teacher2_email), ...}
    """
    co_teacher_pairs = set()
    
    # Group by course and section to find teachers teaching together
    for (course, section), group in schedule_df.groupby(['Course', 'Section']):
        teachers = group['TeacherEmail'].unique().tolist()
        
        # If multiple teachers for this course/section, they're co-teachers
        if len(teachers) > 1:
            for i in range(len(teachers)):
                for j in range(i + 1, len(teachers)):
                    pair = tuple(sorted([teachers[i], teachers[j]]))
                    co_teacher_pairs.add(pair)
    
    return co_teacher_pairs


def create_teacher_pairs_with_unpaired(shared_students, schedule_df):
    """
    Create teacher pairings and track which teachers remain unpaired.
    Uses a greedy algorithm that prioritizes teachers with fewer pairing options.
    Avoids pairing co-teachers together unless necessary.
    
    Returns:
    --------
    tuple: (pairings list, unpaired_teachers set)
    """
    # Get all unique teachers
    all_teachers = set(schedule_df['TeacherEmail'].unique())
    
    # Identify co-teacher pairs (teachers who share the same course/section)
    co_teacher_pairs = identify_co_teachers(schedule_df)
    
    # Count how many shared students each teacher pair has
    teacher_pair_students = defaultdict(list)
    
    for student_id, info in shared_students.items():
        teachers = info['teachers']
        # Create all possible pairs of teachers for this student
        for i in range(len(teachers)):
            for j in range(i + 1, len(teachers)):
                pair = tuple(sorted([teachers[i], teachers[j]]))
                teacher_pair_students[pair].append(student_id)
    
    # Count how many potential partners each teacher has
    teacher_partner_counts = defaultdict(set)
    for (teacher1, teacher2) in teacher_pair_students.keys():
        teacher_partner_counts[teacher1].add(teacher2)
        teacher_partner_counts[teacher2].add(teacher1)
    
    # Track used teachers
    used_teachers = set()
    pairings = []
    
    # STRATEGY: Prioritize teachers with fewer options (most constrained first)
    # Avoid pairing co-teachers unless it's the only option
    
    while True:
        # Find unpaired teachers and their remaining available partners
        available_pairs = []
        
        for (teacher1, teacher2), students in teacher_pair_students.items():
            if teacher1 not in used_teachers and teacher2 not in used_teachers:
                # Count how many OTHER available partners each teacher has
                teacher1_options = len([p for p in teacher_partner_counts[teacher1] 
                                       if p not in used_teachers and p != teacher2])
                teacher2_options = len([p for p in teacher_partner_counts[teacher2] 
                                       if p not in used_teachers and p != teacher1])
                
                # Priority: minimum of the two teachers' option counts
                # This prioritizes pairs where at least one teacher has few options
                min_options = min(teacher1_options, teacher2_options)
                
                # Check if this pair are co-teachers
                is_co_teacher_pair = (teacher1, teacher2) in co_teacher_pairs or (teacher2, teacher1) in co_teacher_pairs
                
                available_pairs.append({
                    'teachers': (teacher1, teacher2),
                    'students': students,
                    'min_options': min_options,
                    'shared_count': len(students),
                    'is_co_teachers': is_co_teacher_pair
                })
        
        if not available_pairs:
            break
        
        # Sort by:
        # 1. Fewest options first (most constrained)
        # 2. Prefer non-co-teachers (False < True in sorting)
        # 3. Then by most shared students (quality of pairing)
        available_pairs.sort(key=lambda x: (x['min_options'], x['is_co_teachers'], -x['shared_count']))
        
        # Take the best pair
        best_pair = available_pairs[0]
        teacher1_email, teacher2_email = best_pair['teachers']
        students = best_pair['students']
        
        # Select 2 students for this pair (prioritize students with fewer total teachers)
        student_priorities = []
        for student_id in students:
            num_teachers = len(shared_students[student_id]['teachers'])
            student_priorities.append((student_id, num_teachers))
        
        # Sort by number of teachers (ascending) - prefer students with fewer teachers
        student_priorities.sort(key=lambda x: x[1])
        selected_students = [s[0] for s in student_priorities[:2]]
        
        pairings.append({
            'teacher1_email': teacher1_email,
            'teacher2_email': teacher2_email,
            'student1_id': selected_students[0] if len(selected_students) > 0 else None,
            'student2_id': selected_students[1] if len(selected_students) > 1 else None,
            'shared_students_count': len(students),
            'all_shared_students': ', '.join([str(s) for s in students]),
            'are_co_teachers': best_pair['is_co_teachers']
        })
        
        used_teachers.add(teacher1_email)
        used_teachers.add(teacher2_email)
    
    # Add teacher and student names to the output
    teacher_info = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    student_info = schedule_df[['StudentID', 'StudentName']].drop_duplicates().set_index('StudentID')['StudentName'].to_dict()
    
    for pairing in pairings:
        pairing['teacher1_name'] = teacher_info.get(pairing['teacher1_email'], 'Unknown')
        pairing['teacher2_name'] = teacher_info.get(pairing['teacher2_email'], 'Unknown')
        pairing['student1_name'] = student_info.get(pairing['student1_id'], 'Unknown') if pairing['student1_id'] else None
        pairing['student2_name'] = student_info.get(pairing['student2_id'], 'Unknown') if pairing['student2_id'] else None
    
    # Track unpaired teachers
    unpaired_teachers = all_teachers - used_teachers
    
    return pairings, unpaired_teachers
    """
    Create teacher pairings where each pair shares at least 2 students.
    Prioritizes students with the most teachers in common.
    
    Returns:
    --------
    list of dicts with pairing information
    """
    # Count how many shared students each teacher pair has
    teacher_pair_students = defaultdict(list)
    
    for student_id, info in shared_students.items():
        teachers = info['teachers']
        # Create all possible pairs of teachers for this student
        for i in range(len(teachers)):
            for j in range(i + 1, len(teachers)):
                pair = tuple(sorted([teachers[i], teachers[j]]))
                teacher_pair_students[pair].append(student_id)
    
    # Sort pairs by number of shared students (descending)
    sorted_pairs = sorted(
        teacher_pair_students.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    # Create pairings, ensuring each teacher appears at most once in first pass
    used_teachers = set()
    pairings = []
    
    # First pass: pair teachers who haven't been paired yet
    for (teacher1_email, teacher2_email), students in sorted_pairs:
        if teacher1_email not in used_teachers and teacher2_email not in used_teachers:
            # Select 2 students for this pair (prioritize students with fewer total teachers)
            student_priorities = []
            for student_id in students:
                num_teachers = len(shared_students[student_id]['teachers'])
                student_priorities.append((student_id, num_teachers))
            
            # Sort by number of teachers (ascending) - prefer students with fewer teachers
            student_priorities.sort(key=lambda x: x[1])
            selected_students = [s[0] for s in student_priorities[:2]]
            
            pairings.append({
                'teacher1_email': teacher1_email,
                'teacher2_email': teacher2_email,
                'student1_id': selected_students[0] if len(selected_students) > 0 else None,
                'student2_id': selected_students[1] if len(selected_students) > 1 else None,
                'shared_students_count': len(students),
                'all_shared_students': ', '.join([str(s) for s in students])
            })
            
            used_teachers.add(teacher1_email)
            used_teachers.add(teacher2_email)
    
    # Second pass: if teachers remain unpaired, try to pair them even if one is already paired
    all_teachers = set(schedule_df['TeacherEmail'].unique())
    remaining_teachers = list(all_teachers - used_teachers)
    
    for (teacher1_email, teacher2_email), students in sorted_pairs:
        if len(remaining_teachers) < 2:
            break
            
        if teacher1_email in remaining_teachers and teacher2_email in remaining_teachers:
            student_priorities = []
            for student_id in students:
                num_teachers = len(shared_students[student_id]['teachers'])
                student_priorities.append((student_id, num_teachers))
            
            student_priorities.sort(key=lambda x: x[1])
            selected_students = [s[0] for s in student_priorities[:2]]
            
            pairings.append({
                'teacher1_email': teacher1_email,
                'teacher2_email': teacher2_email,
                'student1_id': selected_students[0] if len(selected_students) > 0 else None,
                'student2_id': selected_students[1] if len(selected_students) > 1 else None,
                'shared_students_count': len(students),
                'all_shared_students': ', '.join([str(s) for s in students])
            })
            
            remaining_teachers.remove(teacher1_email)
            remaining_teachers.remove(teacher2_email)
    
    # Add teacher and student names to the output
    teacher_info = schedule_df[['TeacherEmail', 'TeacherName']].drop_duplicates().set_index('TeacherEmail')['TeacherName'].to_dict()
    student_info = schedule_df[['StudentID', 'StudentName']].drop_duplicates().set_index('StudentID')['StudentName'].to_dict()
    
    for pairing in pairings:
        pairing['teacher1_name'] = teacher_info.get(pairing['teacher1_email'], 'Unknown')
        pairing['teacher2_name'] = teacher_info.get(pairing['teacher2_email'], 'Unknown')
        pairing['student1_name'] = student_info.get(pairing['student1_id'], 'Unknown') if pairing['student1_id'] else None
        pairing['student2_name'] = student_info.get(pairing['student2_id'], 'Unknown') if pairing['student2_id'] else None
    
    return pairings