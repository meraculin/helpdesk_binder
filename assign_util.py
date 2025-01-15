import pandas as pd
import numpy as np
import re
import random
from datetime import datetime, timedelta

def count_applied_shifts(data):
    """Count the number of shifts each student has applied for."""
    return (data.iloc[:, 1:] == "○").sum(axis=0)

def determine_shift_range(applied_shifts, min_percentage=0.4, max_percentage=0.6):
    """Determine the range of shifts each student should be assigned."""
    min_shifts = (min_percentage * applied_shifts).astype(int)
    max_shifts = (max_percentage * applied_shifts).astype(int)
    return pd.DataFrame({
        "Applied Shifts": applied_shifts,
        "Min_Assigned": min_shifts,
        "Max_Assigned": max_shifts
    })

def extract_simultaneous_shifts(data):
    """Extract simultaneous shifts including date, time, and location, along with available students."""
    # Updated regex pattern to match the new format including location
    pattern = r'(\d{1,2}/\d{1,2})\s\(.\)\s(\d{2}:\d{2} - \d{2}:\d{2})\s\((.+)\)'
    simultaneous_shifts = {}
    for index, row in data.iterrows():
        match = re.search(pattern, row[0])
        if match:
            month_date, time_range, location = match.groups()
            available_students = row[row == "○"].index.tolist()
            # Use (date, time, location) as the key
            key = (month_date, time_range, location)
            simultaneous_shifts[key] = available_students
        else:
            print(f"No match found for row: {row[0]}")  # Debug print

    return pd.DataFrame(simultaneous_shifts.items(), columns=['Shift', 'Available Students'])


def assign_a_student_to_shift(simultaneous_shifts, assignment_range):
    """Assign students to shifts based on availability and shift limits, with an element of randomness.
    Ensure that each shift is filled by distinct students if possible."""
    schedule_entries = []
    shifts_count = {student: 0 for student in assignment_range.index}

    # First pass: Assign students based on availability and shift limits
    for index, row in simultaneous_shifts.iterrows():
        date, timeslot = row['Shift']
        available_students = row['Available Students']
        random.shuffle(available_students)
        sorted_students = sorted(available_students, key=lambda x: shifts_count[x])
        assigned_students = []

        for student in sorted_students:
            if shifts_count[student] < assignment_range.loc[student, "Max_Assigned"]:
                assigned_students.append(student)
                shifts_count[student] += 1

                if len(assigned_students) == 1:
                    break

        schedule_entries.append([date, timeslot, assigned_students[0] if len(assigned_students) > 0 else None,
                                 assigned_students[1] if len(assigned_students) > 1 else None])

    schedule_df = pd.DataFrame(schedule_entries, columns=["Date", "Timeslot", "Student 1", "Student 2"])

    return schedule_df

def test_assign_students_to_shifts(simultaneous_shifts, assignment_range, num_students=2):
    """Assign students to shifts based on availability and shift limits, with an element of randomness.
    Ensure that each shift is filled by distinct students if possible."""
    schedule_entries = []
    shifts_count = {student: 0 for student in assignment_range.index}
    # Make the schedule dataframe based on the number of students
    row_num = 1
    
    # First pass: Assign students based on availability and shift limits
    for index, row in simultaneous_shifts.iterrows():
        assigned_students = []
        assign_count = 0
        date, timeslot = row['Shift']
        available_students = row['Available Students']
        sorted_students = sorted(available_students, key=lambda x: shifts_count[x])
        
        students_shift_count = np.unique([shifts_count[s] for s in sorted_students])
        lowest_shift_count = students_shift_count[0]
        
        # Remove students with shift count higher than the lowest shift count
        filtered_students = [s for s in sorted_students if shifts_count[s] <= lowest_shift_count]
        if len(students_shift_count) > 1 and len(filtered_students) < num_students + 1 and len(students_shift_count) > 1:
            filtered_students = [s for s in sorted_students if shifts_count[s] <= students_shift_count[1]]
        elif len(filtered_students) == len(sorted_students):
            filtered_students = sorted_students
        
        while assign_count < num_students and len(filtered_students) != 0:
            student = random.choice(filtered_students)
            assigned_students.append(student)
            shifts_count[student] += 1
            filtered_students.remove(student)  # Remove the chosen student from the list
            assign_count += 1
        
        schedule_entries.append([date, timeslot] + assigned_students)
        row_num += 1
    
    schedule_df = pd.DataFrame(schedule_entries, columns=["Date", "Timeslot"] + [f"Student {i+1}" for i in range(num_students)])
    return(schedule_df)


def load_member_data_csv(filepath):
    """Load member data from the Excel file and prepare it for the assignment process."""
    members_df = pd.read_csv(filepath)
    
    members_df['IsNewbie'] = members_df['IsNewbie'].fillna(0).astype(int)
    members_df['Languages'] = members_df['Language']  # Simplified assumption
    
    member_info = members_df.set_index('Nickname')[['IsNewbie', 'Languages']].to_dict('index')
    return member_info


# Still in development
def assign_shift_b2b(simultaneous_shifts, member_info, num_students=2):
    schedule_entries = []
    shifts_count = {student: 0 for student in member_info.keys()}
    student_assignments = {student: [] for student in member_info.keys()}
    student_daily_locations = {(student, date): None for student in member_info.keys() for date, _, _ in simultaneous_shifts['Shift']}

    for index, row in simultaneous_shifts.iterrows():
        date, timeslot, location = row['Shift']
        available_students = row['Available Students']
        assigned_students = []

        # Sort students by their shift count
        sorted_students = sorted(available_students, key=lambda x: shifts_count[x])

        for student in sorted_students:
            if len(assigned_students) < num_students:
                # Check if the student is already assigned to a shift at a different location on the same day
                if student_daily_locations[(student, date)] is None or student_daily_locations[(student, date)] == location:
                    assigned_students.append(student)
                    shifts_count[student] += 1
                    student_assignments[student].append((date, timeslot, location))
                    student_daily_locations[(student, date)] = location  # Mark the student's location for the day

        assigned_students += [None] * (num_students - len(assigned_students))
        
        # Available students as a string for easier comparison
        available_students_str = ', '.join(available_students)
        
        schedule_entries.append([date, timeslot, location] + assigned_students + [f"{assigned_students[0]}, {assigned_students[1]}"] + [available_students_str])

    columns = ["Date", "Timeslot", "Location"] + [f"Student {i+1}" for i in range(num_students)] + ["Students"] + ["Available Students"]
    schedule_df = pd.DataFrame(schedule_entries, columns=columns)
    
    return schedule_df

def swap_student_positions(schedule_df, num_students=2):
    """Assign students a consistent 'left' or 'right' position and swap their places in the schedule."""
    # Assign each student a position
    student_positions = {}
    for student in pd.unique(schedule_df[[f"Student {i+1}" for i in range(num_students)]].values.ravel('K')):
        if student is not None and student not in student_positions:
            student_positions[student] = random.choice(['left', 'right'])

    # Swap positions in the schedule based on assigned positions
    for index, row in schedule_df.iterrows():
        students = [row[f"Student {i+1}"] for i in range(num_students)]
        swapped_students = []
        
        for student in students:
            if student in student_positions:
                if student_positions[student] == 'right':
                    swapped_students.append(student)
                else:
                    swapped_students.insert(0, student)
            else:
                swapped_students.append(student)
        
        for i, student in enumerate(swapped_students):
            schedule_df.at[index, f"Student {i+1}"] = student

    return schedule_df

def calculate_assigned_shifts(schedule, applied_shifts, num_students=2):
    """Calculate the number of assigned shifts for each student and overall statistics."""
    # Flatten the DataFrame and filter out non-student entries
    assigned_counts = schedule[[f"Student {i+1}" for i in range(num_students)]].stack().value_counts()

    # Create the individual statistics DataFrame
    individual_stats_df = pd.DataFrame({
        "Applied": applied_shifts,
        "Assigned": assigned_counts
    })

    # Ensure all students are included in stats, even if they have 0 assigned shifts
    all_students = set(applied_shifts.index)
    missing_students = all_students - set(assigned_counts.index)
    for student in missing_students:
        individual_stats_df.loc[student, "Assigned"] = 0

    # Calculate the success rate for individuals
    individual_stats_df["Rate (%)"] = np.round((individual_stats_df["Assigned"] / individual_stats_df["Applied"] * 100).fillna(0), 1)
    individual_stats_df = individual_stats_df.fillna(0).astype({'Assigned': 'int32', 'Applied': 'int32', 'Rate (%)': 'float'})
    
    # Calculate overall statistics and create a DataFrame for them
    overall_stats_df = pd.DataFrame({
        'Mean Assigned': [np.mean(assigned_counts)],
        'Variance Assigned': [np.var(assigned_counts, ddof=0)],  # ddof=0 for population variance
        'Std Dev Assigned': [np.std(assigned_counts, ddof=0)]    # ddof=0 for population standard deviation
    })

    return individual_stats_df.sort_values(by="Rate (%)", ascending=False), overall_stats_df