from __future__ import annotations

from .adapters.wechat_mp import WechatMPAdapter
from .adapters.xiaohongshu import XiaohongshuAdapter
from .models import ContentRecord, PipelineRequest


class CollectorHub:
    def __init__(
        self,
        *,
        opencli_bin: str,
        wechat_api_url: str | None,
        wechat_api_key: str | None,
        wechat_metrics_api_url: str | None,
    ) -> None:
        self._adapters = {
            "xiaohongshu": XiaohongshuAdapter(opencli_bin=opencli_bin),
            "wechat_mp": WechatMPAdapter(
                api_url=wechat_api_url,
                api_key=wechat_api_key,
                metrics_api_url=wechat_metrics_api_url,
            ),
        }

    def collect(self, request: PipelineRequest, platform: str) -> list[ContentRecord]:
        adapter = self._adapters[platform]
        collected: list[ContentRecord] = []
        for keyword in request.keywords:
            collected.extend(
                adapter.collect(
                    keyword=keyword,
                    days=request.days,
                    top_n=request.top_n,
                    sort_by=request.sort_by,
                    collect_date=request.collect_date,
                )
            )
        return collected
