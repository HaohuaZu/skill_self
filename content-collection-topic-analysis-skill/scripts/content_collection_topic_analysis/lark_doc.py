from __future__ import annotations

from .commands import find_first_scalar, load_json_output, run_command
from .creation_models import DocumentWriteResult, WechatArticleDraft


class LarkDocWriter:
    def __init__(
        self,
        *,
        lark_cli_bin: str,
        identity: str,
        folder_token: str | None = None,
    ) -> None:
        self._lark_cli_bin = lark_cli_bin
        self._identity = identity
        self._folder_token = folder_token

    def write_article(self, draft: WechatArticleDraft) -> DocumentWriteResult:
        command = [
            self._lark_cli_bin,
            "docs",
            "+create",
            "--as",
            self._identity,
            "--title",
            draft.document_title,
            "--markdown",
            draft.markdown,
        ]
        if self._folder_token:
            command.extend(["--folder-token", self._folder_token])

        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        return DocumentWriteResult(
            doc_token=find_first_scalar(payload, ("document_id", "doc_token", "token")),
            url=find_first_scalar(payload, ("url", "doc_url")),
            title=draft.document_title,
        )


class StdoutDocWriter:
    def write_article(self, draft: WechatArticleDraft) -> DocumentWriteResult:
        return DocumentWriteResult(doc_token=None, url=None, title=draft.document_title)
