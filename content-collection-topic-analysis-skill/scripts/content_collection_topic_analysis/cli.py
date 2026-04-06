from __future__ import annotations

import argparse
from datetime import date
import json
from typing import Sequence

from .analyzer import build_analyzer
from .collector import CollectorHub
from .config import SkillConfig
from .lark_base import LarkBaseWriter, StdoutWriter
from .models import PipelineRequest
from .pipeline import PipelineRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect content from WeChat MP and Xiaohongshu, then write to Lark Base.",
    )
    parser.add_argument("--keyword", action="append", required=True, help="keyword to collect; repeatable")
    parser.add_argument(
        "--platform",
        action="append",
        required=True,
        choices=["wechat_mp", "xiaohongshu"],
        help="platform to collect; repeatable",
    )
    parser.add_argument("--days", type=int, default=1, help="collect recent N days")
    parser.add_argument("--top-n", type=int, default=10, help="top N items per platform and keyword")
    parser.add_argument(
        "--sort-by",
        choices=["engagement", "read", "like", "comment", "publish_time"],
        default="engagement",
        help="sorting strategy before taking Top N",
    )
    parser.add_argument("--with-analysis", action="store_true", help="run structured topic analysis")
    parser.add_argument("--dry-run", action="store_true", help="collect and print JSON instead of writing to Lark")
    parser.add_argument("--collect-date", default=date.today().isoformat(), help="logical collect date, YYYY-MM-DD")
    parser.add_argument("--base-token", help="override LARK_BASE_TOKEN")
    parser.add_argument("--base-name", help="override LARK_BASE_NAME")
    parser.add_argument("--content-table", help="override content table name")
    parser.add_argument("--content-table-id", help="override LARK_CONTENT_TABLE_ID")
    parser.add_argument("--analysis-table", help="override analysis table name")
    parser.add_argument("--analysis-table-id", help="override LARK_ANALYSIS_TABLE_ID")
    return parser


def _flatten(values: Sequence[str]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        flattened.extend([item.strip() for item in value.split(",") if item.strip()])
    return flattened


def run_from_args(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SkillConfig.from_env()
    if args.base_token:
        config = config.__class__(**{**config.__dict__, "lark_base_token": args.base_token})
    if args.base_name:
        config = config.__class__(**{**config.__dict__, "lark_base_name": args.base_name})
    if args.content_table:
        config = config.__class__(**{**config.__dict__, "content_table_name": args.content_table})
    if args.content_table_id:
        config = config.__class__(**{**config.__dict__, "content_table_id": args.content_table_id})
    if args.analysis_table:
        config = config.__class__(**{**config.__dict__, "analysis_table_name": args.analysis_table})
    if args.analysis_table_id:
        config = config.__class__(**{**config.__dict__, "analysis_table_id": args.analysis_table_id})

    keywords = _flatten(args.keyword)
    platforms = _flatten(args.platform)
    config.validate(platforms=platforms, with_analysis=args.with_analysis)

    request = PipelineRequest(
        keywords=keywords,
        platforms=platforms,
        days=args.days,
        top_n=args.top_n,
        sort_by=args.sort_by,
        with_analysis=args.with_analysis,
        collect_date=args.collect_date,
        dry_run=args.dry_run,
    )

    collector = CollectorHub(
        opencli_bin=config.opencli_bin,
        wechat_api_url=config.wechat_api_url,
        wechat_api_key=config.wechat_api_key,
        wechat_metrics_api_url=config.wechat_metrics_api_url,
    )
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
    analyzer = build_analyzer(
        provider=config.analysis_provider,
        base_url=config.openai_base_url,
        api_key=config.openai_api_key,
        model=config.openai_model,
    )

    runner = PipelineRunner(collector=collector, writer=writer, analyzer=analyzer)
    result = runner.run(request)
    print(
        json.dumps(
            {
                "content_count": result.content_count,
                "analysis_count": result.analysis_count,
                "records": [
                    {
                        "record_key": record.record_key,
                        "platform": record.platform,
                        "keyword": record.keyword,
                        "title": record.title,
                        "publish_time": record.publish_time,
                        "url": record.url,
                    }
                    for record in result.records
                ],
                "analyses": [
                    {
                        "analysis_key": record.analysis_key,
                        "platform": record.platform,
                        "keyword": record.keyword,
                        "topic_direction": record.topic_direction,
                    }
                    for record in result.analyses
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0
