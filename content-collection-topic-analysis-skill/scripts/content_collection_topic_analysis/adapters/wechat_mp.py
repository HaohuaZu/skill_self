from __future__ import annotations

import json
import math
from typing import Any
from urllib import request as urllib_request

from ..commands import IntegrationConfigError, SkillError, find_first_mapping_list
from ..models import ContentRecord
from ..normalize import normalize_wechat_mp_item, should_keep_record


def _sort_key(record: ContentRecord, sort_by: str) -> int | str:
    if sort_by == "read":
        return record.read_count
    if sort_by == "like":
        return record.like_count
    if sort_by == "comment":
        return record.comment_count
    if sort_by == "publish_time":
        return record.publish_time
    return (
        record.read_count
        + record.like_count
        + record.looking_count
        + record.share_count
        + record.collect_count
        + record.comment_count
    )


class WechatMPAdapter:
    def __init__(self, api_url: str | None, api_key: str | None = None, metrics_api_url: str | None = None) -> None:
        self._api_url = api_url
        self._api_key = api_key
        self._metrics_api_url = metrics_api_url

    def collect(self, keyword: str, days: int, top_n: int, sort_by: str, collect_date: str) -> list[ContentRecord]:
        if not self._api_url or not self._api_key:
            raise IntegrationConfigError("wechat_mp collection requires WECHAT_API_URL and WECHAT_API_KEY")
        first_page = self._fetch_page(keyword=keyword, days=days, page=1, sort_by=sort_by)
        page_size = max(int(first_page.get("data_number") or len(first_page.get("data", [])) or 20), 1)
        total_pages = int(first_page.get("total_page") or 1)
        requested_pages = calculate_fetch_pages(top_n=top_n, page_size=page_size, max_pages=total_pages)

        items: list[dict[str, Any]] = list(first_page.get("data", []))
        for page in range(2, requested_pages + 1):
            page_payload = self._fetch_page(keyword=keyword, days=days, page=page, sort_by=sort_by)
            items.extend(page_payload.get("data", []))

        deduped = dedupe_by_url(items)
        if sort_by in {"like", "comment", "engagement"}:
            enriched_items = [self._enrich_metrics(item) for item in deduped]
        else:
            enriched_items = deduped[:top_n]
            enriched_items = [self._enrich_metrics(item) for item in enriched_items]
            if len(deduped) > len(enriched_items):
                enriched_items.extend(deduped[len(enriched_items) :])

        records = [normalize_wechat_mp_item(keyword=keyword, raw_item=item, collect_date=collect_date) for item in enriched_items]
        filtered = [record for record in records if should_keep_record(record.publish_time, collect_date, days)]
        return sorted(filtered, key=lambda item: _sort_key(item, sort_by), reverse=True)[:top_n]

    def _fetch_page(self, keyword: str, days: int, page: int, sort_by: str) -> dict[str, Any]:
        payload = build_search_payload(keyword=keyword, days=days, page=page, sort_by=sort_by, api_key=self._api_key or "")
        body = self._post_json(self._api_url or "", payload)

        if body.get("code") != 0:
            raise SkillError(f"wechat_mp API failed: code={body.get('code')} msg={body.get('msg')}")

        items = find_first_mapping_list(body.get("data"), ("data", "items", "articles", "results"))
        if not isinstance(items, list):
            raise SkillError("wechat_mp API returned invalid data payload")
        return {
            "data": items,
            "data_number": int(body.get("data_number") or len(items) or 0),
            "total_page": int(body.get("total_page") or 1),
            "total": int(body.get("total") or len(items) or 0),
            "page": int(body.get("page") or page),
        }

    def _enrich_metrics(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        if not self._metrics_api_url or not self._api_key:
            return raw_item
        article_url = str(raw_item.get("url") or "").strip()
        if not article_url:
            return raw_item
        try:
            body = self._post_json(
                self._metrics_api_url,
                {
                    "url": article_url,
                    "key": self._api_key,
                },
            )
        except Exception:
            return raw_item

        if body.get("code") != 0 or not isinstance(body.get("data"), dict):
            return raw_item

        detail = body.get("data", {})
        merged = dict(raw_item)
        merged["read"] = detail.get("read", raw_item.get("read"))
        merged["praise"] = detail.get("zan", raw_item.get("praise"))
        merged["looking"] = detail.get("looking", raw_item.get("looking"))
        merged["share_num"] = max(int(detail.get("share_num") or 0), 0)
        merged["collect_num"] = max(int(detail.get("collect_num") or 0), 0)
        merged["comment_count"] = max(int(detail.get("comment_count") or 0), 0)
        return merged

    @staticmethod
    def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))


def build_search_payload(keyword: str, days: int, page: int, sort_by: str, api_key: str) -> dict[str, Any]:
    return {
        "kw": keyword,
        "sort_type": 2 if sort_by == "publish_time" else 1,
        "mode": 3,
        "period": max(1, min(days, 30)),
        "page": page,
        "key": api_key,
        "any_kw": "",
        "ex_kw": "",
    }


def build_cn8n_payload(keyword: str, days: int, page: int) -> dict[str, Any]:
    return {
        "kw": keyword,
        "sort_type": 1,
        "mode": 1,
        "period": days,
        "page": page,
        "any_kw": "",
        "ex_kw": "",
        "verifycode": "",
        "type": 1,
    }


def dedupe_by_url(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        url = str(item.get("url") or "").strip()
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        deduped.append(item)
    return deduped


def filter_records_by_exact_author(records: list[ContentRecord], author_name: str) -> list[ContentRecord]:
    return [record for record in records if record.author == author_name]


def calculate_fetch_pages(top_n: int, page_size: int, max_pages: int) -> int:
    if top_n <= 0:
        return 1
    if page_size <= 0:
        return 1
    return max(1, min(max_pages, math.ceil(top_n / page_size)))
