
import os
import json
import sys
from dotenv import load_dotenv

# Load env to get MODEL_PATH
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH")
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "33"))
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "4096"))

if not MODEL_PATH:
    print("Error: MODEL_PATH not set in .env")
    sys.exit(1)

print(f"Loading Model from: {MODEL_PATH}")
print(f"GPU Layers: {GPU_LAYERS}, Context: {CONTEXT_SIZE}")

try:
    from llama_cpp import Llama, LlamaGrammar
except ImportError:
    print("Error: llama-cpp-python not installed. Run 'pip install llama-cpp-python'")
    sys.exit(1)

# Sample Project Data (Mocking what we'd pull from DB)
project_data = {
    "name": "Sunshine Heights",
    "location": "Sector 45, Gurgaon",
    "developer_reputation": "High - Delivered 50+ projects",
    "amenities": ["Swimming Pool", "Gym", "Clubhouse", "24/7 Security", "Power Backup", "Jogging Track"],
    "legal_status": "Clear",
    "price_per_sqft": 12000
}

# Construct the Prompt
SYSTEM_PROMPT = """You are an expert Real Estate Analyst AI. 
Your task is to evaluate a real estate project based on the provided details and assign a 'Quality Score' (0-100).
You must also provide a brief 1-sentence explanation for the score.

Return your response strictly in JSON format as follows:
{
    "score": <int>,
    "reason": "<string>",
    "analysis": {
        "pros": ["<string>", ...],
        "cons": ["<string>", ...]
    }
}
"""

USER_MSG = f"""Evaluate this project:
{json.dumps(project_data, indent=2)}
"""

print("\n--- PROMPT SYSTEM ---")
print(SYSTEM_PROMPT)
print("--- PROMPT USER ---")
print(USER_MSG)
print("---------------------\n")

# Load Model
try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=CONTEXT_SIZE,
        verbose=True
    )
except Exception as e:
    print(f"Failed to load model: {e}")
    sys.exit(1)

# Run Inference
print("Generating Response (Streaming)...")
stream = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_MSG}
    ],
    response_format={"type": "json_object"},
    stream=True,
    temperature=0.2, # Low temp for deterministic logic
    max_tokens=512
)

full_response = ""
for chunk in stream:
    delta = chunk['choices'][0]['delta']
    if 'content' in delta:
        content = delta['content']
        print(content, end="", flush=True)
        full_response += content

print("\n\n--- COMPLETED ---")
