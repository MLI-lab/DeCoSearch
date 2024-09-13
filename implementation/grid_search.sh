#!/bin/bash

# Function to kill all Python processes
kill_python_processes() {
    echo "$(date) - Killing all Python processes..."
    pkill -f python
    echo "$(date) - All Python processes killed."
}

# Function to check and delete RabbitMQ resources
check_and_delete_rabbitmq_resources() {
    echo "$(date) - Checking for leftover RabbitMQ resources..."

    # Delete all queues
    curl -s -u guest:guest http://rabbitmqFW:15672/api/queues | jq -c '.[] | .name' | while read queue; do
        queue=$(echo $queue | sed 's/"//g')  # Remove quotes from queue name
        echo "Deleting queue: $queue"
        curl -X DELETE -u guest:guest "http://rabbitmqFW:15672/api/queues/%2F/$queue"
    done

    # Close all connections
    curl -s -u guest:guest http://rabbitmqFW:15672/api/connections | jq -c '.[] | .name' | while read connection; do
        connection=$(echo $connection | sed 's/"//g')  # Remove quotes from connection name
        echo "Closing connection: $connection"
        curl -X DELETE -u guest:guest "http://rabbitmqFW:15672/api/connections/$connection"
    done

    # Close all channels
    curl -s -u guest:guest http://rabbitmqFW:15672/api/channels | jq -c '.[] | .name' | while read channel; do
        channel=$(echo $channel | sed 's/"//g')  # Remove quotes from channel name
        echo "Closing channel: $channel"
        curl -X DELETE -u guest:guest "http://rabbitmqFW:15672/api/channels/$channel"
    done

    echo "$(date) - RabbitMQ resources cleaned up."
}

# Function to restart grid search
restart_grid_search() {
    echo "$(date) - Restarting grid search..."
    CUDA_VISIBLE_DEVICES=2 python /franziska/implementation/grid_search.py
    echo "$(date) - Grid search script terminated. Restarting..."
}

# Main script execution loop
while true; do
    kill_python_processes
    sleep 2
    check_and_delete_rabbitmq_resources
    sleep 5
    restart_grid_search
done