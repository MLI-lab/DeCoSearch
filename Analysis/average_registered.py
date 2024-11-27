import os
import pickle
import time

# Define the path to the checkpoint directory
checkpoint_dir = "/franziska/Funsearch/Analysis/Checkpoints_T0.1"

# Initialize variables for tracking resets and registered programs
reset_periods = []
current_reset_time = None
registered_programs_in_period = []
registered_programs_by_island = []
total_islands = 0

# Function to load registered programs and last reset time from a checkpoint
def load_checkpoint_data(file_path):
    with open(file_path, "rb") as f:
        checkpoint_data = pickle.load(f)
        # Extract last reset time and islands state
        last_reset_time = checkpoint_data.get("last_reset_time", None)
        islands_state = checkpoint_data.get("islands_state", [])
        registered_programs = [
            island.get("num_programs", 0) for island in islands_state
        ]
        return last_reset_time, registered_programs, len(islands_state)

# Process the checkpoint directory
file_names = sorted([
    f for f in os.listdir(checkpoint_dir) 
    if f.startswith("checkpoint_") and f.endswith(".pkl")
])

for file_name in file_names:
    file_path = os.path.join(checkpoint_dir, file_name)
    last_reset_time, registered_programs, num_islands = load_checkpoint_data(file_path)

    # Convert reset time to human-readable format if not None
    if last_reset_time is not None:
        last_reset_time = time.ctime(last_reset_time)

    # Check if a reset has occurred
    if current_reset_time is None or last_reset_time != current_reset_time:
        # Store the registered programs for the previous period
        if registered_programs_by_island:
            reset_periods.append(registered_programs_by_island)
            registered_programs_by_island = []

        # Update the current reset time
        current_reset_time = last_reset_time

    # Accumulate registered programs for the current reset period by island
    registered_programs_by_island.append(registered_programs)
    total_islands = max(total_islands, num_islands)  # Track max islands

# Include the last period if not already added
if registered_programs_by_island:
    reset_periods.append(registered_programs_by_island)

# Compute average and variance
if reset_periods and total_islands > 0:
    # Variance within each reset period
    within_period_variances = []
    for period in reset_periods:
        period_totals = [sum(island) for island in period]
        period_mean = sum(period_totals) / len(period_totals)
        period_variance = sum((x - period_mean) ** 2 for x in period_totals) / len(period_totals)
        within_period_variances.append(period_variance)

    # Variance between reset periods
    period_sums = [sum(sum(island) for island in period) for period in reset_periods]
    overall_mean = sum(period_sums) / len(period_sums)
    between_period_variance = sum((x - overall_mean) ** 2 for x in period_sums) / len(period_sums)

    print(f"Average variance within reset periods: {sum(within_period_variances) / len(within_period_variances):.2f}")
    print(f"Variance between reset periods: {between_period_variance:.2f}")
else:
    print("No data available to compute variances.")
