"""
services/rate_limiter.py

Simple file-backed rate limiter helper to enforce max replies per user per hour.
Uses timestamps stored in the processed store (in memory or on disk).
"""
from __future__ import annotations
import time
from typing import Dict, List


class RateLimiter:
    def __init__(self, max_per_hour: int = 5):
        self.max_per_hour = max_per_hour

    def prune_old(self, timestamps: List[float]) -> List[float]:
        cutoff = time.time() - 3600
        return [t for t in timestamps if t >= cutoff]

    def allow(self, user_id: str, replies_map: Dict[str, List[float]]) -> bool:
        lst = replies_map.get(user_id, [])
        lst = self.prune_old(lst)
        return len(lst) < self.max_per_hour

    def record(self, user_id: str, replies_map: Dict[str, List[float]]) -> None:
        lst = replies_map.setdefault(user_id, [])
        lst.append(time.time())
        # prune inline
        replies_map[user_id] = self.prune_old(lst)
