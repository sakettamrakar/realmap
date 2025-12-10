
import os
import time
import json
from dotenv import load_dotenv

# Load Environment
load_dotenv()

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH")
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "0"))
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "2048"))

_LLM_INSTANCE = None

def get_llm_instance():
    """Singleton loader for the LLM to avoid reloading large files."""
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        if not MODEL_PATH or not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
        
        try:
            from llama_cpp import Llama
            print(f"DTO-LOG: Loading Local LLM from {MODEL_PATH}...")
            _LLM_INSTANCE = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=GPU_LAYERS,
                n_ctx=CONTEXT_SIZE,
                verbose=False
            )
            print("DTO-LOG: Model Loaded Successfully.")
        except ImportError:
            print("DTO-ERROR: llama-cpp-python not installed.")
            raise
    return _LLM_INSTANCE

def run_llm(prompt: str, max_tokens: int = 256, temperature: float = 0.7, stop: list = None) -> dict:
    """
    Executes a prompt against the local LLM.
    
    Args:
        prompt (str): Input text.
        max_tokens (int): response limit.
        temperature (float): creativity 0.0-1.0.
        stop (list): stop sequences.
        
    Returns:
        dict: {
            "text": str,
            "tokens_used": int,
            "finish_reason": str,
            "metrics": dict
        }
    """
    start_time = time.time()
    llm = get_llm_instance()
    
    try:
        # We use the lower-level completion API for raw control
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or ["Observation:", "User:"],
            echo=False
        )
        
        latency = time.time() - start_time
        choice = output['choices'][0]
        usage = output.get('usage', {})
        
        return {
            "text": choice['text'],
            "tokens_used": usage.get('total_tokens', 0),
            "finish_reason": choice['finish_reason'],
            "metrics": {
                "latency_sec": round(latency, 3),
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0)
            }
        }
        
    except Exception as e:
        print(f"DTO-ERROR: LLM Inference Failed: {e}")
        return {
            "text": "",
            "tokens_used": 0,
            "finish_reason": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Internal Test
    try:
        print("Testing Local LLM Adapter...")
        result = run_llm("Q: What is the capital of France? A: ", max_tokens=10, temperature=0.1)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test Failed: {e}")
