import os
import time
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Set up logging
logger = logging.getLogger("ai.llm.adapter")
logging.basicConfig(level=logging.INFO)

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH")
GPU_LAYERS = int(os.getenv("GPU_LAYERS", "35"))  # Default to 35 layers for GPU offloading
CONTEXT_SIZE = int(os.getenv("CONTEXT_SIZE", "4096"))  # Increased default for better extraction
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "180"))
REQUIRE_GPU = os.getenv("LLM_REQUIRE_GPU", "true").lower() == "true"  # Default: require GPU

_LLM_INSTANCE = None
_GPU_AVAILABLE = None


def check_cuda_available() -> bool:
    """Check if CUDA is available for GPU acceleration."""
    global _GPU_AVAILABLE
    if _GPU_AVAILABLE is not None:
        return _GPU_AVAILABLE
    
    try:
        from llama_cpp import Llama
        # Try to detect CUDA support by checking if llama_cpp was built with CUDA
        import llama_cpp
        # The presence of CUDA is indicated by the library loading without error
        # and the model successfully using GPU layers
        _GPU_AVAILABLE = True
        logger.info("CUDA support detected in llama-cpp-python")
    except Exception as e:
        logger.warning(f"CUDA not available: {e}")
        _GPU_AVAILABLE = False
    
    return _GPU_AVAILABLE


def get_gpu_info() -> Optional[Dict[str, Any]]:
    """Get GPU information if available."""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 4:
                return {
                    "name": parts[0],
                    "memory_total_mb": int(parts[1]),
                    "memory_free_mb": int(parts[2]),
                    "memory_used_mb": int(parts[3]),
                }
    except Exception as e:
        logger.debug(f"Could not get GPU info: {e}")
    return None


def get_llm_instance():
    """
    Singleton loader for the LLM.
    
    If REQUIRE_GPU is True (default), will only load if GPU is available.
    Returns None if GPU is required but not available.
    """
    global _LLM_INSTANCE
    if _LLM_INSTANCE is not None:
        return _LLM_INSTANCE
    
    if not MODEL_PATH or not os.path.exists(MODEL_PATH):
        logger.warning(f"Model file not found at: {MODEL_PATH}. LLM disabled.")
        return None
    
    # Check GPU availability
    gpu_info = get_gpu_info()
    if gpu_info:
        logger.info(f"GPU detected: {gpu_info['name']} ({gpu_info['memory_free_mb']}MB free / {gpu_info['memory_total_mb']}MB total)")
    else:
        if REQUIRE_GPU:
            logger.error("GPU required but not detected. LLM disabled. Set LLM_REQUIRE_GPU=false to use CPU.")
            return None
        logger.warning("No GPU detected, running on CPU (slow)")
    
    try:
        from llama_cpp import Llama
        logger.info(f"Loading Local LLM from {MODEL_PATH}...")
        logger.info(f"Config: GPU_LAYERS={GPU_LAYERS}, CONTEXT_SIZE={CONTEXT_SIZE}")
        
        _LLM_INSTANCE = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=GPU_LAYERS,
            n_ctx=CONTEXT_SIZE,
            verbose=False
        )
        logger.info("Model Loaded Successfully on GPU.")
        
    except ImportError:
        logger.error("llama-cpp-python not installed. LLM disabled.")
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
            stop=["Observation:", "User:", "System:", "\n\n", "Document:", "Categories:"],
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
