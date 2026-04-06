from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from .models import ContentRecord, PipelineRequest, PipelineResult, TopicInsightRecord


class CollectorProtocol(Protocol):
    def collect(self, request: PipelineRequest, platform: str) -> list[ContentRecord]:
        ...


class WriterProtocol(Protocol):
    def write_content_records(self, records: list[ContentRecord]) -> None:
        ...

    def write_analysis_records(self, records: list[TopicInsightRecord]) -> None:
        ...


class AnalyzerProtocol(Protocol):
    def analyze(self, records: list[ContentRecord]) -> TopicInsightRecord:
        ...


def deduplicate_records(records: list[ContentRecord]) -> list[ContentRecord]:
    seen: set[str] = set()
    unique: list[ContentRecord] = []
    for record in records:
        if record.record_key in seen:
            continue
        seen.add(record.record_key)
        unique.append(record)
    return unique


class PipelineRunner:
    def __init__(
        self,
        collector: CollectorProtocol,
        writer: WriterProtocol,
        analyzer: AnalyzerProtocol | None = None,
    ) -> None:
        self._collector = collector
        self._writer = writer
        self._analyzer = analyzer

    def run(self, request: PipelineRequest) -> PipelineResult:
        collected: list[ContentRecord] = []
        for platform in request.platforms:
            collected.extend(self._collector.collect(request, platform))

        unique_records = deduplicate_records(collected)
        self._writer.write_content_records(unique_records)

        analyses: list[TopicInsightRecord] = []
        if request.with_analysis and self._analyzer is not None:
            grouped: dict[tuple[str, str], list[ContentRecord]] = defaultdict(list)
            for record in unique_records:
                grouped[(record.platform, record.keyword)].append(record)
            for records in grouped.values():
                analyses.append(self._analyzer.analyze(records))
            self._writer.write_analysis_records(analyses)

        return PipelineResult(
            content_count=len(unique_records),
            analysis_count=len(analyses),
            records=unique_records,
            analyses=analyses,
        )

