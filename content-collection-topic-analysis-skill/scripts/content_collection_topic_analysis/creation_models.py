from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CreationBrief:
    topic_title: str
    audience: str
    pain_points: list[str]
    content_goal: str
    core_claim: str
    supporting_points: list[str]
    source_materials: list[str] = field(default_factory=list)
    brand_tone: str = ""
    cta: str = ""


@dataclass(frozen=True)
class WechatArticleDraft:
    document_title: str
    article_title: str
    markdown: str


@dataclass(frozen=True)
class DocumentWriteResult:
    doc_token: str | None
    url: str | None
    title: str
