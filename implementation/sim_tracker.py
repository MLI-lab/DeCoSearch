import os
import time
import pickle
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
from datetime import datetime
from similarity import compare_one_code_similarity_with_protection  # Import your similarity function

# Set CHECKPOINT_DIR to the current directory
CHECKPOINT_DIR = os.getcwd()

# Define the output file path for similarity plot
HTML_OUTPUT_PATH = os.path.join(CHECKPOINT_DIR, "similarity_over_time.html")

# Function to calculate the similarity matrix using your similarity function
def compute_similarity_matrix(programs, similarity_type, protected_vars):
    n = len(programs)
    similarity_matrix = np.zeros((n, n))
    if n == 1:
        return np.array([[1]])  # Edge case: only one program
    for i in range(n):
        for j in range(n):
            if i <= j:  # Only compute upper triangle and diagonal
                similarity_matrix[i, j] = compare_one_code_similarity_with_protection(programs[i], programs[j], similarity_type, protected_vars)
                similarity_matrix[j, i] = similarity_matrix[i, j]  # Symmetric matrix
    return similarity_matrix

# Function to generate heatmap data for all clusters in an island at a specific time
def generate_heatmap_data(island_state, similarity_type, protected_vars, timestamp):
    traces = []
    visibility = []
    cluster_labels = []

    # Iterate over islands and clusters
    for island_idx, island in enumerate(island_state, start=1):
        clusters = island['clusters']
        for cluster_key, cluster_info in clusters.items():
            print(f"Creating heatmap for {cluster_key} in Island {island_idx}")
            programs = cluster_info.get('programs', [])
            if len(programs) > 0:  # Only generate heatmap if there are programs
                similarity_matrix = compute_similarity_matrix(programs, similarity_type, protected_vars)
                
                # Create a heatmap trace for this cluster
                trace = go.Heatmap(
                    z=similarity_matrix,
                    x=[f'Program {i+1}' for i in range(len(programs))],
                    y=[f'Program {i+1}' for i in range(len(programs))],
                    colorscale='YlGnBu',
                    zmin=0, zmax=1,  # Fix the colormap between 0 and 1
                    colorbar=dict(tickvals=[0, 0.25, 0.5, 0.75, 1]),
                    visible=True,  # Set visibility to True initially for testing
                    name=f'Cluster {cluster_key} - Island {island_idx}'
                )
                traces.append(trace)
                visibility.append((island_idx, timestamp))  # Track both island and timestamp for visibility
                cluster_labels.append(f'Cluster {cluster_key} - Island {island_idx}')
        print(f"Number of heatmaps created: {len(traces)}")

    return traces, visibility, cluster_labels


# Function to update visualization with checkpoint data over time
def update_visualization_with_time(checkpoint_files, checkpoint_timestamps, similarity_type, protected_vars):
    frames = []  # List to store animation frames
    for idx, checkpoint_file in enumerate(checkpoint_files):
        with open(os.path.join(CHECKPOINT_DIR, checkpoint_file), "rb") as f:
            checkpoint_data = pickle.load(f)
            traces, visibility, cluster_labels = generate_heatmap_data(
                checkpoint_data['islands_state'], similarity_type, protected_vars, checkpoint_timestamps[idx]
            )
            frame = go.Frame(data=traces, name=str(checkpoint_timestamps[idx]))
            frames.append(frame)
    return frames, traces, visibility, cluster_labels


# Create the interactive heatmap with slider and dropdown
def create_heatmap_with_slider_and_dropdown(frames, slider_steps, traces, visibility, cluster_labels, checkpoint_timestamps):
    # Dynamically calculate number of heatmaps (number of clusters)
    num_clusters = len(traces)
    
    if num_clusters == 0:
        print("No heatmaps to display!")
        return

    # Create subplots with one heatmap per subplot
    fig = sp.make_subplots(rows=num_clusters, cols=1, shared_xaxes=True, shared_yaxes=True, subplot_titles=cluster_labels)

    # Add each heatmap trace to its own row in the subplot
    for i, trace in enumerate(traces):
        fig.add_trace(trace, row=i + 1, col=1)  # Place each heatmap in a separate row

    # Slider setup for manual time control
    sliders = [{
        'currentvalue': {"prefix": "Time: "},
        'steps': slider_steps,
        'transition': {'duration': 300, 'easing': 'cubic-in-out'},
        'x': 0, 'y': -0.2,
        'pad': {'b': 10},
        'len': 0.9
    }]

    # Dropdown menu for selecting islands
    buttons = []
    num_islands = max(v[0] for v in visibility)
    for i in range(1, num_islands + 1):
        button = {
            'label': f'Island {i}',
            'method': 'restyle',
            'args': [{
                'visible': [(v[0] == i) for v in visibility]  # Set visibility to True for selected island
            }, {'title': f'Cluster Similarity for Island {i}'}]
        }
        buttons.append(button)

    # Update layout to reflect the number of heatmaps (clusters)
    fig.update_layout(
        sliders=sliders,
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.9, 'y': 1.15,
            'xanchor': 'right',
            'yanchor': 'top'
        }],
        transition={'duration': 500, 'easing': 'cubic-in-out'},
        title='Cluster Similarity Over Time',
        height=400 * num_clusters  # Adjust height based on number of clusters
    )

    # Save the figure as an HTML file
    fig.write_html(HTML_OUTPUT_PATH)
    print(f"Visualization saved to {HTML_OUTPUT_PATH}")


# Monitor for new checkpoint files and continuously update the heatmap
def check_for_new_checkpoints(directory, interval=60, similarity_type='bag_of_nodes', protected_vars=None):
    if protected_vars is None:
        protected_vars = ['node', 'G', 'n', 's']  # Default protected vars
    last_seen_timestamp = None
    checkpoint_files = []
    checkpoint_timestamps = []
    while True:
        try:
            files = [f for f in os.listdir(directory) if f.startswith("checkpoint_") and f.endswith(".pkl")]
            timestamps = []
            for f in files:
                parts = f.split("_")
                timestamp_str = "_".join(parts[1:3]).replace('.pkl', '')
                timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                timestamps.append((timestamp_dt.timestamp(), f))
            sorted_files = sorted(timestamps, key=lambda x: x[0])
            checkpoint_files = [f[1] for f in sorted_files]
            checkpoint_timestamps = [f[0] for f in sorted_files]
            
            # Check if there is a new checkpoint, only update if there is new data
            if checkpoint_files and (last_seen_timestamp is None or max(checkpoint_timestamps) > last_seen_timestamp):
                frames, traces, visibility, cluster_labels = update_visualization_with_time(
                    checkpoint_files, checkpoint_timestamps, similarity_type, protected_vars
                )
                slider_steps = [{'args': [[str(t)], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
                                 'label': datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S'),
                                 'method': 'animate'} for t in checkpoint_timestamps]
                create_heatmap_with_slider_and_dropdown(
                    frames, slider_steps, traces, visibility, cluster_labels, checkpoint_timestamps
                )
                last_seen_timestamp = max(checkpoint_timestamps)
        except Exception as e:
            print(f"Error while checking for new checkpoints: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    print(f"Monitoring new checkpoints in directory: {CHECKPOINT_DIR}")
    check_for_new_checkpoints(CHECKPOINT_DIR)
