"""
VirtualFS: An in-memory virtual filesystem supporting hierarchical paths,
directory creation, file read/write, and directory listing.
"""
import logging
import time

logger = logging.getLogger(__name__)

_SEP = "/"


class VirtualFile:
    """Represents an open virtual file handle."""

    def __init__(self, path: str, mode: str, fs: "VirtualFS"):
        self.path = path
        self.mode = mode
        self._fs = fs
        self._closed = False

    def read(self) -> str:
        """Read the file contents."""
        if self._closed:
            raise IOError(f"File {self.path!r} is closed")
        return self._fs.read(self.path)

    def write(self, data: str) -> None:
        """Write data to the file."""
        if self._closed:
            raise IOError(f"File {self.path!r} is closed")
        if "r" in self.mode and "+" not in self.mode:
            raise IOError(f"File {self.path!r} opened read-only")
        self._fs.write(self.path, data)

    def close(self) -> None:
        """Close the file handle."""
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class VirtualFS:
    """In-memory hierarchical virtual filesystem."""

    def __init__(self):
        # tree stores directories as dict, files as str
        self._tree: dict = {}
        self._metadata: dict = {}  # path -> {created, modified, size}
        self._metrics: dict = {
            "mkdir_calls": 0,
            "write_calls": 0,
            "read_calls": 0,
            "open_calls": 0,
        }
        # Bootstrap essential directories
        for d in ("/", "/bin", "/etc", "/home", "/tmp", "/var", "/proc"):
            self.mkdir(d)
        logger.info("VirtualFS initialized")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parts(self, path: str) -> list[str]:
        """Split an absolute path into non-empty segments."""
        return [p for p in path.split(_SEP) if p]

    def _navigate(self, parts: list[str], create_dirs: bool = False) -> dict | None:
        """Navigate the tree to the node at parts, optionally creating dirs."""
        node = self._tree
        for part in parts:
            if part not in node:
                if create_dirs:
                    node[part] = {}
                else:
                    return None
            if isinstance(node[part], str):
                return None  # file, not dir
            node = node[part]
        return node

    def _normalize(self, path: str) -> str:
        """Return a normalized absolute path."""
        if not path.startswith(_SEP):
            path = _SEP + path
        # Collapse double slashes
        while "//" in path:
            path = path.replace("//", "/")
        return path.rstrip(_SEP) or _SEP

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mkdir(self, path: str) -> None:
        """Create a directory (and any missing parents)."""
        path = self._normalize(path)
        parts = self._parts(path)
        self._navigate(parts, create_dirs=True)
        self._metrics["mkdir_calls"] += 1
        logger.debug("mkdir: %s", path)

    def exists(self, path: str) -> bool:
        """Return True if the path exists (file or directory)."""
        path = self._normalize(path)
        if path == _SEP:
            return True
        parts = self._parts(path)
        parent = self._navigate(parts[:-1])
        if parent is None:
            return False
        return parts[-1] in parent

    def open(self, path: str, mode: str = "r") -> VirtualFile:
        """Open a file and return a VirtualFile handle."""
        path = self._normalize(path)
        self._metrics["open_calls"] += 1
        if "w" in mode or "a" in mode:
            if not self.exists(path):
                # Create file
                parts = self._parts(path)
                parent = self._navigate(parts[:-1], create_dirs=True)
                if parent is not None:
                    parent[parts[-1]] = ""
            if "a" in mode:
                pass  # append handled in write
        if not self.exists(path):
            raise FileNotFoundError(f"No such file: {path!r}")
        return VirtualFile(path, mode, self)

    def read(self, path: str) -> str:
        """Read and return the contents of a file."""
        path = self._normalize(path)
        self._metrics["read_calls"] += 1
        parts = self._parts(path)
        parent = self._navigate(parts[:-1])
        if parent is None or parts[-1] not in parent:
            raise FileNotFoundError(f"No such file: {path!r}")
        content = parent[parts[-1]]
        if isinstance(content, dict):
            raise IsADirectoryError(f"Is a directory: {path!r}")
        logger.debug("read: %s (%d bytes)", path, len(content))
        return content

    def write(self, path: str, data: str) -> None:
        """Write data to a file, creating it if necessary."""
        path = self._normalize(path)
        self._metrics["write_calls"] += 1
        parts = self._parts(path)
        parent = self._navigate(parts[:-1], create_dirs=True)
        if parent is None:
            raise OSError(f"Cannot write to {path!r}")
        parent[parts[-1]] = data
        self._metadata[path] = {
            "modified": time.time(),
            "size": len(data),
        }
        logger.debug("write: %s (%d bytes)", path, len(data))

    def append(self, path: str, data: str) -> None:
        """Append data to a file."""
        existing = ""
        if self.exists(path):
            existing = self.read(path)
        self.write(path, existing + data)

    def ls(self, path: str = "/") -> list[str]:
        """List the contents of a directory."""
        path = self._normalize(path)
        parts = self._parts(path)
        node = self._navigate(parts) if parts else self._tree
        if node is None or isinstance(node, str):
            raise NotADirectoryError(f"Not a directory: {path!r}")
        return sorted(node.keys())

    def rm(self, path: str) -> bool:
        """Remove a file."""
        path = self._normalize(path)
        parts = self._parts(path)
        parent = self._navigate(parts[:-1])
        if parent and parts[-1] in parent and isinstance(parent[parts[-1]], str):
            del parent[parts[-1]]
            logger.debug("rm: %s", path)
            return True
        return False

    def get_stats(self) -> dict:
        """Return filesystem statistics."""
        return {"metrics": dict(self._metrics)}
