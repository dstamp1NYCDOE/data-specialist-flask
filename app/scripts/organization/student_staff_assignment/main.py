import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict, Counter
import networkx as nx

import app.scripts.utils.utils as utils
from app.scripts import scripts, files_df
from flask import session

from io import BytesIO

def main():
    school_year = session["school_year"]
    term = session["term"]

    year_and_semester = f"{school_year}-{term}"  

    filename = utils.return_most_recent_report_by_semester(files_df, "rosters_and_grades",year_and_semester=year_and_semester)
    df = utils.return_file_as_df(filename)

    filename = utils.return_most_recent_report_by_semester(files_df, "3_07",year_and_semester=year_and_semester)
    students_df = utils.return_file_as_df(filename)    
    students_df = students_df[['StudentID','LastName','FirstName']]

    df = df.merge(students_df, on='StudentID', how='left')

    dff = assign_students_optimal_hungarian(df)
    print(dff)


    f = BytesIO()
    dff.to_csv(f, index=False)
    f = f.seek(0)
    
    download_name = 'student_teacher_assignment.csv'

    return f, download_name


import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import defaultdict, Counter
import networkx as nx

def assign_students_optimal_hungarian(df, student_id_col='StudentID', 
                                    last_name_col='LastName', first_name_col='FirstName',
                                    teacher_col='Teacher1', co_teacher_col='Teacher2'):
    """
    Optimal student-teacher assignment using Hungarian algorithm variant.
    This creates multiple 'slots' per teacher to achieve balanced assignment.
    
    Returns: DataFrame with optimal assignment
    """
    
    # Prepare student data
    students = df[[student_id_col, last_name_col, first_name_col, teacher_col]].copy()
    if co_teacher_col in df.columns:
        students[co_teacher_col] = df[co_teacher_col]
    
    # Get available teachers for each student
    students['available_teachers'] = students.apply(
        lambda row: [t for t in [row[teacher_col], row.get(co_teacher_col)] 
                    if pd.notna(t)], axis=1
    )
    
    # Get all unique teachers
    all_teachers = set()
    for teachers_list in students['available_teachers']:
        all_teachers.update(teachers_list)
    all_teachers = sorted(list(all_teachers))
    
    num_students = len(students)
    num_teachers = len(all_teachers)
    
    # Calculate target students per teacher
    base_count = num_students // num_teachers
    extra_students = num_students % num_teachers
    
    # Create teacher slots (multiple slots per teacher for balanced assignment)
    teacher_slots = []
    slot_to_teacher = {}
    
    for i, teacher in enumerate(all_teachers):
        slots_for_teacher = base_count + (1 if i < extra_students else 0)
        for slot in range(slots_for_teacher):
            slot_id = f"{teacher}_{slot}"
            teacher_slots.append(slot_id)
            slot_to_teacher[slot_id] = teacher
    
    print(f"Created {len(teacher_slots)} teacher slots for {num_students} students")
    print(f"Target distribution: {Counter(slot_to_teacher.values())}")
    
    # Create cost matrix (students x teacher_slots)
    # Cost = 0 if student can be assigned to teacher, infinity otherwise
    cost_matrix = np.full((num_students, len(teacher_slots)), np.inf)
    
    for student_idx, (_, student_row) in enumerate(students.iterrows()):
        available_teachers = student_row['available_teachers']
        
        for slot_idx, slot_id in enumerate(teacher_slots):
            teacher = slot_to_teacher[slot_id]
            if teacher in available_teachers:
                cost_matrix[student_idx, slot_idx] = 0
    
    # Check for infeasible cases before applying Hungarian algorithm
    # 1. Check if any student has no available teachers
    students_with_no_teachers = []
    for student_idx, (_, student_row) in enumerate(students.iterrows()):
        if not student_row['available_teachers']:
            students_with_no_teachers.append(student_row[student_id_col])
    
    if students_with_no_teachers:
        raise ValueError(f"Students with no available teachers: {students_with_no_teachers}")
    
    # 2. Check if cost matrix has any feasible assignments
    feasible_assignments = (cost_matrix != np.inf).sum()
    if feasible_assignments == 0:
        raise ValueError("No feasible assignments possible - check teacher/co-teacher data")
    
    # 3. Check if we have enough teacher slots
    if len(teacher_slots) < num_students:
        print(f"Warning: Only {len(teacher_slots)} teacher slots for {num_students} students")
        print("Some teachers will be over their target capacity")
        
        # Add extra slots to balance the matrix
        teachers_needing_extra = all_teachers[:num_students - len(teacher_slots)]
        for teacher in teachers_needing_extra:
            extra_slots_needed = 1  # Add one extra slot per teacher as needed
            for slot in range(extra_slots_needed):
                slot_id = f"{teacher}_extra_{slot}"
                teacher_slots.append(slot_id)
                slot_to_teacher[slot_id] = teacher
                
                # Add this slot to cost matrix
                new_column = np.full((num_students, 1), np.inf)
                for student_idx, (_, student_row) in enumerate(students.iterrows()):
                    if teacher in student_row['available_teachers']:
                        new_column[student_idx, 0] = 0
                cost_matrix = np.hstack([cost_matrix, new_column])
                
                if len(teacher_slots) >= num_students:
                    break
            if len(teacher_slots) >= num_students:
                break
    
    # Apply Hungarian algorithm
    try:
        student_indices, slot_indices = linear_sum_assignment(cost_matrix)
        
        # Check if solution is feasible
        total_cost = cost_matrix[student_indices, slot_indices].sum()
        if np.isinf(total_cost):
            raise ValueError("Hungarian algorithm found no feasible solution")
            
    except ValueError as e:
        if "cost matrix is infeasible" in str(e).lower():
            print("Hungarian algorithm failed - falling back to greedy approach")
            return assign_students_greedy_balanced(df, student_id_col, last_name_col, 
                                                 first_name_col, teacher_col, co_teacher_col)
        else:
            raise e
    
    # Create result
    result_rows = []
    for student_idx, slot_idx in zip(student_indices, slot_indices):
        student_row = students.iloc[student_idx]
        assigned_teacher = slot_to_teacher[teacher_slots[slot_idx]]
        
        result_rows.append({
            'StudentID': student_row[student_id_col],
            'LastName': student_row[last_name_col],
            'FirstName': student_row[first_name_col],
            'AssignedTeacher': assigned_teacher
        })
    
    result_df = pd.DataFrame(result_rows)
    result_df = result_df.sort_values(['AssignedTeacher', 'LastName', 'FirstName'])
    
    # Print final distribution
    final_counts = result_df['AssignedTeacher'].value_counts().sort_index()
    print(f"\nOptimal assignment distribution:")
    for teacher in all_teachers:
        count = final_counts.get(teacher, 0)
        print(f"{teacher}: {count} students")
    
    return result_df


def assign_students_min_cost_flow(df, student_id_col='StudentID', 
                                last_name_col='LastName', first_name_col='FirstName',
                                teacher_col='Teacher1', co_teacher_col='Teacher2'):
    """
    Optimal student-teacher assignment using minimum cost flow.
    This is the most theoretically sound approach for this problem.
    
    Returns: DataFrame with optimal assignment
    """
    
    # Prepare student data
    students = df[[student_id_col, last_name_col, first_name_col, teacher_col]].copy()
    if co_teacher_col in df.columns:
        students[co_teacher_col] = df[co_teacher_col]
    
    # Get available teachers for each student
    students['available_teachers'] = students.apply(
        lambda row: [t for t in [row[teacher_col], row.get(co_teacher_col)] 
                    if pd.notna(t)], axis=1
    )
    
    # Get all unique teachers
    all_teachers = set()
    for teachers_list in students['available_teachers']:
        all_teachers.update(teachers_list)
    all_teachers = sorted(list(all_teachers))
    
    num_students = len(students)
    num_teachers = len(all_teachers)
    
    # Calculate target students per teacher
    base_count = num_students // num_teachers
    extra_students = num_students % num_teachers
    
    teacher_capacities = {}
    for i, teacher in enumerate(all_teachers):
        teacher_capacities[teacher] = base_count + (1 if i < extra_students else 0)
    
    print(f"Teacher capacities: {teacher_capacities}")
    
    # Create flow network
    G = nx.DiGraph()
    
    # Add source node
    source = 'SOURCE'
    G.add_node(source)
    
    # Add sink node
    sink = 'SINK'
    G.add_node(sink)
    
    # Add student nodes with supply = 1
    student_nodes = [f"student_{i}" for i in range(num_students)]
    for student_node in student_nodes:
        G.add_node(student_node)
        G.add_edge(source, student_node, capacity=1, weight=0)
    
    # Add teacher nodes with capacity = target student count
    teacher_nodes = [f"teacher_{teacher}" for teacher in all_teachers]
    for teacher_node, teacher in zip(teacher_nodes, all_teachers):
        G.add_node(teacher_node)
        capacity = teacher_capacities[teacher]
        G.add_edge(teacher_node, sink, capacity=capacity, weight=0)
    
    # Add edges from students to their available teachers
    for student_idx, (_, student_row) in enumerate(students.iterrows()):
        student_node = f"student_{student_idx}"
        available_teachers = student_row['available_teachers']
        
        for teacher in available_teachers:
            teacher_node = f"teacher_{teacher}"
            G.add_edge(student_node, teacher_node, capacity=1, weight=0)
    
    # Solve minimum cost flow
    try:
        flow_dict = nx.min_cost_flow(G)
    except nx.NetworkXUnfeasible:
        raise ValueError("No feasible assignment exists")
    
    # Extract assignments
    result_rows = []
    for student_idx, (_, student_row) in enumerate(students.iterrows()):
        student_node = f"student_{student_idx}"
        
        # Find which teacher this student was assigned to
        assigned_teacher = None
        for teacher in all_teachers:
            teacher_node = f"teacher_{teacher}"
            if teacher_node in flow_dict[student_node] and flow_dict[student_node][teacher_node] > 0:
                assigned_teacher = teacher
                break
        
        if assigned_teacher:
            result_rows.append({
                'StudentID': student_row[student_id_col],
                'LastName': student_row[last_name_col],
                'FirstName': student_row[first_name_col],
                'AssignedTeacher': assigned_teacher
            })
    
    result_df = pd.DataFrame(result_rows)
    result_df = result_df.sort_values(['AssignedTeacher', 'LastName', 'FirstName'])
    
    # Print final distribution
    final_counts = result_df['AssignedTeacher'].value_counts().sort_index()
    print(f"\nOptimal min-cost flow assignment:")
    for teacher in all_teachers:
        count = final_counts.get(teacher, 0)
        target = teacher_capacities[teacher]
        print(f"{teacher}: {count}/{target} students")
    
    return result_df


# Simpler greedy algorithm for comparison/fallback
def assign_students_greedy_balanced(df, student_id_col='StudentID', 
                                  last_name_col='LastName', first_name_col='FirstName',
                                  teacher_col='Teacher1', co_teacher_col='Teacher2',
                                  random_seed=42):
    """
    Greedy algorithm that tries to balance load while respecting constraints.
    Fast but not guaranteed to be optimal.
    """
    import random
    random.seed(random_seed)
    
    # Prepare data
    students = df[[student_id_col, last_name_col, first_name_col, teacher_col]].copy()
    if co_teacher_col in df.columns:
        students[co_teacher_col] = df[co_teacher_col]
    
    students['available_teachers'] = students.apply(
        lambda row: [t for t in [row[teacher_col], row.get(co_teacher_col)] 
                    if pd.notna(t)], axis=1
    )
    
    # Get all teachers and calculate targets
    all_teachers = set()
    for teachers_list in students['available_teachers']:
        all_teachers.update(teachers_list)
    all_teachers = sorted(list(all_teachers))
    
    num_students = len(students)
    base_count = num_students // len(all_teachers)
    extra_students = num_students % len(all_teachers)
    
    target_counts = {}
    for i, teacher in enumerate(all_teachers):
        target_counts[teacher] = base_count + (1 if i < extra_students else 0)
    
    # Greedy assignment
    teacher_counts = {teacher: 0 for teacher in all_teachers}
    assignments = []
    
    # Shuffle students for randomness
    student_list = list(students.iterrows())
    random.shuffle(student_list)
    
    for _, student_row in student_list:
        available_teachers = student_row['available_teachers']
        
        # Choose teacher with lowest current load among available
        best_teacher = min(available_teachers, 
                          key=lambda t: (teacher_counts[t], random.random()))
        
        teacher_counts[best_teacher] += 1
        assignments.append({
            'StudentID': student_row[student_id_col],
            'LastName': student_row[last_name_col], 
            'FirstName': student_row[first_name_col],
            'AssignedTeacher': best_teacher
        })
    
    result_df = pd.DataFrame(assignments)
    result_df = result_df.sort_values(['AssignedTeacher', 'LastName', 'FirstName'])
    
    print(f"Greedy assignment distribution:")
    for teacher in all_teachers:
        count = teacher_counts[teacher]
        target = target_counts[teacher]
        print(f"{teacher}: {count}/{target} students")
    
    return result_df


def assign_students_with_validation(df, student_id_col='StudentID', 
                                  last_name_col='LastName', first_name_col='FirstName',
                                  teacher_col='Teacher1', co_teacher_col='Teacher2',
                                  method='auto'):
    """
    Smart wrapper that validates data and chooses the best algorithm.
    Handles multiple rows per student (e.g., multiple class enrollments).
    
    Parameters:
    method: 'hungarian', 'min_cost_flow', 'greedy', or 'auto' (default)
    
    Returns: DataFrame with optimal assignment (one row per unique student)
    """
    
    # Validate input data
    print("Validating input data...")
    
    # Check required columns exist
    required_cols = [student_id_col, last_name_col, first_name_col, teacher_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    print(f"Input data shape: {df.shape} (includes multiple enrollments per student)")
    
    # Consolidate student data (multiple rows per student -> one row per student)
    # Collect all teachers each student has across all their enrollments
    student_teacher_map = {}
    
    for _, row in df.iterrows():
        student_id = row[student_id_col]
        
        # Get student info (assuming name is consistent across enrollments)
        if student_id not in student_teacher_map:
            student_teacher_map[student_id] = {
                'StudentID': student_id,
                'LastName': row[last_name_col],
                'FirstName': row[first_name_col],
                'teachers': set()
            }
        
        # Add primary teacher
        if pd.notna(row[teacher_col]) and str(row[teacher_col]).strip():
            student_teacher_map[student_id]['teachers'].add(str(row[teacher_col]).strip())
        
        # Add co-teacher if exists
        if co_teacher_col and co_teacher_col in df.columns:
            if pd.notna(row[co_teacher_col]) and str(row[co_teacher_col]).strip():
                student_teacher_map[student_id]['teachers'].add(str(row[co_teacher_col]).strip())
    
    # Convert to DataFrame with unique students
    students_data = []
    for student_id, info in student_teacher_map.items():
        students_data.append({
            student_id_col: info['StudentID'],
            last_name_col: info['LastName'],
            first_name_col: info['FirstName'],
            'available_teachers': list(info['teachers'])
        })
    
    students = pd.DataFrame(students_data)
    
    # Validation checks
    total_students = len(students)
    students_with_teachers = students['available_teachers'].apply(len) > 0
    valid_students = students_with_teachers.sum()
    
    print(f"Total students: {total_students}")
    print(f"Unique students: {total_students}")
    print(f"Students with available teachers: {valid_students}")
    
    # Show example of consolidated student data
    if len(students) > 0:
        print(f"\nExample consolidated student data:")
        example_student = students.iloc[0]
        print(f"  {example_student[student_id_col]}: {example_student['available_teachers']}")
        
        # Show teacher statistics from consolidated data
        teacher_student_count = {}
        for _, student_row in students.iterrows():
            for teacher in student_row['available_teachers']:
                teacher_student_count[teacher] = teacher_student_count.get(teacher, 0) + 1
        
        print(f"\nTeacher availability (how many students could be assigned to each):")
        for teacher, count in sorted(teacher_student_count.items()):
            print(f"  {teacher}: up to {count} students")
    
    if valid_students == 0:
        raise ValueError("No students have valid teacher assignments")
    
    if valid_students < total_students:
        invalid_students = students[~students_with_teachers][student_id_col].tolist()
        print(f"Warning: {total_students - valid_students} students have no available teachers:")
        print(f"Students: {invalid_students[:5]}{'...' if len(invalid_students) > 5 else ''}")
        
        # Filter to only valid students
        students = students[students_with_teachers].copy()
        total_students = len(students)
    
    # Get teacher statistics
    all_teachers = set()
    for teachers_list in students['available_teachers']:
        all_teachers.update(teachers_list)
    all_teachers = sorted(list(all_teachers))
    
    print(f"Unique teachers found: {len(all_teachers)}")
    print(f"Teachers: {all_teachers}")
    
    # Calculate theoretical balance
    base_count = total_students // len(all_teachers)
    extra_students = total_students % len(all_teachers)
    
    print(f"Target balance: {base_count}-{base_count + (1 if extra_students > 0 else 0)} students per teacher")
    
    # Auto-select method if not specified
    if method == 'auto':
        if total_students <= 100:
            method = 'hungarian'
        elif total_students <= 1000:
            method = 'min_cost_flow'
        else:
            method = 'greedy'
        print(f"Auto-selected method: {method}")
    
    # Apply selected method
    try:
        if method == 'hungarian':
            return assign_students_optimal_hungarian(
                df, student_id_col, last_name_col, first_name_col, teacher_col, co_teacher_col
            )
        elif method == 'min_cost_flow':
            return assign_students_min_cost_flow(
                df, student_id_col, last_name_col, first_name_col, teacher_col, co_teacher_col
            )
        elif method == 'greedy':
            return assign_students_greedy_balanced(
                df, student_id_col, last_name_col, first_name_col, teacher_col, co_teacher_col
            )
        else:
            raise ValueError(f"Unknown method: {method}")
            
    except Exception as e:
        print(f"Method '{method}' failed with error: {e}")
        print("Falling back to greedy algorithm...")
        return assign_students_greedy_balanced(
            df, student_id_col, last_name_col, first_name_col, teacher_col, co_teacher_col
        )
def create_sample_data():
    """Create sample enrollment data with multiple classes per student"""
    # Create students enrolled in multiple classes
    students = []
    student_names = [(f'S{i:03d}', f'Student{i}', f'First{i}') for i in range(1, 21)]  # 20 unique students
    
    # Define some classes with their teachers
    classes = [
        ('Math101', 'Smith', 'Johnson'),     # Primary teacher: Smith, Co-teacher: Johnson
        ('English101', 'Williams', None),    # Primary teacher: Williams, No co-teacher
        ('Science101', 'Brown', 'Davis'),    # Primary teacher: Brown, Co-teacher: Davis
        ('History101', 'Miller', None),      # Primary teacher: Miller, No co-teacher
        ('Art101', 'Wilson', 'Garcia'),      # Primary teacher: Wilson, Co-teacher: Garcia
    ]
    
    # Generate enrollment data - each student enrolls in 2-4 classes
    import random
    random.seed(42)
    
    enrollments = []
    for student_id, last_name, first_name in student_names:
        # Each student takes 2-4 classes
        num_classes = random.randint(2, 4)
        student_classes = random.sample(classes, num_classes)
        
        for class_name, teacher, co_teacher in student_classes:
            enrollments.append({
                'StudentID': student_id,
                'LastName': last_name,
                'FirstName': first_name,
                'Class': class_name,
                'Teacher': teacher,
                'CoTeacher': co_teacher
            })
    
    return pd.DataFrame(enrollments)


if __name__ == "__main__":
    # Create and test with sample data
    sample_df = create_sample_data()
    print("Sample data overview:")
    print(f"Shape: {sample_df.shape}")
    print(f"Teachers: {sample_df['Teacher'].value_counts().to_dict()}")
    print(f"Co-teachers: {sample_df['CoTeacher'].value_counts().to_dict()}")
    
    print("\n" + "=" * 60)
    print("SMART ASSIGNMENT WITH VALIDATION")
    print("=" * 60)
    
    try:
        # Use the smart wrapper - it will handle errors and choose the best method
        result = assign_students_with_validation(
            sample_df,
            student_id_col='StudentID',
            last_name_col='LastName', 
            first_name_col='FirstName',
            teacher_col='Teacher1',
            co_teacher_col='Teacher2',
            method='auto'  # Let it choose the best method
        )
        
        print(f"\nSuccessfully assigned {len(result)} students")
        print("\nFirst 10 assignments:")
        print(result.head(10))
        
        # Show final distribution
        final_distribution = result['AssignedTeacher'].value_counts().sort_index()
        print(f"\nFinal distribution:")
        for teacher, count in final_distribution.items():
            print(f"  {teacher}: {count} students")
            
    except Exception as e:
        print(f"Assignment failed: {e}")
        print("Please check your data format and try again")

# Example usage and test data creation