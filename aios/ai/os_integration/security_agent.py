"""
SecurityAgent: AI agent that scans for policy violations, enforces
security policies, and generates security reports for VAI-OS.
"""
import logging
import time

logger = logging.getLogger(__name__)


class SecurityAgent:
    """AI agent for security scanning and policy enforcement."""

    def __init__(self, permission_manager, audit_log):
        self._perm = permission_manager
        self._audit = audit_log
        self._active = False
        self._last_scan: float = 0.0
        self._metrics: dict = {
            "scans": 0,
            "enforce_calls": 0,
            "findings": 0,
        }
        logger.info("SecurityAgent initialized")

    def start(self) -> None:
        """Activate the security agent."""
        self._active = True
        logger.info("SecurityAgent started")

    def stop(self) -> None:
        """Deactivate the security agent."""
        self._active = False

    def scan(self) -> list[dict]:
        """
        Scan for potential security threats and policy violations.

        Returns a list of finding dicts with keys: severity, description, subject.
        """
        self._metrics["scans"] += 1
        self._last_scan = time.time()
        findings: list[dict] = []

        # Check for overly permissive policies
        for subject, resources in self._perm.policies.items():
            for resource, perms in resources.items():
                if "admin" in perms and subject != "root":
                    findings.append({
                        "severity": "high",
                        "description": f"Non-root subject '{subject}' has admin on '{resource}'",
                        "subject": subject,
                    })

        # Check recent audit log for denied actions (potential probing)
        recent = self._audit.tail(50)
        denied = [e for e in recent if e.get("outcome") == "denied"]
        if len(denied) > 5:
            findings.append({
                "severity": "medium",
                "description": f"{len(denied)} denied actions in recent audit log",
                "subject": "system",
            })

        self._metrics["findings"] += len(findings)
        logger.info("SecurityAgent.scan: %d findings", len(findings))
        return findings

    def enforce_policy(self) -> int:
        """
        Enforce security policies: revoke unauthorized permissions.

        Returns the number of violations remediated.
        """
        self._metrics["enforce_calls"] += 1
        findings = self.scan()
        remediated = 0
        for finding in findings:
            if finding["severity"] == "high":
                subject = finding["subject"]
                # Revoke all admin permissions for non-root subjects
                for resource in list(self._perm.policies.get(subject, {}).keys()):
                    self._perm.revoke(subject, resource, "admin")
                    remediated += 1
                    logger.warning(
                        "SecurityAgent revoked admin from %s on %s", subject, resource
                    )
        return remediated

    def report(self) -> str:
        """Generate a human-readable security report."""
        findings = self.scan()
        high = [f for f in findings if f["severity"] == "high"]
        medium = [f for f in findings if f["severity"] == "medium"]
        return (
            f"Security Report (last scan: {self._last_scan:.0f})\n"
            f"  Findings: {len(findings)} total, {len(high)} high, {len(medium)} medium\n"
            + "".join(f"  [{f['severity'].upper()}] {f['description']}\n" for f in findings[:5])
            + ("  System: No critical threats detected" if not high else "  ⚠ Action required")
        )
