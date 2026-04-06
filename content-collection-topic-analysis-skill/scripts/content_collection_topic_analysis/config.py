from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable

from .commands import IntegrationConfigError


@dataclass(frozen=True)
class SkillConfig:
    opencli_bin: str
    lark_cli_bin: str
    lark_identity: str
    analysis_provider: str
    lark_base_token: str | None
    lark_base_name: str | None
    lark_folder_token: str | None
    content_table_name: str
    content_table_id: str | None
    analysis_table_name: str
    analysis_table_id: str | None
    lark_doc_folder_token: str | None
    wechat_app_id: str | None
    wechat_app_secret: str | None
    wechat_author: str | None
    wechat_content_source_url: str | None
    wechat_cover_image: str | None
    wechat_api_url: str | None
    wechat_api_key: str | None
    wechat_metrics_api_url: str | None
    creator_watchlist_path: str | None
    openai_base_url: str | None
    openai_api_key: str | None
    openai_model: str | None

    @property
    def cn8n_api_url(self) -> str | None:
        return self.wechat_api_url

    @property
    def cn8n_api_key(self) -> str | None:
        return self.wechat_api_key

    @classmethod
    def from_env(cls) -> "SkillConfig":
        return cls(
            opencli_bin=os.getenv("OPENCLI_BIN", "opencli"),
            lark_cli_bin=os.getenv("LARK_CLI_BIN", "lark-cli"),
            lark_identity=os.getenv("LARK_IDENTITY", "user"),
            analysis_provider=os.getenv("ANALYSIS_PROVIDER", "builtin"),
            lark_base_token=os.getenv("LARK_BASE_TOKEN"),
            lark_base_name=os.getenv("LARK_BASE_NAME", "内容采集数据资产"),
            lark_folder_token=os.getenv("LARK_FOLDER_TOKEN"),
            content_table_name=os.getenv("LARK_CONTENT_TABLE", "content_items"),
            content_table_id=os.getenv("LARK_CONTENT_TABLE_ID"),
            analysis_table_name=os.getenv("LARK_ANALYSIS_TABLE", "topic_insights"),
            analysis_table_id=os.getenv("LARK_ANALYSIS_TABLE_ID"),
            lark_doc_folder_token=os.getenv("LARK_DOC_FOLDER_TOKEN", os.getenv("LARK_FOLDER_TOKEN")),
            wechat_app_id=os.getenv("WECHAT_APP_ID"),
            wechat_app_secret=os.getenv("WECHAT_APP_SECRET"),
            wechat_author=os.getenv("WECHAT_AUTHOR"),
            wechat_content_source_url=os.getenv("WECHAT_CONTENT_SOURCE_URL", ""),
            wechat_cover_image=os.getenv("WECHAT_COVER_IMAGE"),
            wechat_api_url=os.getenv(
                "WECHAT_API_URL",
                os.getenv("DAJIALA_SEARCH_API_URL", "https://www.dajiala.com/fbmain/monitor/v3/kw_search"),
            ),
            wechat_api_key=os.getenv(
                "WECHAT_API_KEY",
                os.getenv("DAJIALA_API_KEY", os.getenv("CN8N_API_KEY")),
            ),
            wechat_metrics_api_url=os.getenv(
                "WECHAT_METRICS_API_URL",
                os.getenv("DAJIALA_METRICS_API_URL", "https://www.dajiala.com/fbmain/monitor/v3/read_zan_pro"),
            ),
            creator_watchlist_path=os.getenv("CREATOR_WATCHLIST_PATH"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL"),
        )

    def validate(self, platforms: Iterable[str], with_analysis: bool) -> None:
        selected = set(platforms)
        if "wechat_mp" in selected and not self.wechat_api_key:
            raise IntegrationConfigError("wechat_mp requires WECHAT_API_KEY or DAJIALA_API_KEY")
        if not self.lark_base_token and not self.lark_base_name:
            raise IntegrationConfigError("either LARK_BASE_TOKEN or LARK_BASE_NAME is required")
        if with_analysis and self.analysis_provider == "openai":
            missing = [
                key
                for key, value in (
                    ("OPENAI_BASE_URL", self.openai_base_url),
                    ("OPENAI_API_KEY", self.openai_api_key),
                    ("OPENAI_MODEL", self.openai_model),
                )
                if not value
            ]
            if missing:
                raise IntegrationConfigError("analysis requires " + ", ".join(missing))
