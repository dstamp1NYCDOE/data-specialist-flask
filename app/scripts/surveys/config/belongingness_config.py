"""
Configuration for Student Belongingness Survey
Defines weights, profiles, tier rules, and intervention suggestions
"""


class BelongingnessConfig:
    """Configuration object for belongingness survey analysis."""
    
    def __init__(self):
        # Define all question columns
        self.question_columns = [f'Q{i}' for i in range(1, 17)]
        
        # Define weighted questions (2x multiplier)
        self.weighted_questions = {
            'Q1': 2,  # I have close friends at this school
            'Q3': 2,  # At least one adult at this school knows me well
            'Q8': 2   # I feel like I am part of this school community
        }
        
        # Define dimension groupings
        self.dimension_groups = {
            'Peer_Relationships': [1, 2, 14],  # Q1, Q2, Q14
            'Adult_Relationships': [3, 4],      # Q3, Q4
            'School_Participation': [5, 6],     # Q5, Q6
            'General_Connection': [7, 8, 12, 13],  # Q7, Q8, Q12, Q13
            'Classroom_Belonging': [9, 10, 11]  # Q9, Q10, Q11
        }
        
        # Tier thresholds (percentiles)
        self.tier_thresholds = {
            'tier3_percentile': 5,      # Bottom 5% = Tier 3
            'tier2_percentile_low': 6,  # 6th percentile
            'tier2_percentile_high': 15  # 15th percentile
        }
    
    def get_question_columns(self):
        """Return list of question column names."""
        return self.question_columns
    
    def get_weighted_questions(self):
        """Return dictionary of weighted questions and their multipliers."""
        return self.weighted_questions
    
    def get_profile_functions(self):
        """
        Return dictionary of profile detection functions.
        Each function takes a row and returns True/False.
        """
        profiles = {
            'A': self._profile_a_socially_isolated,
            'B': self._profile_b_no_adult_connection,
            'C': self._profile_c_barrier_faced,
            'D': self._profile_d_classroom_outsider,
            'E': self._profile_e_comprehensively_disengaged
        }
        return profiles
    
    def _profile_a_socially_isolated(self, row):
        """Profile A: Socially Isolated - lacks peer connections."""
        # Criteria: Q1 ≤ 2 OR (Q1 + Q2 + Q14) ≤ 6
        q1 = row.get('Q1', 0)
        q2 = row.get('Q2', 0)
        q14 = row.get('Q14', 0)
        
        return (q1 <= 2) or ((q1 + q2 + q14) <= 6)
    
    def _profile_b_no_adult_connection(self, row):
        """Profile B: No Adult Connection - HIGHEST PRIORITY."""
        # Criteria: Q3 ≤ 2 AND Q4 ≤ 2
        q3 = row.get('Q3', 0)
        q4 = row.get('Q4', 0)
        
        return (q3 <= 2) and (q4 <= 2)
    
    def _profile_c_barrier_faced(self, row):
        """Profile C: Barrier-Faced - wants involvement but faces barriers."""
        # Criteria: Q5 ≤ 2 AND Q6 ≥ 3
        q5 = row.get('Q5', 0)
        q6 = row.get('Q6', 0)
        
        return (q5 <= 2) and (q6 >= 3)
    
    def _profile_d_classroom_outsider(self, row):
        """Profile D: Classroom Outsider - disconnected in classroom settings."""
        # Criteria: (Q9 + Q10 + Q11) ≤ 7
        q9 = row.get('Q9', 0)
        q10 = row.get('Q10', 0)
        q11 = row.get('Q11', 0)
        
        return (q9 + q10 + q11) <= 7
    
    def _profile_e_comprehensively_disengaged(self, row):
        """Profile E: Comprehensively Disengaged - disconnected across multiple dimensions."""
        # Criteria: 5+ questions with score ≤ 2
        low_scores = 0
        for i in range(1, 17):
            q_col = f'Q{i}'
            if q_col in row and row[q_col] <= 2:
                low_scores += 1
        
        return low_scores >= 5
    
    def get_tier_thresholds(self):
        """Return tier threshold percentiles."""
        return self.tier_thresholds
    
    def get_tier_overrides(self):
        """
        Return list of tier override rules.
        Each rule has a 'condition' function and target 'tier'.
        """
        overrides = [
            # {
            #     'name': 'Profile E (Comprehensively Disengaged)',
            #     'condition': lambda row: row.get('Profile_E', False),
            #     'tier': 'Tier 3'
            # }
        ]
        return overrides
    
    def get_ranking_criteria(self):
        """
        Return ordered list of ranking criteria for prioritization within tiers.
        Criteria are applied in order as tie-breakers.
        """
        criteria = [
            {
                'name': 'Weighted Risk Score',
                'column': 'Weighted_Risk_Score',
                'type': 'score'  # Lower = higher priority
            },
            {
                'name': 'Number of Risk Profiles',
                'column': 'Num_Profiles',
                'type': 'count'  # More = higher priority
            },
            {
                'name': 'Has Profile B',
                'column': 'Profile_B',
                'type': 'flag'  # True = higher priority
            },
            {
                'name': 'Close Friends Score',
                'column': 'Q1',
                'type': 'score'  # Lower = higher priority
            },
            {
                'name': 'Grade Level Priority',
                'column': 'year_in_hs',
                'type': 'grade',
                'priority_grades': [1]  # 9th graders get priority
            }
        ]
        return criteria
    
    def get_profile_list(self):
        """Return list of profile names."""
        return ['A', 'B', 'C', 'D', 'E']
    
    def get_profile_name(self, profile_letter):
        """Return descriptive name for profile."""
        profile_names = {
            'A': 'Socially Isolated',
            'B': 'No Adult Connection (PRIORITY)',
            'C': 'Barrier-Faced',
            'D': 'Classroom Outsider',
            'E': 'Comprehensively Disengaged'
        }
        return profile_names.get(profile_letter, f'Profile {profile_letter}')
    
    def get_intervention_suggestions(self, row):
        """
        Generate intervention suggestions based on student's risk profile.
        
        Parameters:
        -----------
        row : pd.Series
            Student data row with profile flags
            
        Returns:
        --------
        str
            Suggested interventions
        """
        suggestions = []
        tier = row.get('Tier', 'Tier 1')
        
        # Profile-specific interventions
        if row.get('Profile_B', False):
            suggestions.append("PRIORITY: No adult connection - Establish counselor relationship, assign adult mentor, weekly check-ins")
        
        if row.get('Profile_E', False):
            suggestions.append("Comprehensively disengaged - One-on-one meeting, family contact, comprehensive assessment, personalized connection plan")
        
        if row.get('Profile_A', False) and row.get('Profile_B', False):
            suggestions.append("URGENT: Total isolation - Weekly counselor meetings, structured peer connection programs, classroom grouping strategies")
        elif row.get('Profile_A', False):
            suggestions.append("Socially isolated - Individual meetings, connect to clubs/activities, structured social opportunities, peer buddy program")
        
        if row.get('Profile_C', False):
            suggestions.append("Barrier-faced - Identify specific barriers (transportation/time/cost), problem-solve solutions, match to flexible activities")
        
        if row.get('Profile_D', False):
            suggestions.append("Classroom outsider - Teacher consultation, seating/grouping strategies, classroom engagement skills")
        
        # Tier-specific guidance
        if tier == 'Tier 3':
            if not suggestions:
                suggestions.append("Individual counselor meetings (2-3 sessions), individualized support plan, weekly check-ins, coordinate with teachers/parents")
        elif tier == 'Tier 2':
            if not suggestions:
                suggestions.append("Brief individual check-in (1-2 sessions), consider small group interventions, targeted resource connection")
        
        # Check for specific dimension deficits
        if 'Peer_Relationships_subscore' in row and row['Peer_Relationships_subscore'] <= 6:
            if not any('Social' in s or 'peer' in s for s in suggestions):
                suggestions.append("Low peer connections - Small group connection sessions, activity matching, club outreach")
        
        if 'Adult_Relationships_subscore' in row and row['Adult_Relationships_subscore'] <= 4:
            if not any('adult' in s for s in suggestions):
                suggestions.append("Limited adult relationships - Adult mentor connection, regular staff check-ins")
        
        if 'Classroom_Belonging_subscore' in row and row['Classroom_Belonging_subscore'] <= 7:
            if not any('Classroom' in s for s in suggestions):
                suggestions.append("Classroom disconnection - Teacher collaboration on participation strategies")
        
        # Check for grade-specific needs
        if row.get('year_in_hs') == 1:
            if row.get('FormID') == 'A' and row.get('Q15', 4) <= 2:
                suggestions.append("9th grader struggling with friendships - New student meetups, peer mentor program")
            if row.get('FormID') == 'A' and row.get('Q16', 4) <= 2:
                suggestions.append("9th grader needs navigation support - Resource orientation, identify go-to staff")
        
        if row.get('year_in_hs') == 2 and row.get('FormID') == 'C':
            if row.get('Q15', 4) <= 2:
                suggestions.append("Transfer student friendship challenges - Targeted social integration support")
            if row.get('Q16', 4) <= 2:
                suggestions.append("Transfer student not feeling ownership - Identity-building activities, leadership opportunities")
        
        if row.get('year_in_hs') in [2, 3, 4] and row.get('FormID') == 'B':
            if row.get('Q15', 4) <= 2:
                suggestions.append("Not contributing meaningfully - Identify strengths, connect to leadership/service opportunities")
            if row.get('Q16', 4) <= 2:
                suggestions.append("Hasn't found belonging groups - Interest inventory, systematic club/activity exploration")
        
        return " | ".join(suggestions) if suggestions else "Continue universal supports, monitor in next survey"
    
    def get_question_text_map(self):
        """
        Return mapping of question codes to full question text.
        Useful for chart labels.
        """
        return {
            'Q1': 'I have close friends at this school',
            'Q2': 'I feel accepted by other students at this school',
            'Q3': 'At least one adult at this school knows me well',
            'Q4': 'There is an adult here I could talk to about something personal',
            'Q5': 'I am involved in clubs sports or activities at this school',
            'Q6': 'I would like to be more involved in after-school activities',
            'Q7': 'I look forward to coming to school most days',
            'Q8': 'I feel like I am part of this school community',
            'Q9': 'I feel comfortable participating in class discussions',
            'Q10': 'In my classes my ideas and opinions are valued',
            'Q11': 'In my classes students would notice and care if I weren\'t there',
            'Q12': 'I feel proud to be a student at this school',
            'Q13': 'This school feels like a place where I fit in',
            'Q14': 'I regularly interact with other students outside of class time',
            'Q15': 'Grade-specific question (see FormID)',
            'Q16': 'Grade-specific question (see FormID)'
        }