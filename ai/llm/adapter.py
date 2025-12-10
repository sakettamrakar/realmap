import os
import time
import logging
import json
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Set up logging
logger = logging.getLogger("ai.llm.adapter")
logging.basicConfig(level=logging.INFO)

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH")
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "0"))
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "2048"))
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "60"))

_LLM_INSTANCE = None

def get_llm_instance():
    """Singleton loader for the LLM."""
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        if not MODEL_PATH or not os.path.exists(MODEL_PATH):
            logger.warning(f"Model file not found at: {MODEL_PATH}. Running in mock mode.")
            return None
        
        try:
            from llama_cpp import Llama
            logger.info(f"Loading Local LLM from {MODEL_PATH}...")
            _LLM_INSTANCE = Llama(
                model_path=MODEL_PATH,
                n_gpu_layers=GPU_LAYERS,
                n_ctx=CONTEXT_SIZE,
                verbose=False
            )
            logger.info("Model Loaded Successfully.")
        except ImportError:
            logger.error("llama-cpp-python not installed. Running in mock mode.")
            return None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None
            
    return _LLM_INSTANCE

def _generate_raw(llm, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    """Internal generation function to be run in a thread."""
    try:
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["Observation:", "User:", "System:"], # standard stops
            echo=False
        )
        return output
    except Exception as e:
        logger.error(f"LLM Generation Error: {e}")
        raise

def run(prompt: str, *, system: str = "", max_tokens: int = 256, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Public adapter function.
    
    Returns:
        {
            "text": str,
            "tokens_used": int,
            "latency_ms": int,
            "error": Optional[str]
        }
    """
    start_time = time.time()
    
    # Construct full prompt (simple wrapper for now, can be improved with templates)
    if system:
        full_prompt = f"System: {system}\nUser: {prompt}\nAssistant:"
    else:
        full_prompt = prompt

    llm = get_llm_instance()
    
    # Mock mode if no model
    if llm is None:
        return {
            "text": "Simulated AI Response (Model not loaded)",
            "tokens_used": 0,
            "latency_ms": 0,
            "error": "ai_unavailable" if not MODEL_PATH else None
        }

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_generate_raw, llm, full_prompt, max_tokens, temperature)
    
    try:
        output = future.result(timeout=LLM_TIMEOUT_SEC)
        
        latency_ms = int((time.time() - start_time) * 1000)
        usage = output.get('usage', {})
        text_content = output['choices'][0]['text']
        
        logger.info(f"LLM Success: {usage.get('total_tokens')} tokens in {latency_ms}ms")
        
        return {
            "text": text_content,
            "tokens_used": usage.get('total_tokens', 0),
            "latency_ms": latency_ms,
            "error": None
        }
        
    except TimeoutError:
        logger.error(f"LLM Timeout after {LLM_TIMEOUT_SEC}s")
        return {
            "text": "",
            "tokens_used": 0,
            "latency_ms": int((time.time() - start_time) * 1000),
            "error": "timeout"
        }
    except Exception as e:
        logger.error(f"LLM Failed: {e}")
        return {
            "text": "",
            "tokens_used": 0,
            "latency_ms": int((time.time() - start_time) * 1000),
            "error": str(e)
        }
    finally:
        executor.shutdown(wait=False)
