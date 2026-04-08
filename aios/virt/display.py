"""
display.py -- Virtual Display / Framebuffer for VAI-OS Virtual Hardware Layer

Architecture Notes:
  - VirtualDisplay simulates a high-resolution OLED mobile display.
  - Maintains a virtual framebuffer as a list of pixel rows.
  - render(frame) accepts a frame object and updates the framebuffer.
  - get_framebuffer() returns current display state.
  - Consumed by: Shell/UI layer (renderer.py), AI (screen observation).

Integration Points:
  - Framebuffer -> Shell/UI renderer
  - Display metrics (FPS, rendered frames) -> HardwareMetrics
  - Display events (brightness, on/off) -> System Services (power)
  - Hooks -> HardwareHooks
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("vaios.virt.display")

DEFAULT_WIDTH = 2400
DEFAULT_HEIGHT = 1080
DEFAULT_FPS = 60
DEFAULT_PANEL = "OLED"


class Frame:
    """Represents a single rendered frame."""
    def __init__(self, width: int, height: int, data: Optional[bytes] = None) -> None:
        self.width = width
        self.height = height
        self.data = data or bytes(width * height * 4)  # RGBA
        self.timestamp = time.monotonic()

    def __repr__(self) -> str:
        return f"<Frame {self.width}x{self.height} size={len(self.data)}B>"


class VirtualDisplay:
    """
    Simulates a mobile OLED display with virtual framebuffer.

    Resolution: 2400x1080 (default)
    Panel: OLED, 60Hz
    """

    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        fps: int = DEFAULT_FPS,
        panel: str = DEFAULT_PANEL,
        metrics=None,
        hooks=None,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.panel = panel
        self._metrics = metrics
        self._hooks = hooks
        self._framebuffer: Optional[Frame] = None
        self._frames_rendered: int = 0
        self._brightness: float = 1.0  # 0.0 - 1.0
        self._power_on: bool = True
        self._init_time = time.monotonic()
        self._last_frame_time: float = 0.0
        logger.info(
            "[DSP]  VirtualDisplay online -- %dx%d %s %dHz",
            width, height, panel, fps,
        )
        if self._hooks:
            self._hooks.fire("display.init", {"width": width, "height": height, "panel": panel})

    def render(self, frame: Frame) -> None:
        """Render a frame to the virtual framebuffer."""
        if not self._power_on:
            return
        if frame.width != self.width or frame.height != self.height:
            raise ValueError(
                f"Frame resolution {frame.width}x{frame.height} "
                f"does not match display {self.width}x{self.height}"
            )
        self._framebuffer = frame
        self._frames_rendered += 1
        self._last_frame_time = time.monotonic()
        elapsed = self._last_frame_time - self._init_time
        fps_actual = self._frames_rendered / elapsed if elapsed > 0 else 0.0
        if self._metrics:
            self._metrics.increment_counter("display.frames_rendered")
            self._metrics.set_gauge("display.fps_actual", fps_actual)
        if self._hooks:
            self._hooks.fire("display.render", {"frame_num": self._frames_rendered, "fps": fps_actual})

    def get_framebuffer(self) -> Optional[Frame]:
        """Return the current framebuffer frame."""
        return self._framebuffer

    def set_brightness(self, level: float) -> None:
        """Set display brightness (0.0 = off, 1.0 = max)."""
        self._brightness = max(0.0, min(1.0, level))
        if self._metrics:
            self._metrics.set_gauge("display.brightness", self._brightness)
        if self._hooks:
            self._hooks.fire("display.brightness", {"level": self._brightness})

    def power_off(self) -> None:
        self._power_on = False
        logger.info("[DSP] Display powered off")
        if self._hooks:
            self._hooks.fire("display.power", {"state": "off"})

    def power_on(self) -> None:
        self._power_on = True
        logger.info("[DSP] Display powered on")
        if self._hooks:
            self._hooks.fire("display.power", {"state": "on"})

    def make_frame(self, data: Optional[bytes] = None) -> Frame:
        """Convenience: create a Frame sized for this display."""
        return Frame(self.width, self.height, data)

    def introspect(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "fps_target": self.fps,
            "panel": self.panel,
            "power_on": self._power_on,
            "brightness": self._brightness,
            "frames_rendered": self._frames_rendered,
            "uptime_s": time.monotonic() - self._init_time,
        }

    def __repr__(self) -> str:
        return (
            f"<VirtualDisplay {self.width}x{self.height} {self.panel} "
            f"{'ON' if self._power_on else 'OFF'} frames={self._frames_rendered}>"
        )
