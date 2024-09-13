from transformers import AutoModelForCausalLM, AutoTokenizer

checkpoint = "bigcode/starcoder2-15b"

cache_dir = "/franziska/implementation/ChachingFace"

# Load the tokenizer and model from the custom cache directory
tokenizer = AutoTokenizer.from_pretrained(checkpoint, cache_dir=cache_dir)
model = AutoModelForCausalLM.from_pretrained(checkpoint, cache_dir=cache_dir)
