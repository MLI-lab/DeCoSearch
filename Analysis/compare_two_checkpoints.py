import pickle
import time
import numpy as np

# Load checkpoint data from two files
def load_checkpoint(filepath):
    with open(filepath, "rb") as f:
        checkpoint_data = pickle.load(f)
    if 'last_reset_time' in checkpoint_data:
        checkpoint_data['last_reset_time'] = time.ctime(checkpoint_data['last_reset_time'])
    return checkpoint_data

# Construct the best signature across all islands
def construct_best_signature_across_islands(islands_state):
    all_signatures = []
    for island in islands_state:
        signatures = [tuple(map(int, sig.strip("()").split(","))) for sig in island['clusters'].keys()]
        all_signatures.extend(signatures)
    
    if not all_signatures:
        return None
    global_best_signature = tuple(max(dim) for dim in zip(*all_signatures))
    return global_best_signature

# Compare two signatures
def is_better_signature(sig1, sig2):
    better_indices = [i for i, (a, b) in enumerate(zip(sig1, sig2)) if a > b]
    return bool(better_indices), better_indices

# Generate a unique identifier for a program based on its content
def get_program_signature(program):
    return (program['name'], program['args'], program['body'].strip(), program.get('docstring', '').strip())

# Load checkpoints
checkpoint_file_1 = "/franziska/Funsearch/Analysis/Checkpoints_T0.1/checkpoint_2024-11-19_05-34-07.pkl"
checkpoint_file_2 = "/franziska/Funsearch/Analysis/Checkpoints_T0.1/checkpoint_2024-11-19_06-37-00.pkl"
checkpoint_1 = load_checkpoint(checkpoint_file_1)
checkpoint_2 = load_checkpoint(checkpoint_file_2)

# Dictionary to track changes
changes = {
    "new_clusters_better": {},
    "new_clusters_worse": {},
    "best_program_changes": {}
}

# Extract best scores per island
best_scores_checkpoint_1 = checkpoint_1.get("best_scores_per_test_per_island", [])
best_scores_checkpoint_2 = checkpoint_2.get("best_scores_per_test_per_island", [])

# Construct the global best signature across all islands from the previous checkpoint
global_best_signature = construct_best_signature_across_islands(checkpoint_1['islands_state'])
print(f"Global Best Signature Across All Islands (from previous checkpoint): {global_best_signature}")

# Track all program signatures from the first checkpoint
program_signatures_checkpoint_1 = set()
for island in checkpoint_1['islands_state']:
    for cluster in island['clusters'].values():
        for program in cluster['programs']:
            program_signatures_checkpoint_1.add(get_program_signature(program))

# Process each island
for island_index, (island_1, island_2) in enumerate(zip(checkpoint_1['islands_state'], checkpoint_2['islands_state'])):
    island_name = f"Island {island_index + 1}"
    changes["new_clusters_better"][island_name] = []
    changes["new_clusters_worse"][island_name] = []

    # Track best program changes
    best_program_1 = checkpoint_1.get('best_program_per_island', [None])[island_index]
    best_program_2 = checkpoint_2.get('best_program_per_island', [None])[island_index]
    if get_program_signature(best_program_1) != get_program_signature(best_program_2):
        changes["best_program_changes"][island_name] = {
            "program": best_program_2,
            "signature": best_scores_checkpoint_2[island_index] if island_index < len(best_scores_checkpoint_2) else None
        }

    # Process clusters in the new checkpoint
    clusters_1 = island_1['clusters']
    clusters_2 = island_2['clusters']

    for cluster_signature, cluster_data_2 in clusters_2.items():
        try:
            parsed_signature = tuple(map(int, cluster_signature.strip("()").split(",")))
        except ValueError:
            print(f"Warning: Skipping invalid cluster signature '{cluster_signature}' in {island_name}.")
            continue

        # Check if the new cluster signature is better than the global best signature
        is_better, better_indices = is_better_signature(
            parsed_signature, 
            global_best_signature if global_best_signature else (0,) * len(parsed_signature)
        )
        if is_better:
            changes["new_clusters_better"][island_name].append({
                "cluster_signature": cluster_signature,
                "better_than_indices": better_indices,
                "programs": cluster_data_2['programs']
            })
        else:
            changes["new_clusters_worse"][island_name].append({
                "cluster_signature": cluster_signature,
                "programs": cluster_data_2['programs']
            })

# Write results to a file
output_filepath = "output_comparison.txt"
with open(output_filepath, "w") as output_file:
    output_file.write("New Clusters and Best Programs Comparison\n" + "=" * 50 + "\n")
    output_file.write(f"Global Best Signature Across All Islands (from previous checkpoint): {global_best_signature}\n\n")

    # Write best program changes
    output_file.write("\nBest Program Changes (with Best Scores and Signatures)\n" + "-" * 30 + "\n")
    for island, data in changes["best_program_changes"].items():
        program = data["program"]
        signature = data["signature"]
        output_file.write(f"{island} - New Best Program: Has signature {signature.values()}\n")
        if program:
            program_code = f"def {program['name']}({program['args']}):\n"
            if program['docstring']:
                program_code += f'    """{program["docstring"].strip()}"""\n'
            program_code += program['body'].replace('\n', '\n    ')  # Indent body
            output_file.write(program_code + "\n\n")

    # Write better clusters
    output_file.write("\nNew Clusters (Better Scores and Reasons)\n" + "-" * 30 + "\n")
    for island, clusters in changes["new_clusters_better"].items():
        if clusters:
            output_file.write(f"{island}:\n")
            for cluster in clusters:
                better_indices_str = ", ".join(map(str, cluster["better_than_indices"]))
                output_file.write(f"  Cluster {cluster['cluster_signature']} (Better at indices: {better_indices_str}):\n")
                for program in cluster['programs']:
                    program_signature = get_program_signature(program)
                    if program_signature in program_signatures_checkpoint_1:
                        output_file.write(f"    Occurred in previous checkpoint: {program['name']}({program['args']})\n")
                    else:
                        program_code = f"    def {program['name']}({program['args']}):\n"
                        if program['docstring']:
                            program_code += f'        """{program["docstring"].strip()}"""\n'
                        program_code += program['body'].replace('\n', '\n        ')
                        output_file.write(program_code + "\n")
                output_file.write("\n")

    # Write worse clusters
    output_file.write("\nNew Clusters (Worse Scores)\n" + "-" * 30 + "\n")
    for island, clusters in changes["new_clusters_worse"].items():
        if clusters:
            output_file.write(f"{island}:\n")
            for cluster in clusters:
                output_file.write(f"  Cluster {cluster['cluster_signature']}:\n")
                for program in cluster['programs']:
                    program_signature = get_program_signature(program)
                    if program_signature in program_signatures_checkpoint_1:
                        output_file.write(f"    Occurred in previous checkpoint: {program['name']}({program['args']})\n")
                    else:
                        program_code = f"    def {program['name']}({program['args']}):\n"
                        if program['docstring']:
                            program_code += f'        """{program["docstring"].strip()}"""\n'
                        program_code += program['body'].replace('\n', '\n        ')
                        output_file.write(program_code + "\n")
                output_file.write("\n")

print(f"Comparison results written to {output_filepath}")
