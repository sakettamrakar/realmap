"""Quick LLM test script."""
import os
import sys

sys.path.insert(0, r'c:\GIT\realmap')
os.environ['MODEL_PATH'] = r'C:/models/ai/general/v1/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf'

from ai.llm.adapter import run

print("Testing LLM...")
result = run("What is 2+2? Answer with just the number.", max_tokens=10, temperature=0.1)
print(f"Response: {result['text']}")
print(f"Latency: {result['latency_ms']}ms")
print(f"Tokens: {result['tokens_used']}")
