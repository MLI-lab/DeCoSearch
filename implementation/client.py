from multiprocessing.managers import SyncManager
import time
import programs_database

def connect_to_manager(retries=5, delay=2):
    """Connects to the manager server with retries if it's not reachable initially."""
    class CustomManager(SyncManager):
        pass

    # Register the Island class from the programs_database to be used through the manager
    CustomManager.register('Island', programs_database.Island, programs_database.IslandProxy)
    CustomManager.register('Cluster', programs_database.Cluster, programs_database.ClusterProxy)

    
    manager = CustomManager(address=('127.0.0.1', 50000), authkey=b'secret')
    
    for attempt in range(retries):
        try:
            manager.connect()
            print("Connected to manager.")
            return manager
        except ConnectionRefusedError:
            if attempt < retries - 1:
                print(f"Connection refused, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise ConnectionError("Failed to connect to the manager server after several attempts.")
    
    return None
