import os
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

# Set plot style for publication-quality figures
sns.set_style('whitegrid')

# Enable LaTeX rendering for text
import matplotlib
matplotlib.rcParams['text.usetex'] = True

# Define paths to the checkpoint folders
checkpoint_dirs = {
    "T=1": "Checkpoints_T1",
    "T=2": "Checkpoints_T2",
    "T=0.5": "Checkpoints_T0.5",
    "T=0.1": "Checkpoints_T0.1"
}

# Initialize data structure to store cumulative new clusters formed per reset period
data = {
    key: {"timestamps": [], "cluster_counts": [], "formation_per_period": [], "improving_clusters": [], "programs_per_period": []}
    for key in checkpoint_dirs.keys()
}

# Initial program signature and its average
initial_signature = (8, 14, 25, 42, 71, 125)
initial_average = sum(initial_signature) / len(initial_signature)

# Function to load clusters, improving clusters, reset time, and total programs
def load_clusters_and_reset_time(file_path):
    with open(file_path, "rb") as f:
        checkpoint_data = pickle.load(f)
        islands_state = checkpoint_data.get("islands_state", [])
        last_reset_time = checkpoint_data.get("last_reset_time", None)
        total_programs = checkpoint_data.get("registered_programs", 0)

        # Calculate total clusters and improving clusters
        total_clusters = 0
        improving_clusters = 0
        for island in islands_state:
            for signature in island["clusters"].keys():
                cluster_signature = eval(signature)
                cluster_average = sum(cluster_signature) / len(cluster_signature)
                total_clusters += 1
                if cluster_average > initial_average:
                    improving_clusters += 1

        return total_clusters, improving_clusters, last_reset_time, total_programs

# Process each checkpoint directory
for dir_name, dir_path in checkpoint_dirs.items():
    timestamps = data[dir_name]["timestamps"]
    formation_per_period = data[dir_name]["formation_per_period"]
    improving_per_period = data[dir_name]["improving_clusters"]
    programs_per_period = data[dir_name]["programs_per_period"]

    current_period_cumulative = 0
    current_period_improving = 0
    current_period_programs = 0
    last_reset_time = None

    # Load all checkpoints and count clusters
    for filename in sorted(os.listdir(dir_path)):
        if filename.startswith("checkpoint_") and filename.endswith(".pkl"):
            # Load cluster count, improving cluster count, reset time, and generated programs
            file_path = os.path.join(dir_path, filename)
            total_clusters, improving_clusters, checkpoint_reset_time, total_programs = load_clusters_and_reset_time(file_path)
            
            # If this is the first file, initialize the last_reset_time
            if last_reset_time is None:
                last_reset_time = checkpoint_reset_time

            # Check if a reset happened
            if checkpoint_reset_time != last_reset_time:
                # Store the cumulative counts for the last period and reset the counters
                formation_per_period.append(current_period_cumulative)
                improving_per_period.append(current_period_improving)
                programs_per_period.append(current_period_programs)
                current_period_cumulative = 0  # Reset for new period
                current_period_improving = 0
                current_period_programs = 0
                last_reset_time = checkpoint_reset_time  # Update last reset time

            # Increment cumulative counts for the current period
            current_period_cumulative += total_clusters
            current_period_improving += improving_clusters
            current_period_programs += total_programs

    # Append the final period cumulative counts after finishing the loop
    formation_per_period.append(current_period_cumulative)
    improving_per_period.append(current_period_improving)
    programs_per_period.append(current_period_programs)

# Normalize by total generated programs
for dir_name in checkpoint_dirs.keys():
    data[dir_name]["normalized_clusters"] = [
        (f / p if p > 0 else 0) for f, p in zip(data[dir_name]["formation_per_period"], data[dir_name]["programs_per_period"])
    ]
    data[dir_name]["normalized_improving"] = [
        (i / p if p > 0 else 0) for i, p in zip(data[dir_name]["improving_clusters"], data[dir_name]["programs_per_period"])
    ]

# Plotting normalized cumulative new clusters formed per reset period
plt.figure(figsize=(12, 7))

# Define color palette
colors = {"T=1": "blue", "T=2": "orange", "T=0.5": "green", "T=0.1": "purple"}

# Plot each folder’s normalized cumulative clusters with custom labels
for dir_name, dir_data in data.items():
    plt.plot(range(len(dir_data["normalized_clusters"])), 
             dir_data["normalized_clusters"], linestyle='-', color=colors[dir_name])
    plt.plot(range(len(dir_data["normalized_improving"])), 
             dir_data["normalized_improving"], linestyle='--', color=colors[dir_name])

# Axis labels, title, and legend
plt.xlabel("Reset Periods", fontsize=14)
plt.ylabel("Normalized Cluster Count per Program", fontsize=14)
plt.title("Normalized Cluster Formation Across Reset Periods", fontsize=16)
# Simplified legend
custom_lines = [plt.Line2D([0], [0], color='black', linestyle='-', lw=2, label='All Clusters'),
                plt.Line2D([0], [0], color='black', linestyle='--', lw=2, label='Improving Clusters')]
color_legend = [plt.Line2D([0], [0], color=color, lw=2, label=f"{dir_name}") for dir_name, color in colors.items()]
plt.legend(handles=custom_lines + color_legend, loc="upper right", fontsize=12)

plt.tight_layout()
plt.savefig('new_cluster_formation.pdf', format='pdf')
