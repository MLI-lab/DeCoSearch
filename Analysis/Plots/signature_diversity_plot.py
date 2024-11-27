import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist
import seaborn as sns  # For setting style

# Set plot style
sns.set_style("whitegrid")

# Define paths to the checkpoint folders
checkpoint_dirs = {
    "T=1": "Checkpoints_T1",
    "T=2": "Checkpoints_T2",
    "T=0.5": "Checkpoints_T0.5",
    "T=0.1": "Checkpoints_T0.1"
}

# Initialize data structure to store signature diversity values for each folder
diversity_data = {dir_name: {"all_clusters": [], "improving_clusters": []} for dir_name in checkpoint_dirs}

# Initial program signature and its average for determining improving clusters
initial_signature = (8, 14, 25, 42, 71, 125)
initial_average = sum(initial_signature) / len(initial_signature)

# Function to load signatures and identify improving clusters from each checkpoint
def load_signatures_from_checkpoint(file_path):
    with open(file_path, "rb") as f:
        checkpoint_data = pickle.load(f)
        islands_state = checkpoint_data.get("islands_state", [])
        if not islands_state:
            return [], []  # No data in this checkpoint
        
        all_signatures = []
        improving_signatures = []

        # Collect all signatures as tuples
        for island in islands_state:
            for signature in island["clusters"].keys():
                cluster_signature = eval(signature)
                cluster_average = sum(cluster_signature) / len(cluster_signature)
                all_signatures.append(cluster_signature)
                if cluster_average > initial_average:
                    improving_signatures.append(cluster_signature)
        
        return all_signatures, improving_signatures

# Process each checkpoint directory
for dir_name, dir_path in checkpoint_dirs.items():
    for filename in sorted(os.listdir(dir_path)):
        if filename.startswith("checkpoint_") and filename.endswith(".pkl"):
            file_path = os.path.join(dir_path, filename)
            all_signatures, improving_signatures = load_signatures_from_checkpoint(file_path)
            
            # Calculate diversity for all clusters
            if len(all_signatures) > 1:
                all_array = np.array(all_signatures)
                all_pairwise_distances = pdist(all_array, metric='cityblock')
                all_diversity = np.mean(all_pairwise_distances) / len(all_signatures)  # Normalize by the number of clusters
            else:
                all_diversity = 0
            
            # Calculate diversity for improving clusters
            if len(improving_signatures) > 1:
                improving_array = np.array(improving_signatures)
                improving_pairwise_distances = pdist(improving_array, metric='cityblock')
                improving_diversity = np.mean(improving_pairwise_distances) / len(improving_signatures)  # Normalize by the number of clusters
            else:
                improving_diversity = 0

            # Append diversity scores for this checkpoint
            diversity_data[dir_name]["all_clusters"].append(all_diversity)
            diversity_data[dir_name]["improving_clusters"].append(improving_diversity)

# Plot the diversity over iterations for all folders
plt.figure(figsize=(12, 8))

# Define color palette for consistency with other plots
colors = {"T=1": "blue", "T=2": "orange", "T=0.5": "green", "T=0.1": "purple"}

for dir_name, dir_scores in diversity_data.items():
    # Plot diversity for all clusters
    plt.plot(range(len(dir_scores["all_clusters"])), 
             dir_scores["all_clusters"], 
             linestyle='-', color=colors[dir_name], label=f"{dir_name} (All Clusters)")
    # Plot diversity for improving clusters
    plt.plot(range(len(dir_scores["improving_clusters"])), 
             dir_scores["improving_clusters"], 
             linestyle='--', color=colors[dir_name], label=f"{dir_name} (Improving Clusters)")

# Axis labels, title, and legend
plt.xlabel("Iterations", fontsize=14)
plt.ylabel("Normalized L1 Distance", fontsize=14)
plt.title("Normalized Signature Diversity Over Iterations", fontsize=16)
plt.legend(loc="upper right", fontsize=12)
plt.tight_layout()

# Save and show the plot
plt.savefig('signature_diversity.pdf', format='pdf')
plt.show()
