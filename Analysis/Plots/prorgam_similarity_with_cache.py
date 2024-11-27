import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor
from sim import compare_one_code_similarity_with_protection
import random

# Set plot style
sns.set_style("whitegrid")
plt.rcParams.update({
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'figure.figsize': (10, 5),
    'axes.spines.top': False,
    'axes.spines.right': False
})

# Directory to store checkpoint files
CHECKPOINT_DIR = os.path.join(os.getcwd(), "Checkpoints_T0.1")
CACHE_DIR = os.path.join(os.getcwd(), "SimilarityCache01")
os.makedirs(CACHE_DIR, exist_ok=True)

# Helper function to load checkpoint data
def load_checkpoint_data(checkpoint_path):
    with open(checkpoint_path, 'rb') as f:
        checkpoint_data = pickle.load(f)
    return checkpoint_data

# Function to save similarity scores to cache
def save_similarity_cache(timestamp, similarities):
    cache_path = os.path.join(CACHE_DIR, f"similarities_{timestamp}.pkl")
    with open(cache_path, 'wb') as f:
        pickle.dump(similarities, f)

# Function to load similarity scores from cache
def load_similarity_cache(timestamp):
    cache_path = os.path.join(CACHE_DIR, f"similarities_{timestamp}.pkl")
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None

# Function to compare a pair of programs
def compute_similarity_pair(args):
    prog_a, prog_b, similarity_type, protected_vars = args
    return compare_one_code_similarity_with_protection(prog_a, prog_b, similarity_type, protected_vars)

# Function to randomly sample programs from a cluster
def sample_programs(cluster, sample_size=10):
    programs = cluster.get('programs', [])
    if len(programs) > sample_size:
        return random.sample(programs, sample_size)
    return programs

# Function to compute similarities within an island (with random sampling)
def compute_island_similarities_with_sampling(island_data, similarity_type, protected_vars, sample_size=10):
    clusters = list(island_data.get('clusters', {}).values())
    all_top_similarities = []

    for i, cluster_a in enumerate(clusters):
        programs_a = sample_programs(cluster_a, sample_size)
        for j in range(i + 1, len(clusters)):
            cluster_b = clusters[j]
            programs_b = sample_programs(cluster_b, sample_size)
            
            # Prepare tasks for parallel program comparison
            tasks = [(prog_a, prog_b, similarity_type, protected_vars) 
                     for prog_a in programs_a for prog_b in programs_b]
            
            # Compute similarities in parallel across program pairs
            with ProcessPoolExecutor(max_workers=20) as executor:
                similarities = list(executor.map(compute_similarity_pair, tasks))
            
            if similarities:
                # Take the top 10 similarities
                all_top_similarities.extend(sorted(similarities, reverse=True)[:10])
    
    return all_top_similarities

# Wrapper function to compute similarities across islands
def compute_across_islands_similarity(checkpoint_path, sample_size=10):
    checkpoint_data = load_checkpoint_data(checkpoint_path)
    islands_state = checkpoint_data.get('islands_state', [])
    similarity_type = 'bag_of_nodes'
    protected_vars = ['node', 'G', 'n', 's']

    # Compute similarities for each island sequentially
    all_top_similarities = []
    for island in islands_state:
        top_similarities = compute_island_similarities_with_sampling(island, similarity_type, protected_vars, sample_size)
        all_top_similarities.extend(top_similarities)

    return all_top_similarities

# Function to process each checkpoint (runs independently in parallel)
def process_checkpoint(checkpoint_file, sample_size=10):
    checkpoint_path = os.path.join(CHECKPOINT_DIR, checkpoint_file)
    timestamp = checkpoint_file.replace("checkpoint_", "").replace(".pkl", "")

    # Try loading from cache first
    cached_similarities = load_similarity_cache(timestamp)
    if cached_similarities is not None:
        print(f"Loaded cached similarities for {timestamp}")
        return timestamp, cached_similarities

    # If not cached, compute and save the similarities
    top_similarities = compute_across_islands_similarity(checkpoint_path, sample_size)
    
    if top_similarities:
        save_similarity_cache(timestamp, top_similarities)  # Save to cache
        print(f"Computed and cached similarities for {timestamp}")
        return timestamp, top_similarities
    return timestamp, []

# Gather similarity data for each checkpoint with multiprocessing
def gather_all_across_islands_similarities(sample_size=10):
    checkpoint_files = sorted([f for f in os.listdir(CHECKPOINT_DIR) if f.startswith("checkpoint_")])
    
    # Use ProcessPoolExecutor to parallelize processing of each checkpoint
    similarities_over_time = {}
    with ProcessPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_checkpoint, checkpoint_files, [sample_size] * len(checkpoint_files)))
        for timestamp, similarities in results:
            similarities_over_time[timestamp] = similarities

    return similarities_over_time

# Plot similarity data
def plot_violin_similarity(similarities_over_time):
    timestamps = list(similarities_over_time.keys())
    similarity_data = list(similarities_over_time.values())
    
    # Prepare data for seaborn plotting
    plot_data = []
    plot_labels = []
    for i, similarities in enumerate(similarity_data):
        plot_data.extend(similarities)
        plot_labels.extend([timestamps[i]] * len(similarities))
    
    # Create violin plot
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.violinplot(x=plot_labels, y=plot_data, inner="box", scale="width", ax=ax, palette="Set2")
    
    # Set plot labels
    ax.set_xlabel("Checkpoint Timestamps", fontsize=12, fontweight='bold')
    ax.set_ylabel("Similarity Scores (Top 10 per Cluster Pair Across All Islands)", fontsize=12, fontweight='bold')
    ax.set_title("Across-Cluster Similarity Score Distribution Across Checkpoints (Aggregated Across Islands)", fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, which='major', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.savefig('program_similarity_temp1.pdf', format='pdf')

# Main function
def main():
    sample_size = 10  # Number of programs to sample
    similarities_over_time = gather_all_across_islands_similarities(sample_size=sample_size)
    plot_violin_similarity(similarities_over_time)

if __name__ == "__main__":
    main()
