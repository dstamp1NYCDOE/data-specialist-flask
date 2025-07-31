import pandas as pd


from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import min_weight_full_bipartite_matching

double_periods = [
    'ACS11TD',
    'AES11TE',
    'APS11T',
    'ALS21T',
    'ALS21TP',
    'AFS61TF',
    'AFS63TD',
    'AFS65TC',
    'AFS65TCC',
    'AFS65TCH',
    ]

def main(master_schedule_output_filename):
    master_schedule_df = pd.read_excel(master_schedule_output_filename).fillna('')
    student_requests_df = pd.read_excel('4.01.xlsx')


    requests_cols = ['StudentID','LastName','FirstName','Course']
    master_schedule_cols = ['CourseCode','SectionID','PeriodID']
    combined_df = student_requests_df[requests_cols].merge(master_schedule_df[master_schedule_cols], left_on=['Course'], right_on=['CourseCode'], how='left')

    combined_df = combined_df.sort_values(by=['PeriodID'])

    student_group_by = combined_df.groupby(['StudentID'])
    counter = 0
    for StudentID, student_courses_df in student_group_by:
        student_course_list = student_courses_df['Course'].unique()
        student_course_grid_df = student_courses_df.groupby(['Course'])
        output_matrix = []
        for course, course_grid_df in student_course_grid_df:
            output_dict = {'Course':course}
            list_of_periods = list(course_grid_df['PeriodID'])
            for i in range(10):
                if i in list_of_periods:
                    if output_dict.get(i):
                        output_dict[i] += 1
                    else:
                        output_dict[i] = 1
                else:
                    output_dict[i] = 0
            output_matrix.append(output_dict)

            if course in double_periods:
                output_matrix.append(output_dict)

        output_df = pd.DataFrame(output_matrix)

        cost = output_df[[1,2,3,4,5,6,7,8,9]]
        biadjacency_matrix = csr_matrix(cost)
        try:
            matching_output = min_weight_full_bipartite_matching(biadjacency_matrix)[1]
        except ValueError:
            counter+=1
            print(output_df)
            print(f'no match {StudentID}: #{counter}')

        # row_ind, col_ind = linear_sum_assignment(cost)
        # print(row_ind)
        # print(col_ind)





if __name__ == "__main__":
    master_scheduled_output_filename = 'MasterScheduleOutput|02M600|2022-2023|1.xlsx'
    main(master_scheduled_output_filename)
