"""
io.py -- Virtual I/O Subsystem for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualIO simulates touch input, hardware buttons, and USB-C.
  - Events are placed in an event queue; OS/Shell consumes them via handle_event().
  - Supports event injection for testing.
  - Consumed by: Shell/UI layer (input handling), OS Kernel (interrupt dispatch).

Integration Points:
  - Input events -> OS Kernel interrupt simulation
  - Input events -> Shell/UI (touch, button press)
  - USB attach/detach -> System Services (charging, ADB)
  - Metrics -> HardwareMetrics
  - Hooks -> HardwareHooks
"""

import logging
import queue
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.io")

# Event type constants
EVT_TOUCH_DOWN  = "touch_down"
EVT_TOUCH_UP    = "touch_up"
EVT_TOUCH_MOVE  = "touch_move"
EVT_BUTTON      = "button"
EVT_USB_ATTACH  = "usb_attach"
EVT_USB_DETACH  = "usb_detach"
EVT_KEY         = "key"

BUTTONS = ("power", "vol_up", "vol_down", "fingerprint")


class IOEvent:
    """Represents a virtual input/output event."""
    def __init__(self, event_type: str, data: Dict[str, Any]) -> None:
        self.event_type = event_type
        self.data = data
        self.timestamp = time.monotonic()

    def __repr__(self) -> str:
        return f"<IOEvent type={self.event_type!r} data={self.data}>"


class VirtualIO:
    """
    Simulates mobile device I/O: touchscreen, buttons, USB-C.
    """

    def __init__(self, metrics=None, hooks=None) -> None:
        self._metrics = metrics
        self._hooks = hooks
        self._event_queue: queue.Queue = queue.Queue(maxsize=2048)
        self._event_count: int = 0
        self._usb_connected: bool = False
        self._init_time = time.monotonic()
        logger.info("[IO]   VirtualIO online -- touch, buttons, USB-C")
        if self._hooks:
            self._hooks.fire("io.init", {})

    def inject_event(self, event: IOEvent) -> None:
        """Inject an event (used by tests or hardware simulation)."""
        self._event_queue.put_nowait(event)

    def handle_event(self, event: IOEvent) -> Dict[str, Any]:
        """
        Process a single I/O event.

        Returns a dict describing the handled action.
        """
        self._event_count += 1
        if self._metrics:
            self._metrics.increment_counter("io.events_handled")
        if self._hooks:
            self._hooks.fire(f"io.{event.event_type}", event.data)

        if event.event_type == EVT_TOUCH_DOWN:
            return {"action": "touch_start", "pos": event.data.get("pos")}
        elif event.event_type == EVT_TOUCH_UP:
            return {"action": "touch_end", "pos": event.data.get("pos")}
        elif event.event_type == EVT_TOUCH_MOVE:
            return {"action": "touch_drag", "pos": event.data.get("pos")}
        elif event.event_type == EVT_BUTTON:
            btn = event.data.get("button")
            pressed = event.data.get("pressed", True)
            logger.debug("[IO] Button %r %s", btn, "pressed" if pressed else "released")
            return {"action": "button", "button": btn, "pressed": pressed}
        elif event.event_type == EVT_USB_ATTACH:
            self._usb_connected = True
            logger.info("[IO] USB-C attached")
            return {"action": "usb_attach"}
        elif event.event_type == EVT_USB_DETACH:
            self._usb_connected = False
            logger.info("[IO] USB-C detached")
            return {"action": "usb_detach"}
        elif event.event_type == EVT_KEY:
            return {"action": "key", "key": event.data.get("key"), "mod": event.data.get("mod")}
        else:
            return {"action": "unknown", "event_type": event.event_type}

    def poll(self, timeout: float = 0.0) -> Optional[IOEvent]:
        """Poll for the next event. Returns None if none pending."""
        try:
            return self._event_queue.get(block=timeout > 0, timeout=timeout or None)
        except queue.Empty:
            return None

    def is_usb_connected(self) -> bool:
        return self._usb_connected

    def introspect(self) -> Dict[str, Any]:
        return {
            "event_count": self._event_count,
            "queue_depth": self._event_queue.qsize(),
            "usb_connected": self._usb_connected,
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return f"<VirtualIO events={self._event_count} queue={self._event_queue.qsize()} usb={'Y' if self._usb_connected else 'N'}>"
