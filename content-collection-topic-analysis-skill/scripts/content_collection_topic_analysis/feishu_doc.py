from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

from .commands import load_json_output, run_command


DOC_URL_PATTERN = re.compile(r"/docx/([A-Za-z0-9]+)")
IMAGE_TOKEN_PATTERN = re.compile(r'<image\s+token="([^"]+)"[^/]*/>')


@dataclass(frozen=True)
class FeishuDocument:
    doc_token: str
    title: str
    markdown: str


def extract_doc_token(value: str) -> str:
    match = DOC_URL_PATTERN.search(value)
    if match:
        return match.group(1)
    return value.strip()


class FeishuDocFetcher:
    def __init__(self, *, lark_cli_bin: str, identity: str) -> None:
        self._lark_cli_bin = lark_cli_bin
        self._identity = identity

    def fetch(self, doc: str) -> FeishuDocument:
        token = extract_doc_token(doc)
        result = run_command(
            [
                self._lark_cli_bin,
                "docs",
                "+fetch",
                "--as",
                self._identity,
                "--doc",
                token,
                "--format",
                "json",
            ]
        )
        payload = load_json_output(result.stdout, result.stderr)
        data = payload.get("data", {})
        return FeishuDocument(
            doc_token=str(data.get("doc_id") or token),
            title=str(data.get("title") or ""),
            markdown=str(data.get("markdown") or ""),
        )

    def extract_image_tokens(self, markdown: str) -> list[str]:
        seen: list[str] = []
        for token in IMAGE_TOKEN_PATTERN.findall(markdown):
            if token not in seen:
                seen.append(token)
        return seen

    def download_media(self, token: str, output_dir: str | None = None) -> str:
        base_dir = Path(output_dir) if output_dir else Path(".wechat-publish-media")
        base_dir.mkdir(parents=True, exist_ok=True)
        output_path = base_dir / token
        run_command(
            [
                self._lark_cli_bin,
                "docs",
                "+media-download",
                "--as",
                self._identity,
                "--token",
                token,
                "--output",
                str(output_path),
                "--overwrite",
            ]
        )
        matches = sorted(output_path.parent.glob(f"{token}*"))
        if not matches:
            raise RuntimeError(f"failed to download feishu media for token: {token}")
        return str(matches[0])
