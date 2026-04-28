"""
Per-user message queue.

Ensures that if a user sends multiple messages quickly, they are
processed one at a time (in order) without blocking other users.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor


class PerUserQueue:
    def __init__(self, max_workers: int = 5) -> None:
        self._executor   = ThreadPoolExecutor(max_workers=max_workers)
        self._queues:  dict[str, deque]        = defaultdict(deque)
        self._active:  dict[str, bool]         = defaultdict(bool)
        self._lock     = threading.Lock()

    def submit(self, user_id: str, fn, *args, **kwargs) -> None:
        """Enqueue a task for a user. Runs immediately if user is idle."""
        with self._lock:
            self._queues[user_id].append((fn, args, kwargs))
            if not self._active[user_id]:
                self._active[user_id] = True
                self._executor.submit(self._drain, user_id)

    def _drain(self, user_id: str) -> None:
        """Process all queued tasks for a user sequentially."""
        while True:
            with self._lock:
                if not self._queues[user_id]:
                    self._active[user_id] = False
                    return
                fn, args, kwargs = self._queues[user_id].popleft()
            try:
                fn(*args, **kwargs)
            except Exception:
                pass  # errors are logged inside the task itself
