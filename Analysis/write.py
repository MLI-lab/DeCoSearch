import pickle
import time
import os

# Load the checkpoint data
filepath = "/franziska/Funsearch/Analysis/Checkpoints_T0.5/checkpoint_2024-11-23_16-02-36.pkl"
with open(filepath, "rb") as f:
    checkpoint_data = pickle.load(f)

# Convert the 'last_reset_time' if it exists
if 'last_reset_time' in checkpoint_data:
    checkpoint_data['last_reset_time'] = time.ctime(checkpoint_data['last_reset_time'])

# Define the output filepath
output_filepath = "/franziska/Funsearch/Analysis/checkpoint_full.txt"

# Dictionary to track previously seen programs and their original locations
seen_programs = {}

# Function to generate a unique identifier for a program based on its content
def get_program_signature(program):
    return (program['name'], program['args'], program['body'].strip(), program.get('docstring', '').strip())

# Write the checkpoint data to a text file in a readable format
with open(output_filepath, "w") as output_file:
    output_file.write(f"Checkpoint Data\n{'=' * 30}\n")
    output_file.write(f"Registered Programs: {checkpoint_data.get('registered_programs', 0)}\n")
    output_file.write(f"Total Programs: {checkpoint_data.get('total_programs', 0)}\n")
    output_file.write(f"Execution Failed: {checkpoint_data.get('execution_failed', 0)}\n")
    output_file.write(f"Best Score per Island: {checkpoint_data.get('best_score_per_island', [])}\n")
    output_file.write(f"Best Scores per Test per Island: {checkpoint_data.get('best_scores_per_test_per_island', [])}\n")
    output_file.write(f"Last Reset Time: {checkpoint_data.get('last_reset_time', 'N/A')}\n\n")
    
    # Format and print the best programs per island
    output_file.write("\nBest Program per Island\n" + "=" * 30 + "\n")
    for i, program in enumerate(checkpoint_data.get('best_program_per_island', [])):
        output_file.write(f"\nIsland {i + 1} Best Program:\n")
        
        if program:
            program_signature = get_program_signature(program)
            if program_signature in seen_programs:
                # Reference to the first occurrence of the program
                first_occurrence = seen_programs[program_signature]
                output_file.write(f"  Same as Island {first_occurrence[0] + 1} (first occurred in cluster {first_occurrence[1]}).\n")
            else:
                # Add the program to the seen dictionary and print it
                seen_programs[program_signature] = (i, None)  # Store island index and None for no cluster reference
                program_code = f"def {program['name']}({program['args']}):\n"
                if program['docstring']:
                    program_code += f'    """{program["docstring"].strip()}"""\n'
                program_code += program['body'].replace('\n', '\n    ')  # Indent body
                output_file.write(program_code + "\n")
        else:
            output_file.write("  No best program recorded for this island.\n")

    output_file.write("Islands State\n" + "=" * 30 + "\n")
    
    for i, island in enumerate(checkpoint_data['islands_state']):
        output_file.write(f"\nIsland {i + 1} with {island['num_programs']} programs registered and version {island['version']}:\n")
        
        for cluster_signature, cluster_data in island["clusters"].items():
            output_file.write(f"  Cluster {cluster_signature} with score {cluster_data['score']}:\n")
            
            for program in cluster_data["programs"]:
                program_signature = get_program_signature(program)
                if program_signature in seen_programs:
                    # Reference to the first occurrence of the program
                    first_occurrence = seen_programs[program_signature]
                    output_file.write(f"  Same as Island {first_occurrence[0] + 1} (first occurred in cluster {first_occurrence[1]}).\n")
                else:
                    # Add the program to the seen dictionary and print it
                    seen_programs[program_signature] = (i, cluster_signature)
                    program_code = f"def {program['name']}({program['args']}):\n"
                    if program['docstring']:
                        program_code += f'    """{program["docstring"].strip()}"""\n'
                    program_code += program['body'].replace('\n', '\n    ')  # Indent body
                    output_file.write(program_code + "\n")

print(f"Checkpoint data written to {output_filepath}")
