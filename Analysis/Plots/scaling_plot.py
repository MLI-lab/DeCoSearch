import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter

# Set plot style for publication-quality figures
sns.set_style('whitegrid')

# Enable LaTeX rendering for text
import matplotlib
matplotlib.rcParams['text.usetex'] = True

# Define paths to the checkpoint folders grouped by configuration
checkpoint_dirs = {
    "5GPUs_450CPUs": [
        "Checkpoints_T0.5",
        "Checkpoints_T2",
        "Checkpoints_T0.1",
    ],
    "6GPUs_540CPUs": [
        "Checkpoints_500p",
        "Checkpoints_exp",
        "Checkpoints_8h",
    ],
    "4GPUs_360CPUs": [
        "Checkpoints_2h",
    ],
    "7GPUs_630CPUs": [
        "7GPUs",
    ],
}

# Initialize data structure to store total programs for each configuration
data = {config: [] for config in checkpoint_dirs.keys()}

# Function to load total programs from each checkpoint
def load_total_programs(file_path):
    with open(file_path, "rb") as f:
        checkpoint_data = pickle.load(f)
        execution_failed = checkpoint_data.get('execution_failed', 0)
        total_programs = checkpoint_data.get('total_programs', 0) + execution_failed
        return total_programs

# Process each configuration
for config, dir_paths in checkpoint_dirs.items():
    all_runs = []  # To store all runs for the configuration
    max_length = 0

    for dir_path in dir_paths:
        run_total_programs = []
        # Process all files in the directory
        for filename in sorted(os.listdir(dir_path)):
            if filename.startswith("checkpoint_") and filename.endswith(".pkl"):
                file_path = os.path.join(dir_path, filename)
                run_total_programs.append(load_total_programs(file_path))
        all_runs.append(run_total_programs)
        max_length = max(max_length, len(run_total_programs))

    # Align runs dynamically
    extended_runs = []
    for run in all_runs:
        extended_run = run + [np.nan] * (max_length - len(run))  # Use NaN for missing values
        extended_runs.append(extended_run)

    # Convert to numpy array for easier processing
    extended_runs = np.array(extended_runs)
    
    # Compute mean and std dynamically ignoring NaN values
    mean_programs = np.nanmean(extended_runs, axis=0)
    std_programs = np.nanstd(extended_runs, axis=0)

    # Store the aggregated data
    data[config] = {
        "mean": mean_programs,
        "std": std_programs,
        "iterations": range(max_length),
    }a

# Plotting total programs with error bars for scaling investigation
plt.figure(figsize=(10, 6))

# Define color palette for configurations
colors = {
    "5GPUs_450CPUs": "blue",
    "6GPUs_540CPUs": "orange",
    "4GPUs_360CPUs": "green",
    "7GPUs_630CPUs": "red",
}

for config, config_data in data.items():
    plt.plot(config_data["iterations"], config_data["mean"], 
             linestyle='-', color=colors[config], label=f"{config} (Mean)")
    plt.fill_between(config_data["iterations"], config_data["mean"] - config_data["std"], 
                     config_data["mean"] + config_data["std"], 
                     color=colors[config], alpha=0.2, label=f"{config} (Std)")

# Customize the y-axis to show values scaled by 10^6
plt.gca().yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
plt.ticklabel_format(axis="y", style="sci", scilimits=(6, 6))

# Axis labels, title, and legend
plt.xlabel("Iterations", fontsize=14)
plt.ylabel("Total Programs Generated ($\\times 10^6$)", fontsize=14)
plt.title("Scaling with Compute", fontsize=16)
plt.legend(loc="upper right", fontsize=12)
plt.tight_layout()
plt.savefig('scaling.pdf', format='pdf')
plt.show()
