"""
AIEngine: Bootstrap module for the VAI-OS AI subsystem.
Initializes model registry, loads models, and provides a simulated
inference interface returning deterministic responses for virtual OS use.
"""
import logging
import hashlib
import time

from .model_registry import ModelRegistry

logger = logging.getLogger(__name__)

# Built-in simulated responses keyed by prompt keyword patterns
_RESPONSE_BANK = {
    "hello": "Hello! I am VAI-OS AI assistant. How can I help?",
    "status": "All VAI-OS subsystems are operating within normal parameters.",
    "help": "I can assist with system queries, configuration, and troubleshooting.",
    "optimize": "Analyzing resource usage... CPU and RAM utilization look balanced.",
    "error": "I detected an anomaly. Recommend running a full system diagnostic.",
    "cloud": "Cloud cluster status nominal. All nodes healthy.",
    "security": "No active threats detected. Audit log clean.",
    "build": "Build system ready. Specify target and source files.",
    "default": "I have processed your request and recommend reviewing system logs.",
}


def _simulated_infer(prompt: str, context: dict) -> dict:
    """
    Produce a deterministic simulated inference result.

    Uses keyword matching against the prompt for response selection.
    """
    prompt_lower = prompt.lower()
    response = _RESPONSE_BANK["default"]
    for keyword, text in _RESPONSE_BANK.items():
        if keyword in prompt_lower:
            response = text
            break

    # Deterministic confidence derived from prompt hash
    h = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
    confidence = 0.70 + (h % 30) / 100.0  # 0.70 - 0.99
    tokens = len(prompt.split()) * 3 + 10

    return {
        "response": response,
        "confidence": round(confidence, 2),
        "tokens": tokens,
        "model": "default",
        "latency_ms": 2.5,
    }


class AIEngine:
    """VAI-OS AI Engine: model registry and inference dispatcher."""

    def __init__(self):
        self.initialized: bool = False
        self.models: ModelRegistry = ModelRegistry()
        self._total_inferences: int = 0
        self._metrics: dict = {
            "initialize_calls": 0,
            "load_model_calls": 0,
            "infer_calls": 0,
            "infer_errors": 0,
        }
        logger.info("AIEngine created (not yet initialized)")

    def initialize(self) -> None:
        """Initialize the AI engine and load the default model."""
        if self.initialized:
            logger.warning("AIEngine already initialized")
            return
        self._metrics["initialize_calls"] += 1
        self.load_model("default", {"type": "simulated", "version": "1.0"})
        self.initialized = True
        logger.info("AIEngine initialized, models: %s", self.models.list_models())

    def load_model(self, name: str, config: dict) -> bool:
        """
        Register and mark a model as loaded.

        Returns True on success.
        """
        self._metrics["load_model_calls"] += 1
        self.models.register(name, config)
        self.models.mark_loaded(name)
        logger.info("Model loaded: %s config=%s", name, config)
        return True

    def infer(self, model_name: str, prompt: str, context: dict) -> dict:
        """
        Run inference using the named model.

        Returns a dict with keys: response, confidence, tokens.
        """
        self._metrics["infer_calls"] += 1
        if not self.initialized:
            logger.warning("AIEngine.infer called before initialize()")
            self.initialize()

        model = self.models.get(model_name)
        if model is None:
            # Fall back to default
            model_name = "default"
            model = self.models.get(model_name)
            if model is None:
                self._metrics["infer_errors"] += 1
                return {"response": "No models available.", "confidence": 0.0, "tokens": 0}

        self.models.increment_calls(model_name)
        self._total_inferences += 1

        t0 = time.time()
        result = _simulated_infer(prompt, context)
        result["latency_ms"] = round((time.time() - t0) * 1000, 3)
        logger.debug(
            "Inference: model=%s tokens=%d confidence=%.2f",
            model_name,
            result["tokens"],
            result["confidence"],
        )
        return result

    def get_stats(self) -> dict:
        """Return AI engine statistics."""
        return {
            "initialized": self.initialized,
            "model_count": len(self.models.models),
            "total_inferences": self._total_inferences,
            "metrics": dict(self._metrics),
        }
