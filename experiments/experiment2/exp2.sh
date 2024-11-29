#!/bin/bash
#SBATCH -p mcml-hgx-a100-80x4
#SBATCH --qos=mcml
#SBATCH --nodes=2
#SBATCH --mem=200GB
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=92
#SBATCH --gres=gpu:4
#SBATCH -o /dss/dsshome1/02/di38yur/Funsearch/experiments/experiment2/logs/experiment2.out
#SBATCH -e /dss/dsshome1/02/di38yur/Funsearch/experiments/experiment2/logs/experiment2.err
#SBATCH --time=48:00:00

# Second job component (CPU node)
#SBATCH hetjob
#SBATCH -p lrz-cpu
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --mem=100GB
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=20
#SBATCH -o /dss/dsshome1/02/di38yur/Funsearch/experiments/experiment2/logs/experiment2_cpu.out
#SBATCH -e /dss/dsshome1/02/di38yur/Funsearch/experiments/experiment2/logs/experiment2_cpu.err
#SBATCH --time=48:00:00


# Debugging SLURM variables
echo "SLURM_NODELIST_HET_GROUP_0: $SLURM_JOB_NODELIST_HET_GROUP_0"
echo "SLURM_NODELIST_HET_GROUP_1: $SLURM_JOB_NODELIST_HET_GROUP_1"

# Extract node lists for GPU and CPU groups
GPU_NODE_LIST=($(scontrol show hostnames $SLURM_JOB_NODELIST_HET_GROUP_0)) || { echo "Error fetching GPU node list"; exit 1; }
CPU_NODE_LIST=($(scontrol show hostnames $SLURM_JOB_NODELIST_HET_GROUP_1)) || { echo "Error fetching CPU node list"; exit 1; }

echo "Allocated GPU nodes: ${GPU_NODE_LIST[@]}"
echo "Allocated CPU nodes: ${CPU_NODE_LIST[@]}"

# Assign GPU_1 and remaining GPUs
GPU_1=${GPU_NODE_LIST[0]} || { echo "Error assigning GPU_1"; exit 1; }
REMAINING_GPU=("${GPU_NODE_LIST[@]:1}")

echo "Primary GPU node: $GPU_1"
echo "Remaining GPU nodes: ${REMAINING_GPU[@]}"


# Experiment-specific variables
EXPERIMENT_NAME="experiment2"
EXPERIMENT_DIR="/dss/dsshome1/02/di38yur/Funsearch/experiments/$EXPERIMENT_NAME"
SANDBOX_DIR=/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/sandbox/$EXPERIMENT_NAME/
CONFIG_NAME="config.py"
CONFIG_ATTACH_NAME="config_attach.py"
RABBITMQ_CONF="rabbitmq.conf"
PORT=15691

# Ensure logs and checkpoints directories exist
mkdir -p $EXPERIMENT_DIR/logs || { echo 'Error creating logs directory'; exit 1; }
mkdir -p $EXPERIMENT_DIR/Checkpoints || { echo 'Error creating checkpoints directory'; exit 1; }
mkdir -p $SANDBOX_DIR

# Get RabbitMQ hostname
RABBITMQ_HOSTNAME=$(srun -N1 -n1 --nodelist=$GPU_1 hostname -f) || { echo "Error getting RabbitMQ hostname"; exit 1; }
echo "RabbitMQ server hostname: $RABBITMQ_HOSTNAME"

# Run the main setup process on Node 1
srun -N1 -n1 --nodelist=$GPU_1 \
     --container-mounts=$EXPERIMENT_DIR:/experiment/,\
/dss/dsshome1/02/di38yur/Funsearch/implementation:/Funsearch/implementation/,\
/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/models/:/workspace/models/,\
$SANDBOX_DIR:/workspace/sandboxstorage/ \
     --container-image=/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/enroot/fw.sqsh \
     bash -c "
         echo 'Running on $(hostname -f)'
         cd /experiment || { echo 'Error changing to /experiment'; exit 1; }

         # Install dependencies
         pip install nvidia-ml-py3 dash plotly numpy scikit-learn zss || { echo 'Error installing dependencies'; exit 1; }

         # Update the RabbitMQ configuration with the hostname
         python /Funsearch/implementation/update_config_file.py /experiment/$CONFIG_NAME \"$RABBITMQ_HOSTNAME\" || { echo 'Error running update_config_file.py'; exit 1; }

         # Configure RabbitMQ environment
         export RABBITMQ_NODENAME=rabbit_${SLURM_JOB_ID}@localhost
         export RABBITMQ_USE_LONGNAME=true
         export RABBITMQ_CONFIG_FILE=/experiment/$RABBITMQ_CONF

         # Ensure proper permissions
         chmod 777 /experiment/$RABBITMQ_CONF || { echo 'Error setting permissions on RabbitMQ config'; exit 1; }
         chmod -R 750 /workspace/models || { echo 'Error setting permissions on /workspace/models'; exit 1; }

         # Start RabbitMQ in the foreground
         echo 'Starting RabbitMQ server...'
         rabbitmq-server &

         # Wait for RabbitMQ to fully start
         sleep 30 || { echo 'Error during sleep waiting for RabbitMQ'; exit 1; }

         # Create the virtual host
         curl -s -u guest:guest -X PUT http://localhost:$PORT/api/vhosts/temp_1 || { echo 'Error creating virtual host'; exit 1; }

         # Create a new RabbitMQ user
         curl -s -u guest:guest -X PUT -d '{\"password\":\"mypassword\",\"tags\":\"administrator\"}' \
             -H 'content-type:application/json' http://localhost:$PORT/api/users/myuser || { echo 'Error creating RabbitMQ user'; exit 1; }

         # Set permissions for the new user on the virtual host
         curl -s -u guest:guest -X PUT -d '{\"configure\":\".*\", \"write\":\".*\", \"read\":\".*\"}' \
             -H 'content-type:application/json' http://localhost:$PORT/api/permissions/temp_1/myuser || { echo 'Error setting permissions'; exit 1; }

         echo 'RabbitMQ setup complete.'

         # Set up reverse SSH tunnel for RabbitMQ management interface
         ssh -R $PORT:localhost:$PORT ge74met@login01.msv.ei.tum.de -p 3022 -N -f || { echo 'Error setting up SSH tunnel'; exit 1; }

         # Run the experiment
         python /Funsearch/implementation/funsearch.py \
            --spec-path=/Funsearch/implementation/specifications/baseline.txt \
            --save_checkpoints_path=/experiment/Checkpoints \
            --config-name=/experiment/$CONFIG_NAME \
            --no-dynamic-scaling \
            --log-dir=/experiment/logs || { echo 'Error running funsearch.py'; exit 1; }
     " &

# Create a list of 10 times evenly spaced from 1800 to 3600 seconds
scaling_intervals_s=($(seq 1800 200 3600))
# Create a list of times from 200 to 300 with a step of 30 seconds
scaling_intervals_e=($(seq 200 30 300))
sleep 60

# Run tasks on remaining nodes (evaluator and sampler scripts)
for i in "${!REMAINING_GPU[@]}"; do
    node="${REMAINING_GPU[$i]}"
    scaling_time_s=${scaling_intervals_s[$i]}  # Get scaling interval for sampler
    scaling_time_e=${scaling_intervals_e[$i]}  # Get scaling interval for evaluator
    srun -N1 -n1 --nodelist=$node \
        --container-mounts=$EXPERIMENT_DIR:/experiment/,\
/dss/dsshome1/02/di38yur/Funsearch/implementation:/Funsearch/implementation/,\
/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/models/:/workspace/models/,\
$SANDBOX_DIR:/workspace/sandboxstorage/ \
        --container-image=/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/enroot/fw.sqsh \
        bash -c "
            echo 'Running on $(hostname -f)'
            cd /experiment || { echo 'Error changing to /experiment'; exit 1; }

            # Install dependencies
            pip install nvidia-ml-py3 dash plotly numpy scikit-learn zss || { echo 'Error installing dependencies'; exit 1; }

            python /Funsearch/implementation/attach_eval.py \
                --spec-path=/Funsearch/implementation/specifications/baseline.txt \
                --no-dynamic-scaling \
                --config-name=/experiment/$CONFIG_NAME \
                --log-dir=/experiment/logs || { echo 'Error running attach_eval.py'; exit 1; } &
            python /Funsearch/implementation/attach_sampler.py \
                --spec-path=/Funsearch/implementation/specifications/baseline.txt \
                --config-name=/experiment/$CONFIG_NAME \
                --no-dynamic-scaling \
                --log-dir=/experiment/logs || { echo 'Error running attach_sampler.py'; exit 1; } &
            wait
        " &
done

sleep 20

# Run evaluator tasks on CPU nodes
for i in "${!CPU_NODE_LIST[@]}"; do
    node="${CPU_NODE_LIST[$i]}"
    echo "Running evaluator task on CPU node $node"
    scaling_time_e=${scaling_intervals_e[$i]}
    srun --het-group=1 -N1 -n1 --nodelist=$node \
        --container-mounts=$EXPERIMENT_DIR:/experiment/,\
/dss/dsshome1/02/di38yur/Funsearch/implementation:/Funsearch/implementation/,\
/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/models/:/workspace/models/,\
$SANDBOX_DIR:/workspace/sandboxstorage/ \
        --container-image=/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/franziska/enroot/fw.sqsh \
        bash -c "
            echo 'Running on $(hostname -f)'
            echo 'Running cpu only tasks'
            cd /experiment || { echo 'Error changing to /experiment'; exit 1; }

            # Install dependencies
            pip install nvidia-ml-py3 dash plotly numpy scikit-learn zss || { echo 'Error installing dependencies'; exit 1; }

            # Update the RabbitMQ configuration with the hostname
            python /Funsearch/implementation/update_config_file.py /experiment/$CONFIG_ATTACH_NAME \"$RABBITMQ_HOSTNAME\" || { echo 'Error running update_config_file.py'; exit 1; }

            python /Funsearch/implementation/attach_eval.py \
                --spec-path=/Funsearch/implementation/specifications/baseline.txt \
                --config-name=/experiment/$CONFIG_ATTACH_NAME \
                --no-dynamic-scaling \
                --log-dir=/experiment/logs || { echo 'Error running attach_eval.py'; exit 1; } &
            wait
        " &
done

wait  # Wait for all tasks to complete
