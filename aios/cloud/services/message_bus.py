"""
MessageBus: Provides topic-based pub/sub messaging for VAI-OS cloud
services, supporting synchronous callbacks and message history.
"""
import logging
import time

logger = logging.getLogger(__name__)


class MessageBus:
    """Topic-based publish/subscribe message bus."""

    def __init__(self):
        self.topics: dict[str, list] = {}
        self.subscribers: dict[str, list] = {}
        self._metrics: dict = {
            "published": 0,
            "deliveries": 0,
            "topics_created": 0,
        }
        logger.info("MessageBus initialized")

    def _ensure_topic(self, topic: str) -> None:
        """Create topic storage if it doesn't exist."""
        if topic not in self.topics:
            self.topics[topic] = []
            self.subscribers[topic] = []
            self._metrics["topics_created"] += 1
            logger.debug("MessageBus: topic created: %s", topic)

    def publish(self, topic: str, message: dict) -> None:
        """
        Publish a message to a topic.

        Stores the message and notifies all subscribers.
        """
        self._ensure_topic(topic)
        stamped = {"ts": time.time(), "topic": topic, **message}
        self.topics[topic].append(stamped)
        # Keep history bounded
        if len(self.topics[topic]) > 1_000:
            self.topics[topic] = self.topics[topic][-500:]
        self._metrics["published"] += 1

        for callback in self.subscribers.get(topic, []):
            try:
                callback(stamped)
                self._metrics["deliveries"] += 1
            except Exception as exc:
                logger.error("MessageBus subscriber error on topic %s: %s", topic, exc)

        logger.debug("MessageBus.publish: topic=%s", topic)

    def subscribe(self, topic: str, callback) -> None:
        """Subscribe a callable to a topic."""
        self._ensure_topic(topic)
        if callback not in self.subscribers[topic]:
            self.subscribers[topic].append(callback)
            logger.debug("MessageBus.subscribe: topic=%s fn=%s", topic, callback.__name__ if hasattr(callback, "__name__") else callback)

    def unsubscribe(self, topic: str, callback) -> bool:
        """Remove a subscriber from a topic. Returns True if removed."""
        if topic in self.subscribers and callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            return True
        return False

    def get_messages(self, topic: str, limit: int = 10) -> list[dict]:
        """Return the last 'limit' messages for a topic."""
        return self.topics.get(topic, [])[-limit:]

    def list_topics(self) -> list[str]:
        """Return a sorted list of all topics."""
        return sorted(self.topics.keys())

    def get_stats(self) -> dict:
        """Return message bus statistics."""
        return {
            "topic_count": len(self.topics),
            "total_messages": sum(len(v) for v in self.topics.values()),
            "metrics": dict(self._metrics),
        }
