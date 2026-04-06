from __future__ import annotations

from typing import Protocol

from ..models import ContentRecord


class PlatformAdapter(Protocol):
    def collect(self, keyword: str, days: int, top_n: int, sort_by: str, collect_date: str) -> list[ContentRecord]:
        ...

