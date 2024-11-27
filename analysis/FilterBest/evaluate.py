import itertools
import numpy as np
import time
import os
from multiprocessing import Pool
import networkx as nx

def priority(node, G, n, s):
    """Priority function as provided."""
    l = [len(v) - 1 for v in list(nx.all_neighbors(G, node))]
    max_l = max(l) if l else -float("Inf")  # Handle empty list

    def calc_p():
        return (-(max_l - (s)) *
                sum([(n - i) * (i + 1) * int(bit == "1") 
                     for bit, i in zip(reversed(list(node)), range(len(node)))])
                + sum(l) / 5)

    p = ((calc_p() * 4 // len(node)) +
         int(('1' * (s + 1) + "0" + node[len(node) >> 1:]) != ("0" * (n - s)) + (node[:s])) *
         (sum(l) // 7)) / 10

    if not bool(p % 1 or type(p) != int):
        p += np.random.rand() / 1e8

    return p

def has_common_subsequence(seq1, seq2, n, s):
    """Check if two sequences share a common subsequence of length n - s."""
    threshold = n - s
    if threshold <= 0:
        return True
    prev = [0] * (n + 1)
    current = [0] * (n + 1)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                current[j] = prev[j - 1] + 1
            else:
                current[j] = max(prev[j], current[j - 1])
            if current[j] >= threshold:
                return True
        prev, current = current, prev
    return False

def check_neighbors(args):
    """Helper function for parallel neighbor checking."""
    current_node, candidate_node, n, s = args
    if has_common_subsequence(current_node, candidate_node, n, s):
        return candidate_node
    return None

def greedy_independent_set(n, s, num_workers=4, checkpoint_file="checkpoint.txt"):
    """Greedy algorithm to find an independent set with parallelized edge evaluation."""
    # Load from checkpoint if it exists
    if os.path.exists(checkpoint_file):
        print(f"Resuming from checkpoint {checkpoint_file}...")
        with open(checkpoint_file, "r") as f:
            lines = f.readlines()
            independent_set = set(lines[0].strip().split(","))
            remaining_nodes = set(lines[1].strip().split(","))
    else:
        # Generate all nodes (binary strings of length n)
        sequences = [''.join(seq) for seq in itertools.product('01', repeat=n)]
        # Sort nodes by priority (highest first)
        remaining_nodes = set(sequences)
        independent_set = set()

    # Initialize graph object for priority function
    G = nx.Graph()
    for node in remaining_nodes:
        G.add_node(node)

    # Compute priorities once for all nodes
    priorities = {node: priority(node, G, n, s) for node in remaining_nodes}

    # Greedy construction of the independent set
    while remaining_nodes:
        # Pick the highest-priority node
        current_node = max(remaining_nodes, key=lambda x: priorities[x])
        independent_set.add(current_node)
        remaining_nodes.remove(current_node)

        # Parallel neighbor exclusion
        with Pool(num_workers) as pool:
            neighbors = pool.map(
                check_neighbors,
                [(current_node, candidate, n, s) for candidate in remaining_nodes]
            )
        neighbors = {node for node in neighbors if node}  # Remove None values
        remaining_nodes -= neighbors

        # Save progress to checkpoint
        with open(checkpoint_file, "w") as f:
            f.write(",".join(independent_set) + "\n")
            f.write(",".join(remaining_nodes) + "\n")

        print(f"Added node {current_node}. Independent set size: {len(independent_set)}. Remaining nodes: {len(remaining_nodes)}")

    return independent_set

if __name__ == "__main__":
    n = 21
    s = 1
    num_workers = 45  # Use all available CPUs
    start_time = time.time()
    independent_set = greedy_independent_set(n, s, num_workers=num_workers, checkpoint_file="checkpoint_n18.txt")
    elapsed_time = time.time() - start_time
    print(f"N={n}, s={s} | Independent set size: {len(independent_set)} | Computed in {elapsed_time:.2f} seconds")
