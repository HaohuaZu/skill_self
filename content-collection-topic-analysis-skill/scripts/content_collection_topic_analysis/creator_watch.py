from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Sequence

from .adapters.wechat_mp import WechatMPAdapter, filter_records_by_exact_author
from .commands import IntegrationConfigError
from .config import SkillConfig
from .lark_base import LarkBaseWriter, StdoutWriter
from .models import ContentRecord
from .pipeline import deduplicate_records


@dataclass(frozen=True)
class CreatorWatchConfig:
    platform: str
    match_mode: str
    creators: list[str]


def load_creator_watchlist(path: str) -> CreatorWatchConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return CreatorWatchConfig(
        platform=str(payload.get("platform") or "wechat_mp"),
        match_mode=str(payload.get("match_mode") or "exact"),
        creators=[str(item).strip() for item in payload.get("creators", []) if str(item).strip()],
    )


def build_creator_watch_records(
    *,
    watch: CreatorWatchConfig,
    adapter: WechatMPAdapter,
    days: int,
    top_n: int,
    collect_date: str,
) -> list[ContentRecord]:
    if watch.platform != "wechat_mp":
        raise IntegrationConfigError("creator watch currently supports only wechat_mp")
    if watch.match_mode != "exact":
        raise IntegrationConfigError("creator watch currently supports only exact match mode")

    records: list[ContentRecord] = []
    for creator in watch.creators:
        matched = filter_records_by_exact_author(
            adapter.collect(
                keyword=creator,
                days=days,
                top_n=top_n,
                sort_by="publish_time",
                collect_date=collect_date,
            ),
            creator,
        )
        records.extend(
            replace(
                record,
                keyword=creator,
                monitor_type="creator_watch",
                creator_name=creator,
                match_author=record.author,
            )
            for record in matched
        )
    return deduplicate_records(records)


def run_creator_watch(
    *,
    watch: CreatorWatchConfig,
    adapter: WechatMPAdapter,
    writer: LarkBaseWriter | StdoutWriter | object,
    days: int,
    top_n: int,
    collect_date: str,
) -> list[ContentRecord]:
    records = build_creator_watch_records(
        watch=watch,
        adapter=adapter,
        days=days,
        top_n=top_n,
        collect_date=collect_date,
    )
    writer.write_content_records(records)
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor exact WeChat MP creators and write new articles to Lark Base.")
    parser.add_argument("--watchlist", help="override creator watchlist json path")
    parser.add_argument("--days", type=int, default=1, help="collect recent N days")
    parser.add_argument("--top-n", type=int, default=10, help="top N items per creator")
    parser.add_argument("--collect-date", default=date.today().isoformat(), help="logical collect date, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="collect and print JSON instead of writing to Lark")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SkillConfig.from_env()
    watchlist_path = args.watchlist or config.creator_watchlist_path
    if not watchlist_path:
        raise IntegrationConfigError("creator watch requires CREATOR_WATCHLIST_PATH or --watchlist")

    watch = load_creator_watchlist(watchlist_path)
    config.validate(platforms=[watch.platform], with_analysis=False)
    adapter = WechatMPAdapter(api_url=config.cn8n_api_url, api_key=config.cn8n_api_key)
    writer = (
        StdoutWriter()
        if args.dry_run
        else LarkBaseWriter(
            lark_cli_bin=config.lark_cli_bin,
            identity=config.lark_identity,
            base_token=config.lark_base_token,
            base_name=config.lark_base_name,
            folder_token=config.lark_folder_token,
            content_table_name=config.content_table_name,
            content_table_id=config.content_table_id,
            analysis_table_name=config.analysis_table_name,
            analysis_table_id=config.analysis_table_id,
        )
    )

    records = run_creator_watch(
        watch=watch,
        adapter=adapter,
        writer=writer,
        days=args.days,
        top_n=args.top_n,
        collect_date=args.collect_date,
    )
    print(
        json.dumps(
            {
                "content_count": len(records),
                "records": [
                    {
                        "record_key": record.record_key,
                        "platform": record.platform,
                        "creator_name": record.creator_name,
                        "match_author": record.match_author,
                        "title": record.title,
                        "publish_time": record.publish_time,
                        "url": record.url,
                    }
                    for record in records
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0
