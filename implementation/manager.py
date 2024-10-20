from multiprocessing.managers import SyncManager
import multiprocessing
import programs_database

# Define the custom manager class
class CustomManager(SyncManager):
    pass

# Register the 'Island' class from the programs_database to be used through the manager
CustomManager.register('Island', programs_database.Island, programs_database.IslandProxy)
CustomManager.register('Cluster', programs_database.Cluster, programs_database.ClusterProxy)


def start_manager():
    """Starts the manager and waits for it to be ready before returning the manager object."""
    # Create the manager instance
    manager = CustomManager(address=('127.0.0.1', 50000), authkey=b'secret')
    manager.start()  # Start the manager server
    
    print("Manager started, ready to accept connections.")
    return manager

# Optionally, if you want to run the server in a way that it waits indefinitely:
def run_forever(manager):
    server = manager.get_server()
    print("Manager running, waiting for clients to connect...")
    server.serve_forever()

if __name__ == "__main__":
    manager = start_manager()
    run_forever(manager)  # Only call this if you want the script to block here
