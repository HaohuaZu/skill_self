from __future__ import annotations

import argparse
import json
import re
from typing import Sequence

from .commands import IntegrationConfigError
from .config import SkillConfig
from .feishu_doc import FeishuDocFetcher
from .wechat_formatting import (
    extract_markdown_image_urls,
    render_bauhaus_html,
    replace_feishu_image_tokens,
    replace_image_urls,
)
from .wechat_publish import WechatArticleDraftInput, WechatPublisher, require_cover_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a Feishu doc, render it with Bauhaus styling, upload images to WeChat, and create a WeChat draft.",
    )
    parser.add_argument("--doc", required=True, help="Feishu doc URL or token")
    parser.add_argument("--theme", default="bauhaus", choices=["bauhaus"], help="publishing theme")
    parser.add_argument("--title", help="override article title")
    parser.add_argument("--author", help="override article author")
    parser.add_argument("--digest", help="override article digest")
    parser.add_argument("--cover-image", help="explicit cover image URL or local path")
    parser.add_argument("--content-source-url", help="override content source url")
    parser.add_argument("--appid", help="override WECHAT_APP_ID")
    parser.add_argument("--appsecret", help="override WECHAT_APP_SECRET")
    parser.add_argument("--dry-run", action="store_true", help="render and print payload preview instead of creating a WeChat draft")
    return parser


def _normalize_article_title(title: str) -> str:
    text = title.strip()
    if text.startswith("《") and text.endswith("》"):
        text = text[1:-1]
    text = text.split("｜", 1)[0].strip()
    return text


def _build_digest(markdown: str, limit: int = 120) -> str:
    text = re.sub(r"!\[[^\]]*]\(([^)]+)\)", "", markdown)
    text = re.sub(r"<img[^>]*>", "", text)
    text = re.sub(r"<image[^>]*\/>", "", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def run_from_args(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SkillConfig.from_env()
    app_id = args.appid or config.wechat_app_id
    app_secret = args.appsecret or config.wechat_app_secret
    if not args.dry_run and (not app_id or not app_secret):
        raise IntegrationConfigError("wechat publishing requires WECHAT_APP_ID and WECHAT_APP_SECRET")

    fetcher = FeishuDocFetcher(
        lark_cli_bin=config.lark_cli_bin,
        identity=config.lark_identity,
    )
    fetched = fetcher.fetch(args.doc)
    title = args.title or _normalize_article_title(fetched.title)
    author = args.author or config.wechat_author or ""
    digest = args.digest or _build_digest(fetched.markdown)
    content_source_url = args.content_source_url or config.wechat_content_source_url or ""

    temp_dir = ".wechat-publish-media"
    image_token_map = {
        token: fetcher.download_media(token, temp_dir)
        for token in fetcher.extract_image_tokens(fetched.markdown)
    }
    normalized_markdown = replace_feishu_image_tokens(fetched.markdown, image_token_map)
    image_urls = extract_markdown_image_urls(normalized_markdown)
    rendered_html = render_bauhaus_html(normalized_markdown)
    cover_image = require_cover_image(args.cover_image or config.wechat_cover_image, image_urls)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "doc_token": fetched.doc_token,
                    "title": title,
                    "author": author,
                    "digest": digest,
                    "image_urls": image_urls,
                    "cover_image": cover_image,
                    "html": rendered_html,
                },
                ensure_ascii=False,
            )
        )
        return 0

    publisher = WechatPublisher(app_id=app_id or "", app_secret=app_secret or "")
    uploaded_image_map = {url: publisher.upload_article_image(url) for url in image_urls}
    final_html = replace_image_urls(rendered_html, uploaded_image_map)
    thumb_media_id = publisher.upload_cover_image(cover_image)
    result = publisher.create_draft(
        WechatArticleDraftInput(
            title=title,
            author=author,
            digest=digest,
            content=final_html,
            content_source_url=content_source_url,
            thumb_media_id=thumb_media_id,
        )
    )
    print(
        json.dumps(
            {
                "doc_token": fetched.doc_token,
                "title": title,
                "thumb_media_id": thumb_media_id,
                "uploaded_images": uploaded_image_map,
                "result": result,
            },
            ensure_ascii=False,
        )
    )
    return 0
