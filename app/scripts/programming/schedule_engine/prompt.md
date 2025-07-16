# Student Scheduling System Prompt

## Objective
Create a Python program that optimally assigns students to course sections based on their requests, master schedule constraints, and conflict avoidance rules. The system should provide detailed analysis of scheduling issues and actionable recommendations for master schedule improvements.

## Input Data Files

### 1. Student Course Requests
- Format: Long-form list with columns: Student_ID, Course_Code
- Each row represents one course request for one student
- Students may have varying numbers of course requests

### 2. Master Schedule
- Columns: Course_Code, Section, Teacher, Room, Capacity, Period, Cycle_Day
- Cycle_Day format: 5-character string (MTWRF) where 1=meets that day, 0=doesn't meet
  - Example: "11111" (daily), "10101" (MWF), "01010" (TR)
- Period: numerical period identifier
- Capacity: maximum students per section

### 3. Locked Student Assignments
- Columns: Student_ID, Course_Code, Section
- These are pre-determined assignments that must be honored if the course/section still exists
- Flag any locked assignments where the course/section no longer exists in master schedule

### 4. Student Conflict List
- Columns: Student_A, Student_B
- Students who should not be scheduled together unless mathematically impossible to avoid

### 5. Course Time Constraints (Optional)
- Columns: Course_Code, Allowed_Periods, Allowed_Days
- Specifies which courses can only be taught at certain times
- Use for recommendation context

## Algorithm Requirements

### Phase 1: Constraint Processing
1. **Validate locked assignments** - Create error report for any locked assignments referencing non-existent course/section combinations
2. **Identify scheduling conflicts** - Analyze course requests to identify:
   - Singletons: courses offered only once that conflict with other student requests
   - Virtual singletons: courses offered multiple times but all at the same conflicting time
3. **Calculate student difficulty scores** based on:
   - Number of course requests
   - Conflicts with locked students
   - Limited section availability
   - Singleton/virtual singleton conflicts

### Phase 2: Initial Assignment
1. **Place locked students first** - Assign all valid locked assignments
2. **Schedule hardest students first** - Process students in order of difficulty score
3. **Apply hard constraints**:
   - No student in two courses meeting same period/day combination
   - Respect section capacity limits
   - Honor student conflict avoidance when possible

### Phase 3: Optimization
1. **Balance class sizes** - Redistribute students to achieve more even section enrollment within capacity limits
2. **Compact schedules** - For students with fewer courses, minimize gaps and cluster toward beginning/end of day
3. **Resolve remaining conflicts** - Final attempt to separate conflicted students

### Phase 4: Analysis and Recommendations

## Output Requirements

### 1. Student Assignment Report
- Columns: Student_ID, Course_Code, Section_Assignment
- Include ALL students and their course requests
- Leave Section_Assignment blank for unscheduled courses
- Sort by Student_ID, then Course_Code

### 2. Error Report
- List all locked assignments that reference non-existent course/section combinations
- Format: Student_ID, Course_Code, Section, Error_Description

### 3. Scheduling Statistics
- Overall success rate (percentage of course requests fulfilled)
- Grade-level breakdowns (analyze course request patterns to infer grade levels)
- Course-specific metrics (enrollment, capacity utilization)
- Section balance analysis (variance in enrollment across sections of same course)
- Conflict resolution success rate

### 4. Master Schedule Analysis and Recommendations

#### By Department Analysis:
- Identify cross-departmental conflicts where popular courses for the same student population are scheduled simultaneously
- Calculate "competition index" for each time slot showing demand vs. availability
- Flag periods with high student demand but limited course offerings

#### Specific Recommendations:
- **General guidance**: "Grade X has too many popular courses in Period Y"
- **Specific suggestions**: "Move Course_Code from Period X to Period Y to reduce conflicts"
- **Capacity recommendations**: "Add section of Course_Code" or "Increase capacity of existing sections"
- Consider time constraints when making recommendations

### 5. Problematic Students Report
- List students who couldn't be fully scheduled
- Show which specific courses couldn't be assigned and why
- Identify students with the most conflicts

## Algorithm Approach
- Use constraint satisfaction with iterative optimization
- Implement heuristic-based initial solution followed by local optimization
- Prioritize complete student schedules over perfect class balance
- When conflicts are unavoidable, document the decision-making process

## Success Criteria
- Maximize number of students with complete schedules
- Minimize student conflicts while maintaining feasibility
- Provide actionable insights for master schedule iteration
- Generate clear, implementable recommendations for schedule improvements

## Notes
- Focus on core functionality; handle edge cases gracefully but don't over-complicate
- Emphasize cross-departmental conflict detection as this is often missed in manual scheduling
- Design output to support iterative master schedule refinement process