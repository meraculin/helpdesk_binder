import pandas as pd
from assign_util import *

# Exclude specific individuals
#def exclude_individuals(data, excluded_names):
#    return data.drop(columns=excluded_names, errors='ignore')

# Choose the time
year = 2025
month = 1
WW_check = False

month_str = f'0{month}' if month < 10 else str(month)

# File name of the densuke file
file_name = f"HD_{year}{month_str}"
# Path to the densuke .csv file
file_path = f"data/{file_name}.csv"

# Load the shift data from densuke .csv file
try:
    shift_data = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"File not found: {file_path}", end="\n\n")


# Set the number of students per shift
num_per_shift = 2

# Load the member data from the .csv file (from Airtable)
member_info = load_member_data_csv('data/HD_2024members.csv')

# Obtain the shifts applied by the students
applied_shifts = count_applied_shifts(shift_data)
# Determine the assignment range
assignment_range = determine_shift_range(applied_shifts, min_percentage=0.5, max_percentage=1.0)
# Obtain the shifts that the students applied to
simultaneous_shifts = extract_simultaneous_shifts(shift_data)

schedule_temp = assign_shift_b2b(simultaneous_shifts, member_info=member_info, num_students=num_per_shift)
schedule = swap_student_positions(schedule_temp, num_students=num_per_shift)

# Print the assigned schedule
print("\nAssigned schedules\n")
print(schedule, end="\n\n")

# Statistics of the assignment algorithms
individual_stats_df, overall_stats_df = calculate_assigned_shifts(schedule, applied_shifts, num_students=num_per_shift)
print(individual_stats_df, end="\n\n")
print("Overall statistics:\n")
print(overall_stats_df, end="\n\n")

# Save the schedule and the statistics to an Excel file
save_directory = f"result/{file_name}_temp.xlsx"
with pd.ExcelWriter(save_directory) as writer:
    schedule.to_excel(writer, sheet_name='Schedule')
    individual_stats_df.to_excel(writer, sheet_name='Individual Stats')
    overall_stats_df.to_excel(writer, sheet_name='Overall Stats')
    print(f"Assigned schedule and statistics have been successfully saved into: ~/{save_directory}", end="\n\n")
    print("\n================================================================\n")
