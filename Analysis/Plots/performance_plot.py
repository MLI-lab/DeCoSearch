import os
import pickle
import matplotlib.pyplot as plt

import seaborn as sns

# Use LaTeX for rendering text and ensure it matches the document style
plt.rcParams.update({
    "text.usetex": True,  # Use LaTeX for all text rendering
    "font.family": "serif",  # Use LaTeX's default serif font
    "font.serif": ["Computer Modern Roman"],
    "font.size": 11,  # Match the document's font size
    "axes.titlesize": 11,
    "axes.labelsize": 11,
    "legend.fontsize": 9,  # Slightly smaller legend text size
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "axes.linewidth": 0.5,  # Match typical LaTeX line width
    "lines.linewidth": 0.75,  # Match LaTeX default line width for figures
    #"text.latex.preamble": r"\usepackage{amsmath, amssymb, bm}",  # Include packages used in your LaTeX document
})

# Set plot style consistent with LaTeX documents
sns.set_style("whitegrid")

# Define the path to the checkpoint directory
checkpoint_dir = "/franziska/Funsearch/Analysis/Checkpoints_Prompt3_detailed"

# Initialize dictionaries to store performance scores and registered programs for each island
performance_data = {}
registered_programs_data = []

optimal = {
    "last": 172, 
    "average": 62.34,
    "exp": 120.413
}

# Function to load performance data and registered programs from a checkpoint
def load_checkpoint_data(file_path):
    with open(file_path, "rb") as f:
        checkpoint_data = pickle.load(f)
        # Extract scores for all islands
        scores = checkpoint_data.get("best_score_per_island", [])
        registered_programs = checkpoint_data.get("registered_programs", 0)
        return scores, registered_programs

# Process the checkpoint directory
file_names = sorted([
    f for f in os.listdir(checkpoint_dir) 
    if f.startswith("checkpoint_") and f.endswith(".pkl")
])

for file_name in file_names:
    file_path = os.path.join(checkpoint_dir, file_name)
    island_scores, registered_programs = load_checkpoint_data(file_path)
    
    # Store scores for each island
    for island_idx, score in enumerate(island_scores):
        if island_idx not in performance_data:
            performance_data[island_idx] = []
        performance_data[island_idx].append(score)
    
    # Store registered programs count for the x-axis
    registered_programs_data.append(registered_programs)

# Plot the performance scores for each island
plt.figure(figsize=(6.5, 3.9))  # Match \textwidth (6.5 inches) and proportionate height

# Define color palette for islands
colors = sns.color_palette("tab10", len(performance_data))  # Use a tab10 color palette

for island_idx, scores in performance_data.items():
    plt.plot(
        registered_programs_data,
        scores,
        linestyle='-',  # Keep the line style as solid
        marker='o',     # Add circle markers
        markersize=4,   # Set marker size to 4pt
        label=rf"Island {island_idx + 1}",  # Corrected label formatting
        color=colors[island_idx]
    )


# Add a horizontal dashed black line for the "last" optimal value and annotate it
plt.axhline(optimal["last"], color='black', linestyle='--',  linewidth=0.75)
plt.text(
    x=-1,  # Place the label slightly to the left of the maximum x-axis value
    y=optimal["last"],  # Align exactly with the horizontal line
    s=r"$VT_0$ score",  # LaTeX formatting for the label
    color="black",
    fontsize=11,
    ha="right",
    va="center"
)

# Axis labels, title, and legend
plt.xlabel(rf"Registered Programs")  # LaTeX-rendered labels
plt.ylabel(rf"Performance Score")
# Adjusted legend position
plt.legend(
    loc="upper left",  # Position relative to the bounding box
    bbox_to_anchor=(0.0, 0.9),  # Adjust the y-coordinate to move the legend down
    fontsize=9,
    title_fontsize=10,
    frameon=True,
    handlelength=1.5
)

plt.tight_layout()

# Save the plot as a PDF
output_path = "performance.pdf"
plt.savefig(output_path, format='pdf')

# Show the plot
plt.show()

print(f"Plot saved as {output_path}")
