"""
BuilderAgent: AI agent that plans, executes, and repairs VAI-OS
OS component builds using the virtual filesystem and kernel.
"""
import logging
import time

logger = logging.getLogger(__name__)


class BuilderAgent:
    """AI agent for planning and executing OS component builds."""

    def __init__(self, filesystem, kernel):
        self._fs = filesystem
        self._kernel = kernel
        self._build_log: list[str] = []
        self._metrics: dict = {
            "plans": 0,
            "executions": 0,
            "repairs": 0,
        }
        logger.info("BuilderAgent initialized")

    def start(self) -> None:
        """Activate the builder agent."""
        logger.info("BuilderAgent started")

    def stop(self) -> None:
        """Deactivate the builder agent."""

    def plan_build(self, target: str) -> list[str]:
        """
        Generate a build plan for the given target component.

        Returns an ordered list of build step strings.
        """
        self._metrics["plans"] += 1
        plan = [
            f"check_dependencies:{target}",
            f"compile:{target}",
            f"link:{target}",
            f"test:{target}",
            f"install:{target}",
        ]
        logger.info("BuilderAgent.plan_build: target=%s steps=%d", target, len(plan))
        return plan

    def execute_plan(self, plan: list[str]) -> bool:
        """
        Execute a build plan step by step.

        Returns True if all steps complete successfully.
        """
        self._metrics["executions"] += 1
        for step in plan:
            try:
                self._execute_step(step)
                self._build_log.append(f"[OK] {step}")
                logger.debug("Build step OK: %s", step)
            except Exception as exc:
                self._build_log.append(f"[FAIL] {step}: {exc}")
                logger.error("Build step FAILED: %s -> %s", step, exc)
                return False
        return True

    def _execute_step(self, step: str) -> None:
        """Execute a single build step (simulated)."""
        action, _, target = step.partition(":")
        # Simulated work
        if action == "install" and target:
            path = f"/var/build/{target}"
            self._fs.mkdir(path)
            self._fs.write(f"{path}/build.log", f"Built at {time.time()}")

    def repair(self, component: str) -> bool:
        """
        Attempt to repair a broken component by replanning and rebuilding.

        Returns True if repair succeeded.
        """
        self._metrics["repairs"] += 1
        logger.info("BuilderAgent.repair: component=%s", component)
        plan = self.plan_build(component)
        success = self.execute_plan(plan)
        if success:
            logger.info("BuilderAgent.repair: %s repaired", component)
        else:
            logger.error("BuilderAgent.repair: %s repair FAILED", component)
        return success

    def get_build_log(self) -> list[str]:
        """Return the accumulated build log."""
        return list(self._build_log)
