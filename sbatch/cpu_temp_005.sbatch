#!/bin/bash
#SBATCH -p lrz-cpu 
#SBATCH --qos=cpu   
#SBATCH --nodes=1
#SBATCH --nodelist=cpu-003  # Request specific node
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH -o Temp_005/enroot_test2.out  
#SBATCH -e Temp_005/enroot_test2.err  
#SBATCH --time=48:00:00  

# Get the list of allocated nodes
NODE_LIST=($(scontrol show hostnames $SLURM_JOB_NODELIST)) || { echo "Error fetching node list"; exit 1; }
echo "Allocated nodes: ${NODE_LIST[@]}"

# Use the first node for RabbitMQ
NODE_1="${NODE_LIST[0]}"
RABBITMQ_HOSTNAME=$(srun -N1 -n1 --nodelist="$NODE_1" hostname -f) || { echo "Error getting RabbitMQ hostname"; exit 1; }
echo "RabbitMQ server hostname: $RABBITMQ_HOSTNAME"

# Create a list of times from 200 to 300 with a step of 30 seconds
scaling_intervals_e=($(seq 200 30 300))

# Run tasks on all allocated nodes
for i in "${!NODE_LIST[@]}"; do
    node="${NODE_LIST[$i]}"
    scaling_time_e="${scaling_intervals_e[$i % ${#scaling_intervals_e[@]}]}"

    srun --exclusive -N1 -n1 --nodelist="$node" \
        --container-mounts=/dss/dsshome1/02/di38yur/Temp_005:/workspace/main/,/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/models/:/workspace/models/,/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/sandbox/Temp_005/:/workspace/sandboxstorage/\
        --container-image=/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/enroot/fw.sqsh \
        bash -c "
            echo 'Running on $(hostname -f)'
            cd /workspace/main || { echo 'Error changing to /workspace/main'; exit 1; }

            # Log the user running the script
            whoami || { echo 'Error checking user'; exit 1; }

            # Log the permissions and ownership of the directory
            ls -ld /workspace/models/ || { echo 'Error checking directory permissions'; exit 1; }

            # Ensure the directory has the right permissions, recursively
            chmod -R 750 /workspace/models/ || { echo 'Error setting directory permissions'; exit 1; }

            # Log the mount status
            mount | grep /workspace || { echo 'Error checking mount status'; exit 1; }

            pip install nvidia-ml-py3 || { echo 'Error installing nvidia-ml-py3 on Node 2'; exit 1; }

            # Run funsearch_e in the background
            python /workspace/main/funsearch_cpu.py --check_interval_eval $scaling_time_e || { echo 'Error running funsearch_e.py'; exit 1; } &
            
            wait
        " &
done

wait  # Wait for all background tasks to complete
