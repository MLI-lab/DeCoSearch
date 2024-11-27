import os  
import psutil 
import pynvml  
import logging 
import asyncio  
import threading  
import torch.multiprocessing as mp  
from typing import Sequence, Any




class ResourceManager:
    def __init__(self, resource_logger=None):
        self.resource_logger = resource_logger or self._initialize_resource_logger()
        self._initialize_nvml()
        self.process_to_device_map = {}

    def _initialize_resource_logger(self):
        logger = logging.getLogger("resource_logger")
        logger.setLevel(logging.DEBUG)
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file_path = os.path.join(logs_dir, "resources.log")
        handler = logging.FileHandler(log_file_path, mode="w")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

    def _initialize_nvml(self):
        try:
            pynvml.nvmlInit()
            self.resource_logger.debug("Successfully initialized NVML for GPU monitoring.")
        except pynvml.NVMLError as e:
            self.resource_logger.error(f"Failed to initialize NVML: {e}")
            raise

    async def log_resource_stats_periodically(self, interval=300):
        """Log available CPU, GPU, RAM, and system load/utilization every `interval` seconds."""
        while True:
            try:
                # Log CPU usage
                cpu_affinity = os.sched_getaffinity(0)  # Get CPUs available to the current process/container
                cpu_usage = psutil.cpu_percent(interval=None, percpu=True)  # Get usage for all system CPUs
                available_cpu_usage = [cpu_usage[i] for i in cpu_affinity]  # Filter for CPUs available to the process
                avg_cpu_usage = sum(available_cpu_usage) / len(available_cpu_usage)  # Calculate the average CPU usage
                self.resource_logger.info(f"Available CPUs: {len(cpu_affinity)}, Average CPU Usage: {avg_cpu_usage:.2f}%")

                # Log GPU usage
                device_count = pynvml.nvmlDeviceGetCount()  # Get the number of available GPUs
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)

                    free_memory_mib = memory_info.free / 1024**2  # Convert bytes to MiB
                    total_memory_mib = memory_info.total / 1024**2
                    gpu_utilization = utilization.gpu  # GPU utilization percentage
                    self.resource_logger.info(f"GPU {i}: Free Memory = {free_memory_mib:.2f} MiB / {total_memory_mib:.2f} MiB, GPU Utilization = {gpu_utilization}%")

                # Log RAM usage
                process = psutil.Process(os.getpid())  # Get current process
                memory_info = process.memory_info()
                rss_mib = memory_info.rss / 1024**2  # Resident Set Size in MiB
                vms_mib = memory_info.vms / 1024**2  # Virtual Memory Size in MiB
                self.resource_logger.info(f"Memory Usage: RSS = {rss_mib:.2f} MiB, VMS = {vms_mib:.2f} MiB")

                # Log system load
                load_avg_1, load_avg_5, load_avg_15 = os.getloadavg()
                num_cores = len(cpu_affinity)  # Number of CPU cores available to the process
                self.resource_logger.info(f"System Load (1m, 5m, 15m): {load_avg_1:.2f}, {load_avg_5:.2f}, {load_avg_15:.2f} and Load/Cores Ratio (1m): {load_avg_1:.2f}/{num_cores} ({load_avg_1 / num_cores:.2f})")

            except psutil.Error as e:
                self.resource_logger.error(f"Failed to query CPU or RAM information: {e}")
            except pynvml.NVMLError as e:
                self.resource_logger.error(f"Failed to query GPU information: {e}")
            finally:
                await asyncio.sleep(interval)  # Wait for the specified interval before checking again


    async def get_queue_message_count(self, channel, queue_name):
        try:
            queue = await channel.declare_queue(queue_name, passive=True)
            message_count = queue.declaration_result.message_count
            return message_count
        except Exception as e:
            self.resource_logger(f"Error getting message count for queue {queue_name}: {e}")
            return 0

    async def adjust_processes(self, message_count, threshold, processes, target_fnc, args, max_processes, min_processes, process_name):
        num_processes = len(processes)
        self.resource_logger.debug(f"Adjusting {process_name}: message_count={message_count}, threshold={threshold}, num_processes={num_processes}, min_processes={min_processes}")

        if message_count > threshold and num_processes < max_processes:
            # Scale up
            self.start_process(target_fnc, args, processes, process_name)
            current_processes = len(processes)
            if current_processes > num_processes:
                self.resource_logger.info(f"Scaled up {process_name} processes to {current_processes}")
            else:
                self.resource_logger.info(f"Could not scale up {process_name} processes; still at {current_processes}")

        elif message_count < threshold and num_processes > min_processes:
            # Scale down
            self.terminate_process(processes, process_name)
            current_processes = len(processes)
            if current_processes < num_processes:
                self.resource_logger.info(f"Scaled down {process_name} processes to {current_processes}")
            else: 
                self.resource_logger.info(f"Could not scale down {process_name} processes; still at {current_processes}")
        else: 
            self.resource_logger.info(f"No scaling action needed for {process_name}. Current processes: {num_processes}, Message count: {message_count}")
            return 


    def start_process(self, target_fnc, args, processes, process_name):
        current_pid = os.getpid()
        current_thread = threading.current_thread().name
        thread_id = threading.get_ident()

        # CPU check for evaluator processes
        if process_name == 'Evaluator':
            cpu_affinity = os.sched_getaffinity(0)  # Get CPUs available to the container
            cpu_usage = psutil.cpu_percent(percpu=True)  # Get usage for all system CPUs
            container_cpu_usage = [cpu_usage[i] for i in cpu_affinity]

            # Count how many of the available CPUs are under 50% usage
            available_cpus_with_low_usage = sum(1 for usage in container_cpu_usage if usage < 50)
            self.resource_logger.info(f"Available CPUs with <50% usage (in container): {available_cpus_with_low_usage}")

            # Scale up only if more than 4 CPUs have less than 50% usage
            if available_cpus_with_low_usage <= 4:
                self.resource_logger.info(f"Cannot scale up {process_name}: Not enough available CPU resources.")
                return  # Exit the function if not enough CPU resources

        # GPU check for sampler processes
        if process_name == 'Sampler':
            visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
            visible_devices = [int(dev.strip()) for dev in visible_devices if dev.strip()]  # Ensure non-empty strings and convert to int

            # Initialize GPU memory info and utilization
            gpu_memory_info = {}

            try:
                pynvml.nvmlInit()
            except pynvml.NVMLError as e:
                self.resource_logger.error(f"Failed to initialize NVML: {e}")
                device = 'cuda'
                self.resource_logger.warning(f"Proceeding with device=cuda for {process_name}.")
                args += (device,)
                try:
                    # Start the process
                    proc = mp.Process(target=target_fnc, args=args, name=f"{process_name}-{len(processes)}")
                    proc.start()
                    processes.append(proc)
                    return
                except Exception as e: 
                    return 

            for dev_id in visible_devices:
                try:
                    handle = None
                    if isinstance(dev_id, int): # Check if dev_id is an integer (regular GPU)
                        dev_int = int(dev_id)
                        handle = pynvml.nvmlDeviceGetHandleByIndex(dev_int)
                        # Create mapping for regular GPU device indices
                        id_to_container_index = {dev: idx for idx, dev in enumerate(visible_devices) if isinstance(dev, int)}
                    else:
                        handle = pynvml.nvmlDeviceGetHandleByUUID(dev_id)

                except (ValueError, pynvml.NVMLError) as e:
                    self.resource_logger.error(f"Error getting handle for device ID {dev_id}: {e}")
                    continue

                if handle:
                    try:
                        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        free_memory_mib = memory_info.free / 1024**2  # Convert bytes to MiB
                        gpu_utilization = utilization.gpu  # Percentage
                        gpu_memory_info[dev_id] = (free_memory_mib, gpu_utilization)
                    except pynvml.NVMLError as e:
                        self.resource_logger.error(f"Error querying memory for device {dev_id}: {e}")
                        gpu_memory_info[dev_id] = (None, None)  # Set to None on error

            suitable_gpu_id = None
            combined_memory = 0
            combined_gpus = []

            # Check if any single GPU has >= 32 GiB of memory free and < 50% utilization
            for dev_id, (free_memory, utilization) in gpu_memory_info.items():
                if free_memory is None and utilization is None:
                    self.resource_logger.warning(f"Memory information could not be queried for device {dev_id}. Skipping this device.")
                    continue  # Skip this device and continue checking others
                if free_memory > 32768 and utilization < 200: #need more than 32 GiB for starcoder too fit
                    suitable_gpu_id = dev_id
                    self.resource_logger.warning(f"Device {dev_id} has free memory {free_memory} and utilization {utilization}. Attemption to load model on device. ")
                    break
                elif utilization < 200:
                    combined_memory += free_memory if free_memory else 0
                    combined_gpus.append(dev_id)

            # Assign device based on availability
            if suitable_gpu_id is not None and isinstance(suitable_gpu_id, int): 
                container_index = id_to_container_index[suitable_gpu_id]
                device = f"cuda:{container_index}"
            elif combined_memory >= 32768:
                device = 'cuda'  # Use multiple GPUs
                self.resource_logger.info(f"Using combination of GPUs: {combined_gpus} with total memory: {combined_memory} MiB")
            elif free_memory is None and utilization is None: # When no memory and utilization could be queried 
                device='cuda'
                self.resource_logger.warning(f"Memory information could not be queried for device {dev_id}.")
            else:
                self.resource_logger.warning(f"Not enough GPU memory available: {free_memory} for {process_name}, no scaling.")
                return

            self.resource_logger.info(f"Assigning {process_name} to device {device if device else 'combined GPUs (cuda)'}")
            args += (device,)  # Append the device to args

        # Start the process
        try: 
            proc = mp.Process(target=target_fnc, args=args, name=f"{process_name}-{len(processes)}")
            proc.start()
            processes.append(proc)
            # Store the process PID and device in the map only for sampler processes
            if process_name == 'Sampler':
                self.process_to_device_map[proc.pid] = device
        except Exception as e: 
            self.resource_logger.error(f"Could not start process because {e}.")
            return 

    def terminate_process(self, processes, process_name, immediate=False):
        if processes:
            if immediate:
                process_to_terminate = processes.pop(0)
                self.resource_logger.info(f"Immediately terminating {process_name} process with PID: {process_to_terminate.pid}")
            else:
                # Try to get the least busy process
                if process_name.startswith('Evaluator'):
                    least_busy_process = self.get_process_with_zero_or_lowest_cpu(processes)
                elif process_name.startswith('Sampler'): 
                    least_busy_process = self.get_process_with_zero_or_lowest_gpu(processes)
                else: 
                    self.resource_logger.info(f"No Sampler or Evaluator process is {process_name}")
                    return 
                self.resource_logger.info(f"least_busy_process is {least_busy_process}")
                if least_busy_process is None:
                    return
                else:
                    # Remove the chosen process from the list
                    processes.remove(least_busy_process)

                if least_busy_process.is_alive():
                    self.resource_logger.info(f"Initiating termination for {process_name} process with PID: {least_busy_process.pid}")
                    least_busy_process.terminate()
                    least_busy_process.join(timeout=10)  # Wait for it to fully terminate
                    if least_busy_process.is_alive():
                        self.resource_logger.warning(f"{process_name} process with PID: {least_busy_process.pid} is still alive after timeout, forcing kill.")
                        least_busy_process.kill()
                    self.resource_logger.info(f"{process_name} process with PID: {least_busy_process.pid} terminated successfully.")
        else:
            self.resource_logger.warning(f"No {process_name} processes to terminate.")

    def get_process_with_zero_or_lowest_cpu(self, processes, cpu_utilization_threshold=20):
        """Find a process to terminate based on CPU utilization."""
        for proc in processes:
            try:
                p = psutil.Process(proc.pid)
                cpu_usage = p.cpu_percent(interval=1)
                self.resource_logger.debug(f"Process PID {proc.pid} CPU utilization: {cpu_usage}%")

                # If CPU utilization is below the threshold, select this process for termination
                if cpu_usage < cpu_utilization_threshold:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.resource_logger.warning(f"Failed to access CPU usage for process PID {proc.pid}. It might have finished or access was denied.")
                continue

        # If no process meets the threshold, return None
        self.resource_logger.info(f"No process with CPU utilization below {cpu_utilization_threshold}% found.")
        return None


    def get_process_with_zero_or_lowest_gpu(self, processes, gpu_utilization_threshold=10):
        """Find a process to terminate based on GPU utilization."""
        try:
            for proc in processes:
                try:
                    # Try to extract the GPU device from the process arguments 
                    device = self.process_to_device_map.get(proc.pid)
                    if device and device != 'cuda':
                        # Extract the GPU index from the device string, e.g., "cuda:0" -> 0
                        gpu_index = int(device.split(":")[1])
                    
                        # Get GPU utilization percentage using pynvml
                        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
                        gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu  

                        # If GPU utilization is below the threshold, select this process for termination
                        if gpu_utilization < gpu_utilization_threshold:
                            self.resource_logger.info(f"Process with PID {proc.pid} is using GPU {gpu_index} with utilization {gpu_utilization}%, below threshold {gpu_utilization_threshold}%.")
                            return proc
                    else:
                        self.resource_logger.info(f"Process PID {proc.pid} does not have a GPU device argument.")
                except pynvml.NVMLError as e:
                    self.resource_logger.warning(f"Failed to get GPU utilization for process PID {proc.pid}: {e}")
                    continue
                except Exception as e:
                    self.resource_logger.warning(f"Error checking GPU utilization for process PID {proc.pid}: {e}")
                    continue

            # If no GPU-based process has utilization below the threshold, return None
            self.resource_logger.info("No GPU-based process found with GPU utilization below threshold.")
            return None

        except Exception as e:
            self.resource_logger.error(f"Error occurred while checking GPU utilization: {e}, falling back to cpu based check.")
            return self.get_process_with_zero_or_lowest_cpu(processes)