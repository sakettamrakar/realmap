# Local Model Setup & Hardware Guide

## A. Local vs. Cloud Recommendation

### Cloud (Production)
For high-volume, highly reliable inference, use hosted APIs.
*   **Recommended:** Gemini 1.5 Pro, Claude 3.5 Sonnet, or OpenAI GPT-4o.
*   **Why:** Zero maintenance, high limits, best reasoning capabilities.

### Local (Development & Prototyping)
For running the stack entirely on your own hardware (e.g., GTX 1660 Super with 6GB VRAM).
*   **Recommended:** **Qwen2.5-7B-Instruct-GGUF** (Quantization: `Q4_K_M` or `Q5_K_S`).
*   **Why:** Fits comfortably in 6GB VRAM (approx 4.5GB loaded), fast token generation, excellent reasoning for its size.
*   **Alternative:** Mistral 7B Instruct v0.3 (GGUF `Q4_K_M`).

## B. Storage Locations
Organize models systematically to avoid clutter.

*   **Standard Path:** `/models/{feature_category}/{model_name}/{version}/`
*   **Permissions:** ensure the user running the service (e.g., `app_user`) has read access.
    ```bash
    chown -R app_user:app_group /models
    chmod -R 640 /models
    ```

## C. Step-by-Step Download
*(Developer: Replace placeholders with actual paths)*

1.  **Create Directory:**
    ```bash
    mkdir -p C:/models/ai/general/v1
    ```

2.  **Download Model:**
    Download `qwen2.5-7b-instruct-q4_k_m.gguf` from HuggingFace (TheBloke or equivalent).
    *   Source: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

3.  **Place File:**
    Move the downloaded `.gguf` file to `C:/models/ai/general/v1/`.

4.  **Verify:**
    ```powershell
    ls C:/models/ai/general/v1
    ```

## D. Runtime Requirements
*   **Python:** 3.10 or higher.
*   **Dependencies:**
    ```bash
    pip install torch --index-url https://download.pytorch.org/whl/cu118
    pip install llama-cpp-python  # Key for GGUF support
    ```
*   **Env Variable:**
    Set `MODEL_RUNTIME_PATH` to point to the `llama.dll` if manual linking is needed, though usually `pip install` handles it.

## E. GPU Tuning for 6GB VRAM
*   **Quantization:** STRICTLY use `Q4_K_M` (4-bit). `FP16` (16-bit) will OOM (Out Of Memory).
*   **Layers to GPU (`n_gpu_layers`):**
    *   Start with `-1` (all layers).
    *   If OOM, try `30`.
    *   If still OOM, drop to `20` and offload rest to CPU (slower but works).
*   **Context Window (`n_ctx`):** Keep it around `4096` or `8192`. Do not try `32k` on 6GB card.

## F. Example Environment Variables
Add these to your `.env`:

```ini
MODEL_ROOT=C:/models
# Primary LLM
Start_MODEL_PATH=C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m.gguf
MODEL_RUNTIME=gguf
# VRAM Config
GPU_LAYERS=33
CONTEXT_SIZE=4096
```

## G. Validation Script
Run this python snippet to verify setup:

```python
from llama_cpp import Llama

model_path = "C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m.gguf"

try:
    llm = Llama(
        model_path=model_path, 
        n_gpu_layers=33, # Adjust based on VRAM
        n_ctx=4096
    )
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": "Return JSON: {'status': 'ok'}"}],
        response_format={"type": "json_object"}
    )
    print("SUCCESS:", response['choices'][0]['message']['content'])
except Exception as e:
    print("FAILURE:", e)
```
