from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any
from urllib import request as urllib_request

from .commands import IntegrationConfigError
from .models import ContentRecord, TopicInsightRecord


def _extract_json_block(payload: str) -> dict[str, Any]:
    text = payload.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("analysis payload must be a JSON object")
    return data


def parse_analysis_response(
    keyword: str,
    platform: str,
    collect_date: str,
    sample_size: int,
    payload: str,
) -> TopicInsightRecord:
    data = _extract_json_block(payload)
    return TopicInsightRecord(
        platform=platform,
        keyword=keyword,
        collect_date=collect_date,
        sample_size=sample_size,
        topic_direction=str(data.get("topic_direction") or "").strip(),
        why_it_works=str(data.get("why_it_works") or "").strip(),
        content_angle_suggestion=str(data.get("content_angle_suggestion") or "").strip(),
    )


def build_analysis_prompt(records: list[ContentRecord]) -> str:
    lines = []
    for index, record in enumerate(records, start=1):
        lines.append(
            (
                f"{index}. title={record.title}; author={record.author}; "
                f"read={record.read_count}; like={record.like_count}; "
                f"comment={record.comment_count}; summary={record.summary}"
            )
        )
    return (
        "你是一个内容选题分析器。请基于输入内容，只输出 JSON 对象，字段固定为 "
        "topic_direction、why_it_works、content_angle_suggestion。\n"
        + "\n".join(lines)
    )


@dataclass(frozen=True)
class OpenAIAnalyzerConfig:
    base_url: str
    api_key: str
    model: str


class OpenAICompatibleAnalyzer:
    def __init__(self, config: OpenAIAnalyzerConfig) -> None:
        self._config = config

    def analyze(self, records: list[ContentRecord]) -> TopicInsightRecord:
        if not records:
            raise ValueError("records must not be empty")

        prompt = build_analysis_prompt(records)
        url = self._config.base_url.rstrip("/") + "/chat/completions"
        body = {
            "model": self._config.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "你输出结构化 JSON，不要输出解释性文字。",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }
        req = urllib_request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        message = payload["choices"][0]["message"]["content"]
        return parse_analysis_response(
            keyword=records[0].keyword,
            platform=records[0].platform,
            collect_date=records[0].collect_date,
            sample_size=len(records),
            payload=message,
        )


class BuiltinAnalyzer:
    def analyze(self, records: list[ContentRecord]) -> TopicInsightRecord:
        if not records:
            raise ValueError("records must not be empty")

        titles = " ".join(record.title for record in records)
        summaries = " ".join(record.summary for record in records if record.summary)
        corpus = f"{titles} {summaries}"

        theme_tags: list[str] = []
        if any(token in corpus for token in ("源码", "架构", "泄露", "拆解")):
            theme_tags.append("热点事件拆解")
        if any(token in corpus for token in ("命令", "教程", "攻略", "上手", "工作流")):
            theme_tags.append("实操教程")
        if any(token in corpus for token in ("宠物", "焦虑", "金皮", "隐藏功能", "新功能")):
            theme_tags.append("情绪化新鲜感")
        if not theme_tags:
            theme_tags.append("关键词趋势内容")

        avg_read = int(sum(record.read_count for record in records) / len(records))
        avg_like = int(sum(record.like_count for record in records) / len(records))
        avg_comment = int(sum(record.comment_count for record in records) / len(records))

        topic_direction = (
            f"{records[0].keyword} 的"
            + " + ".join(theme_tags[:3])
            + "选题"
        )
        why_it_works = (
            f"这一批内容同时踩中了事件热度、可复用信息和情绪钩子。"
            f"样本平均阅读/曝光约 {avg_read}，平均点赞 {avg_like}，平均评论 {avg_comment}。"
            "高表现标题普遍把“源码泄露/架构拆解/上手命令”说得很具体，让用户能快速判断价值。"
        )
        content_angle_suggestion = (
            "优先延展 3 个方向："
            "1) 源码或产品变化背后的工作流影响；"
            "2) 新手可以直接照抄的命令/配置/案例；"
            "3) 带有争议、反差或彩蛋感的细节拆解。"
        )

        return TopicInsightRecord(
            platform=records[0].platform,
            keyword=records[0].keyword,
            collect_date=records[0].collect_date,
            sample_size=len(records),
            topic_direction=topic_direction,
            why_it_works=why_it_works,
            content_angle_suggestion=content_angle_suggestion,
        )


def build_analyzer(
    provider: str,
    base_url: str | None,
    api_key: str | None,
    model: str | None,
) -> OpenAICompatibleAnalyzer | BuiltinAnalyzer | None:
    if provider == "openai":
        if not base_url or not api_key or not model:
            raise IntegrationConfigError("analysis requires OPENAI_BASE_URL, OPENAI_API_KEY, and OPENAI_MODEL")
        return OpenAICompatibleAnalyzer(
            OpenAIAnalyzerConfig(base_url=base_url, api_key=api_key, model=model)
        )
    if provider == "builtin":
        return BuiltinAnalyzer()
    if not base_url and not api_key and not model:
        return None
    raise IntegrationConfigError(f"unsupported ANALYSIS_PROVIDER: {provider}")
