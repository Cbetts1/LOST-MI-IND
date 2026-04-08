"""
AIController: Coordinates all AI agents registered in the VAI-OS system,
routes requests to appropriate agents, and manages agent lifecycle.
"""
import logging

logger = logging.getLogger(__name__)


class AIController:
    """Central coordinator for VAI-OS AI agents."""

    def __init__(self, kernel, ai_engine):
        self._kernel = kernel
        self._engine = ai_engine
        self.agents: dict[str, object] = {}
        self._running: bool = False
        self._metrics: dict = {
            "requests_routed": 0,
            "routing_errors": 0,
        }
        logger.info("AIController initialized")

    def register_agent(self, name: str, agent: object) -> None:
        """Register an AI agent under the given name."""
        self.agents[name] = agent
        logger.info("AI agent registered: %s (%s)", name, type(agent).__name__)

    def start_all(self) -> None:
        """Start all registered agents (call start() if available)."""
        self._running = True
        for name, agent in self.agents.items():
            if hasattr(agent, "start"):
                try:
                    agent.start()
                    logger.info("Agent started: %s", name)
                except Exception as exc:
                    logger.error("Agent %s failed to start: %s", name, exc)

    def stop_all(self) -> None:
        """Stop all registered agents (call stop() if available)."""
        self._running = False
        for name, agent in self.agents.items():
            if hasattr(agent, "stop"):
                try:
                    agent.stop()
                    logger.info("Agent stopped: %s", name)
                except Exception as exc:
                    logger.error("Agent %s failed to stop: %s", name, exc)

    def route_request(self, request: dict) -> dict:
        """
        Route a request dict to the appropriate agent.

        The request must contain a 'target' key naming the destination agent.
        Returns the agent's response dict, or an error dict.
        """
        self._metrics["requests_routed"] += 1
        target = request.get("target", "")
        if target not in self.agents:
            self._metrics["routing_errors"] += 1
            logger.warning("No agent for target: %s", target)
            return {"error": f"No agent: {target!r}", "target": target}

        agent = self.agents[target]
        action = request.get("action", "")
        payload = request.get("payload", {})

        if hasattr(agent, action):
            try:
                fn = getattr(agent, action)
                result = fn(**payload) if payload else fn()
                logger.debug("Routed request: target=%s action=%s", target, action)
                return {"target": target, "action": action, "result": result}
            except Exception as exc:
                self._metrics["routing_errors"] += 1
                logger.error("Agent %s.%s raised: %s", target, action, exc)
                return {"error": str(exc), "target": target, "action": action}
        return {"error": f"Agent {target!r} has no action {action!r}"}

    def get_stats(self) -> dict:
        """Return controller statistics."""
        return {
            "agent_count": len(self.agents),
            "agent_names": list(self.agents.keys()),
            "running": self._running,
            "metrics": dict(self._metrics),
        }
