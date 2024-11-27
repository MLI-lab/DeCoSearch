# Funsearch

---

## Command-line Arguments
1. **`--spec-path` (Required)**  
   - **Description**: Path to the specification file from which the prompt is build.  
   - **Usage**:  
     ```bash
     python funsearch.py --spec-path /path/to/specification.txt
     ```

2. **`--backup` (Optional)**  
   - **Description**: Enables backup of all Python files in the working directory before starting the task.  
   - **Usage**:  
     ```bash
     python your_script.py --backup
     ```
   - **Backup Location**:  
     Backups are saved in `/mnt/hdd_pool/userdata/franziska/code_backups` with a timestamped subdirectory.

3. **`--dynamic-scaling` (Optional)**  
   - **Description**: Enables dynamic scaling of evaluators and samplers based on system resources and message queue load.  
   - **Usage**:  
     ```bash
     python your_script.py --dynamic-scaling
     ```

---
## Dynamic Scaling Logic

The **dynamic scaling controller** adjusts the number of evaluator and sampler processes dynamically based on:

### CPU Load
- If the system's 5-minute load average exceeds the number of available CPU cores, processes are scaled down.
- **Evaluator processes** are terminated until:
  - The load drops below or equals the CPU core count.
  - The minimum number of evaluators (`min_evaluators`, default: 1) is reached.

### Queue Metrics

#### Evaluator Queue
- If the queue contains more messages than the `evaluator_threshold` (default: 5), additional evaluator processes are started **if more than 4 CPUs have less than 50% usage**.
- Evaluators are scaled down if:
  - The message count falls below the threshold.
  - A process with CPU usage below 20% is identified.

#### Sampler Queue
- Additional samplers are started if:
  - The queue contains more messages than the `sampler_threshold` (default: 15).
  - A GPU with the following conditions is available:
    - **At least 32 GiB of free memory.**
    - **Less than 50% utilization.**
- **Multiple GPUs Condition**:
  - If no single GPU meets the criteria, multiple GPUs are combined if their total free memory is at least **32 GiB**.
- Samplers are scaled down if:
  - The message count drops below the threshold.
  - A process with GPU utilization below 10% is identified.


