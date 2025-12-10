from llama_cpp import Llama
import os

# Updated to point to the first part of the split file
model_path = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"

print(f"Loading model from: {model_path}")

try:
    llm = Llama(
        model_path=model_path, 
        n_gpu_layers=33, # Adjust based on VRAM
        n_ctx=4096,
        verbose=True
    )
    print("Model loaded successfully.")
    
    print("Attempting inference...")
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": "Return JSON: {'status': 'ok'}"}],
        response_format={"type": "json_object"}
    )
    print("SUCCESS:", response['choices'][0]['message']['content'])
except Exception as e:
    print("FAILURE:", e)
