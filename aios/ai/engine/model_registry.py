"""
ModelRegistry: Maintains a registry of AI model configurations and
usage statistics for the VAI-OS AI engine.
"""
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for AI model metadata and usage counters."""

    def __init__(self):
        self.models: dict[str, dict] = {}
        self._metrics: dict = {
            "registrations": 0,
            "unregistrations": 0,
        }
        logger.info("ModelRegistry initialized")

    def register(self, name: str, config: dict) -> None:
        """Register a model with its configuration."""
        self.models[name] = {
            "name": name,
            "config": dict(config),
            "loaded": False,
            "calls": 0,
        }
        self._metrics["registrations"] += 1
        logger.info("Model registered: %s", name)

    def get(self, name: str) -> dict | None:
        """Return the model dict for the given name, or None."""
        return self.models.get(name)

    def list_models(self) -> list[str]:
        """Return a sorted list of registered model names."""
        return sorted(self.models.keys())

    def unregister(self, name: str) -> bool:
        """Remove a model from the registry. Returns True if it existed."""
        if name in self.models:
            del self.models[name]
            self._metrics["unregistrations"] += 1
            logger.info("Model unregistered: %s", name)
            return True
        return False

    def mark_loaded(self, name: str) -> None:
        """Mark a model as loaded (weights resident in memory)."""
        if name in self.models:
            self.models[name]["loaded"] = True
            logger.debug("Model marked loaded: %s", name)

    def increment_calls(self, name: str) -> None:
        """Increment the call counter for a model."""
        if name in self.models:
            self.models[name]["calls"] += 1

    def get_stats(self) -> dict:
        """Return registry statistics."""
        return {
            "model_count": len(self.models),
            "loaded": [n for n, m in self.models.items() if m["loaded"]],
            "metrics": dict(self._metrics),
        }
