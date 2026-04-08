"""
StorageService: Provides namespaced key-value object storage for VAI-OS
cloud services with put/get/delete/list operations.
"""
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Namespaced key-value object storage service."""

    def __init__(self):
        self.store: dict[str, dict] = {}
        self._metrics: dict = {
            "puts": 0,
            "gets": 0,
            "deletes": 0,
            "get_misses": 0,
        }
        logger.info("StorageService initialized")

    def put(self, namespace: str, key: str, value) -> None:
        """Store a value under namespace/key."""
        if namespace not in self.store:
            self.store[namespace] = {}
        self.store[namespace][key] = value
        self._metrics["puts"] += 1
        logger.debug("StorageService.put: ns=%s key=%s", namespace, key)

    def get(self, namespace: str, key: str):
        """
        Retrieve a value by namespace/key.

        Returns None if not found.
        """
        self._metrics["gets"] += 1
        ns = self.store.get(namespace, {})
        if key not in ns:
            self._metrics["get_misses"] += 1
            return None
        return ns[key]

    def delete(self, namespace: str, key: str) -> bool:
        """
        Delete a key from a namespace.

        Returns True if the key existed.
        """
        ns = self.store.get(namespace, {})
        if key in ns:
            del ns[key]
            self._metrics["deletes"] += 1
            logger.debug("StorageService.delete: ns=%s key=%s", namespace, key)
            return True
        return False

    def list(self, namespace: str) -> list[str]:
        """Return a sorted list of keys in the given namespace."""
        return sorted(self.store.get(namespace, {}).keys())

    def list_namespaces(self) -> list[str]:
        """Return a sorted list of all namespaces."""
        return sorted(self.store.keys())

    def get_stats(self) -> dict:
        """Return storage service statistics."""
        return {
            "namespaces": len(self.store),
            "total_keys": sum(len(v) for v in self.store.values()),
            "metrics": dict(self._metrics),
        }
