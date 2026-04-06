from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any


def _stable_hash(parts: list[str]) -> str:
    text = "|".join(parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ContentRecord:
    platform: str
    keyword: str
    title: str
    summary: str
    author: str
    publish_time: str
    url: str
    read_count: int
    like_count: int
    comment_count: int
    raw_content: str
    collect_date: str
    looking_count: int = 0
    share_count: int = 0
    collect_count: int = 0
    monitor_type: str = "keyword"
    creator_name: str = ""
    match_author: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def record_key(self) -> str:
        if self.url:
            return _stable_hash([self.platform, self.url])
        return _stable_hash([self.platform, self.title, self.author, self.publish_time])


@dataclass(frozen=True)
class TopicInsightRecord:
    platform: str
    keyword: str
    collect_date: str
    sample_size: int
    topic_direction: str
    why_it_works: str
    content_angle_suggestion: str

    @property
    def analysis_key(self) -> str:
        return _stable_hash([self.platform, self.keyword, self.collect_date])


@dataclass(frozen=True)
class PipelineRequest:
    keywords: list[str]
    platforms: list[str]
    days: int
    top_n: int
    sort_by: str
    with_analysis: bool
    collect_date: str
    dry_run: bool = False


@dataclass(frozen=True)
class PipelineResult:
    content_count: int
    analysis_count: int
    records: list[ContentRecord] = field(default_factory=list)
    analyses: list[TopicInsightRecord] = field(default_factory=list)
