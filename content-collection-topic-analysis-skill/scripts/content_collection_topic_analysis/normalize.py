from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .models import ContentRecord


def coerce_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if text.endswith("w"):
        return int(float(text[:-1]) * 10000)
    try:
        return int(float(text))
    except ValueError:
        return 0


def normalize_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone().replace(microsecond=0).isoformat()
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("Z", "+00:00")
    for candidate in (text, text.replace("/", "-")):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.isoformat()
        except ValueError:
            continue
    return text


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def should_keep_record(publish_time: str, collect_date: str, days: int) -> bool:
    published = parse_datetime(publish_time)
    collected = parse_datetime(collect_date)
    if published is None or collected is None:
        return True
    if published.tzinfo is not None:
        published = published.astimezone(timezone.utc).replace(tzinfo=None)
    if collected.tzinfo is not None:
        collected = collected.astimezone(timezone.utc).replace(tzinfo=None)
    return published >= collected - timedelta(days=days)


def summarize(raw_item: dict[str, Any]) -> str:
    candidates = [
        raw_item.get("summary"),
        raw_item.get("excerpt"),
        raw_item.get("desc"),
        raw_item.get("content"),
        raw_item.get("raw_content"),
    ]
    for item in candidates:
        if item:
            return str(item).strip()[:240]
    return ""


def normalize_xiaohongshu_item(keyword: str, raw_item: dict[str, Any], collect_date: str) -> ContentRecord:
    return ContentRecord(
        platform="xiaohongshu",
        keyword=keyword,
        title=str(raw_item.get("title") or raw_item.get("note_title") or ""),
        summary=summarize(raw_item),
        author=str(raw_item.get("author") or raw_item.get("nickname") or raw_item.get("user_name") or ""),
        publish_time=normalize_datetime(raw_item.get("published_at") or raw_item.get("publish_time") or ""),
        url=str(raw_item.get("url") or raw_item.get("link") or ""),
        read_count=coerce_int(raw_item.get("read_count")),
        like_count=coerce_int(raw_item.get("likes") or raw_item.get("like_count")),
        looking_count=0,
        share_count=0,
        collect_count=0,
        comment_count=coerce_int(raw_item.get("comments") or raw_item.get("comment_count")),
        raw_content=str(raw_item.get("raw_content") or raw_item.get("content") or ""),
        collect_date=collect_date,
        extra={"source": raw_item},
    )


def normalize_wechat_mp_item(keyword: str, raw_item: dict[str, Any], collect_date: str) -> ContentRecord:
    publish_value = raw_item.get("publish_time_str") or raw_item.get("publish_time") or raw_item.get("published_at") or ""
    return ContentRecord(
        platform="wechat_mp",
        keyword=keyword,
        title=str(raw_item.get("title") or raw_item.get("article_title") or ""),
        summary=summarize(raw_item),
        author=str(
            raw_item.get("author")
            or raw_item.get("wx_name")
            or raw_item.get("account_name")
            or raw_item.get("nickname")
            or ""
        ),
        publish_time=normalize_datetime(publish_value),
        url=str(raw_item.get("url") or raw_item.get("link") or ""),
        read_count=coerce_int(
            raw_item.get("read_count") or raw_item.get("reads") or raw_item.get("read_num") or raw_item.get("read")
        ),
        like_count=coerce_int(
            raw_item.get("like_count") or raw_item.get("likes") or raw_item.get("digg_count") or raw_item.get("praise")
        ),
        looking_count=coerce_int(raw_item.get("looking_count") or raw_item.get("looking")),
        share_count=coerce_int(raw_item.get("share_count") or raw_item.get("share_num")),
        collect_count=coerce_int(raw_item.get("collect_count") or raw_item.get("collect_num")),
        comment_count=coerce_int(raw_item.get("comment_count") or raw_item.get("comments") or raw_item.get("looking")),
        raw_content=str(raw_item.get("raw_content") or raw_item.get("content") or ""),
        collect_date=collect_date,
        extra={"source": raw_item},
    )
