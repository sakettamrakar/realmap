
from typing import Dict, Any
from .logger import get_logger

logger = get_logger("ai_metrics")

class MetricsTracker:
    def __init__(self):
        self._metrics = []

    def log_latency(self, operation: str, duration_sec: float, tags: Dict[str, str] = None):
        metric = {
            "name": "latency",
            "operation": operation,
            "value": duration_sec,
            "unit": "s",
            "tags": tags or {}
        }
        self._emit(metric)

    def log_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        metric = {
            "name": name,
            "type": "counter",
            "value": value,
            "tags": tags or {}
        }
        self._emit(metric)

    def log_token_usage(self, agent: str, prompt_tokens: int, completion_tokens: int):
        self.log_counter("llm_tokens", prompt_tokens + completion_tokens, 
                         {"agent": agent, "kind": "total"})
        self.log_counter("llm_tokens", prompt_tokens, 
                         {"agent": agent, "kind": "prompt"})
        self.log_counter("llm_tokens", completion_tokens, 
                         {"agent": agent, "kind": "completion"})

    def _emit(self, metric: Dict[str, Any]):
        # In a real system, this would push to Prometheus/Datadog
        # For now, we log structured JSON
        logger.info("Metric Emitted", extra={"props": {"metric": metric}})

tracker = MetricsTracker()
