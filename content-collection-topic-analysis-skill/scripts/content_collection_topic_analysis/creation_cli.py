from __future__ import annotations

import argparse
import json
from typing import Sequence

from .config import SkillConfig
from .creation_models import CreationBrief
from .lark_doc import LarkDocWriter, StdoutDocWriter
from .wechat_article_creator import BuiltinWechatArticleCreator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a publish-ready WeChat article from a structured brief and write it to Lark Docs.",
    )
    parser.add_argument("--topic-title", required=True, help="validated topic title")
    parser.add_argument("--audience", required=True, help="target audience")
    parser.add_argument("--pain-point", action="append", default=[], help="core pain point; repeatable")
    parser.add_argument("--content-goal", required=True, help="content goal")
    parser.add_argument("--core-claim", required=True, help="core article claim")
    parser.add_argument("--supporting-point", action="append", default=[], help="supporting point; repeatable")
    parser.add_argument("--source-material", action="append", default=[], help="source material or reference; repeatable")
    parser.add_argument("--brand-tone", default="", help="brand tone for the article")
    parser.add_argument("--cta", default="", help="closing call to action")
    parser.add_argument("--dry-run", action="store_true", help="print markdown JSON instead of writing to Lark Docs")
    parser.add_argument("--doc-folder-token", help="override LARK_DOC_FOLDER_TOKEN")
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
    if args.doc_folder_token:
        config = config.__class__(**{**config.__dict__, "lark_doc_folder_token": args.doc_folder_token})

    brief = CreationBrief(
        topic_title=args.topic_title.strip(),
        audience=args.audience.strip(),
        pain_points=_flatten(args.pain_point),
        content_goal=args.content_goal.strip(),
        core_claim=args.core_claim.strip(),
        supporting_points=_flatten(args.supporting_point),
        source_materials=_flatten(args.source_material),
        brand_tone=args.brand_tone.strip(),
        cta=args.cta.strip(),
    )

    draft = BuiltinWechatArticleCreator().create(brief)
    writer = (
        StdoutDocWriter()
        if args.dry_run
        else LarkDocWriter(
            lark_cli_bin=config.lark_cli_bin,
            identity=config.lark_identity,
            folder_token=config.lark_doc_folder_token,
        )
    )
    result = writer.write_article(draft)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "title": draft.document_title,
                    "article_title": draft.article_title,
                    "markdown": draft.markdown,
                    "doc_token": result.doc_token,
                    "url": result.url,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(
            json.dumps(
                {
                    "title": result.title,
                    "doc_token": result.doc_token,
                    "url": result.url,
                },
                ensure_ascii=False,
            )
        )
    return 0
