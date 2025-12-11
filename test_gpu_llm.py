#!/usr/bin/env python3
"""
Test if LLM is using GPU acceleration.
"""
import os
import sys
import time

# Force GPU settings
os.environ["MODEL_PATH"] = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
os.environ["GPU_LAYERS"] = "35"  # Offload 35 layers to GPU
os.environ["CONTEXT_SIZE"] = "8192"
os.environ["LLM_TIMEOUT_SEC"] = "180"

print("=" * 70)
print("GPU LLM TEST")
print("=" * 70)
print(f"\nEnvironment Settings:")
print(f"  MODEL_PATH: {os.environ['MODEL_PATH']}")
print(f"  GPU_LAYERS: {os.environ['GPU_LAYERS']}")
print(f"  CONTEXT_SIZE: {os.environ['CONTEXT_SIZE']}")

print("\n1. Checking llama-cpp-python CUDA support...")
try:
    from llama_cpp import Llama
    print("   llama_cpp imported successfully")
    
    # Check for CUDA-related attributes
    import llama_cpp
    if hasattr(llama_cpp, 'llama_backend_init'):
        print("   Backend init function available")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

print("\n2. Loading model with GPU layers...")
start = time.time()
try:
    llm = Llama(
        model_path=os.environ["MODEL_PATH"],
        n_gpu_layers=int(os.environ["GPU_LAYERS"]),
        n_ctx=int(os.environ["CONTEXT_SIZE"]),
        verbose=True  # Enable verbose to see GPU loading info
    )
    load_time = time.time() - start
    print(f"\n   Model loaded in {load_time:.1f}s")
except Exception as e:
    print(f"   ERROR loading model: {e}")
    sys.exit(1)

print("\n3. Testing inference speed...")
test_prompt = "What is 2+2? Answer with just the number:"

# Warm-up run
print("   Warm-up run...")
_ = llm(test_prompt, max_tokens=10, temperature=0.1)

# Timed run
print("   Timed run...")
start = time.time()
result = llm(test_prompt, max_tokens=10, temperature=0.1)
inference_time = time.time() - start

response = result['choices'][0]['text'].strip()
tokens = result.get('usage', {}).get('total_tokens', 0)

print(f"\n   Response: {response}")
print(f"   Inference time: {inference_time*1000:.0f}ms")
print(f"   Tokens: {tokens}")
print(f"   Tokens/sec: {tokens/inference_time:.1f}" if inference_time > 0 else "   N/A")

# Longer test
print("\n4. Testing longer generation...")
long_prompt = "Write a haiku about programming:"
start = time.time()
result = llm(long_prompt, max_tokens=50, temperature=0.7)
inference_time = time.time() - start

response = result['choices'][0]['text'].strip()
tokens = result.get('usage', {}).get('total_tokens', 0)

print(f"\n   Response: {response}")
print(f"   Inference time: {inference_time*1000:.0f}ms")
print(f"   Tokens: {tokens}")
print(f"   Tokens/sec: {tokens/inference_time:.1f}" if inference_time > 0 else "   N/A")

print("\n" + "=" * 70)
print("GPU TEST COMPLETE")
print("=" * 70)
print("\nIf inference time is under 5 seconds, GPU is working!")
print("If inference time is 30+ seconds, still running on CPU.")
