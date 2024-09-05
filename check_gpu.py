import torch

# Print the PyTorch version
print(f"PyTorch version: {torch.__version__}")

# Check if CUDA is available
print(f"CUDA available: {torch.cuda.is_available()}")

# Check the number of GPUs available
print(f"Number of GPUs available: {torch.cuda.device_count()}")

# Print the name of the first GPU
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
