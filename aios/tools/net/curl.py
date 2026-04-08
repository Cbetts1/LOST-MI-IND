"""
VAI-OS Internal curl
HTTP client using stdlib urllib — allows the virtual OS to fetch real URLs.
Architecture: the only module permitted to make outbound host network calls.
"""
import logging
import urllib.request
import urllib.error
import json as _json

logger = logging.getLogger(__name__)


def curl(url: str, method: str = "GET", headers: dict = None, data=None, timeout: int = 15) -> dict:
    """Fetch a URL and return {status, headers, body}.

    Uses the host's urllib so the virtual OS can retrieve packages/data.
    """
    headers = headers or {}
    if isinstance(data, dict):
        data = _json.dumps(data).encode()
        headers.setdefault("Content-Type", "application/json")
    elif isinstance(data, str):
        data = data.encode()

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode(errors="replace")
            result = {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": body,
                "error": None,
            }
            logger.debug("curl %s %s -> %d", method, url, resp.status)
            return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace") if exc.fp else ""
        logger.warning("curl HTTP error %s %s: %d", method, url, exc.code)
        return {"status": exc.code, "headers": {}, "body": body, "error": str(exc)}
    except Exception as exc:
        logger.error("curl error %s %s: %s", method, url, exc)
        return {"status": 0, "headers": {}, "body": "", "error": str(exc)}
