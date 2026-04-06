from __future__ import annotations

from typing import Any

from ..commands import load_json_output, find_first_mapping_list, run_command
from ..models import ContentRecord
from ..normalize import normalize_xiaohongshu_item, should_keep_record


def _sort_key(record: ContentRecord, sort_by: str) -> int | str:
    if sort_by == "read":
        return record.read_count
    if sort_by == "like":
        return record.like_count
    if sort_by == "comment":
        return record.comment_count
    if sort_by == "publish_time":
        return record.publish_time
    return record.read_count + record.like_count + record.comment_count


class XiaohongshuAdapter:
    def __init__(self, opencli_bin: str = "opencli") -> None:
        self._opencli_bin = opencli_bin

    def collect(self, keyword: str, days: int, top_n: int, sort_by: str, collect_date: str) -> list[ContentRecord]:
        command = [
            self._opencli_bin,
            "xiaohongshu",
            "search",
            keyword,
            "--limit",
            str(max(top_n * 3, top_n)),
            "--format",
            "json",
        ]
        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        items = find_first_mapping_list(payload, ("items", "results", "data"))
        records = [
            normalize_xiaohongshu_item(keyword=keyword, raw_item=item, collect_date=collect_date)
            for item in items
        ]
        filtered = [record for record in records if should_keep_record(record.publish_time, collect_date, days)]
        return sorted(filtered, key=lambda item: _sort_key(item, sort_by), reverse=True)[:top_n]

