"""
Thread-safe activity tracker for real-time pipeline visualization.

Captures structured events from every pipeline stage and streams them
to the frontend via SSE. Each event includes:
- timestamp, mpn, step, provider, action, detail, source file:line, status, icon
"""
from __future__ import annotations
import time
import threading
import inspect
from collections import defaultdict
from typing import Optional


class ActivityEvent:
    __slots__ = ("timestamp", "mpn", "step", "provider", "action",
                 "detail", "source", "status", "icon", "meta")

    def __init__(self, **kw):
        self.timestamp = kw.get("timestamp", time.time())
        self.mpn = kw.get("mpn", "")
        self.step = kw.get("step", "")
        self.provider = kw.get("provider", "")
        self.action = kw.get("action", "")
        self.detail = kw.get("detail", "")
        self.source = kw.get("source", "")
        self.status = kw.get("status", "running")  # running | success | fail | skip
        self.icon = kw.get("icon", "arrow")  # search | fetch | extract | normalize | validate | score | done | error | arrow
        self.meta = kw.get("meta", {})

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "mpn": self.mpn,
            "step": self.step,
            "provider": self.provider,
            "action": self.action,
            "detail": self.detail,
            "source": self.source,
            "status": self.status,
            "icon": self.icon,
        }


def _caller_source(skip: int = 1) -> str:
    """Get file:line of the caller."""
    frame = inspect.currentframe()
    for _ in range(skip + 1):
        frame = frame.f_back
        if frame is None:
            return ""
    import os
    fname = os.path.basename(frame.f_code.co_filename)
    return f"{fname}:{frame.f_lineno}"


class ActivityTracker:
    """
    Thread-safe, ring-buffer activity store.
    One tracker instance is shared across the entire pipeline.
    """

    def __init__(self, max_events: int = 500):
        self._events: list[ActivityEvent] = []
        self._lock = threading.Lock()
        self._max = max_events
        self._sequence = 0

    def emit(self, **kw) -> ActivityEvent:
        """Emit an activity event. Returns the event for chaining."""
        if "source" not in kw or not kw["source"]:
            kw["source"] = _caller_source(skip=2)
        ev = ActivityEvent(**kw)
        with self._lock:
            self._sequence += 1
            ev.meta["seq"] = self._sequence
            self._events.append(ev)
            if len(self._events) > self._max:
                self._events = self._events[-self._max:]
        return ev

    def get_since(self, last_seq: int = 0) -> list[dict]:
        """Return events with seq > last_seq."""
        with self._lock:
            return [e.to_dict() | {"seq": e.meta.get("seq", 0)}
                    for e in self._events if e.meta.get("seq", 0) > last_seq]

    def get_all(self) -> list[dict]:
        with self._lock:
            return [e.to_dict() | {"seq": e.meta.get("seq", 0)}
                    for e in self._events]

    def clear(self):
        with self._lock:
            self._events.clear()
            self._sequence = 0


# ── Global singleton ──────────────────────────────────────────────────
tracker = ActivityTracker()
