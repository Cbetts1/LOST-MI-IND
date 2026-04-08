"""
PermissionManager: Role-based access control (RBAC) for VAI-OS.
Manages grant/revoke/check of per-subject, per-resource permissions.
"""
import logging

logger = logging.getLogger(__name__)


class PermissionManager:
    """RBAC permission manager for subjects, resources, and permissions."""

    def __init__(self):
        # policies[subject][resource] = set of permissions
        self.policies: dict[str, dict[str, set]] = {}
        self._metrics: dict = {
            "grants": 0,
            "revokes": 0,
            "checks": 0,
            "check_denials": 0,
        }
        # Bootstrap root with all permissions
        self.grant("root", "*", "read")
        self.grant("root", "*", "write")
        self.grant("root", "*", "exec")
        self.grant("root", "*", "admin")
        logger.info("PermissionManager initialized")

    def grant(self, subject: str, resource: str, permission: str) -> None:
        """Grant a permission to a subject on a resource."""
        if subject not in self.policies:
            self.policies[subject] = {}
        if resource not in self.policies[subject]:
            self.policies[subject][resource] = set()
        self.policies[subject][resource].add(permission)
        self._metrics["grants"] += 1
        logger.debug("Permission granted: %s -> %s:%s", subject, resource, permission)

    def revoke(self, subject: str, resource: str, permission: str) -> bool:
        """
        Revoke a permission from a subject on a resource.

        Returns True if the permission existed and was removed.
        """
        self._metrics["revokes"] += 1
        perms = self.policies.get(subject, {}).get(resource, set())
        if permission in perms:
            perms.discard(permission)
            logger.debug("Permission revoked: %s -> %s:%s", subject, resource, permission)
            return True
        return False

    def check(self, subject: str, resource: str, permission: str) -> bool:
        """
        Check if a subject has a permission on a resource.

        Also checks wildcard resource '*'.
        Returns True if permitted.
        """
        self._metrics["checks"] += 1

        # Root gets everything
        if subject == "root":
            return True

        perms = self.policies.get(subject, {})
        # Check specific resource
        if permission in perms.get(resource, set()):
            return True
        # Check wildcard resource
        if permission in perms.get("*", set()):
            return True

        self._metrics["check_denials"] += 1
        logger.debug("Permission denied: %s -> %s:%s", subject, resource, permission)
        return False

    def list_permissions(self, subject: str) -> dict:
        """Return all resource->permissions mappings for a subject."""
        return {r: set(p) for r, p in self.policies.get(subject, {}).items()}

    def get_stats(self) -> dict:
        """Return permission manager statistics."""
        return {
            "subjects": len(self.policies),
            "metrics": dict(self._metrics),
        }
