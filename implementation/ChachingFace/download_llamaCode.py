from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login

huggingface_token = "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" # for Llama Code
login(token=huggingface_token)

checkpoint = "meta-llama/CodeLlama-13b-Python-hf"

cache_dir = "/franziska/implementation/ChachingFace"

# Load the tokenizer and model from the custom cache directory
tokenizer = AutoTokenizer.from_pretrained(checkpoint, cache_dir=cache_dir)
model = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir=cache_dir)
