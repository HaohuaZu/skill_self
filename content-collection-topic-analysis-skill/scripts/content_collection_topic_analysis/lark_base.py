from __future__ import annotations

import json
import time
from typing import Any

from .commands import CommandExecutionError, find_first_mapping_list, find_first_scalar, load_json_output, run_command
from .models import ContentRecord, TopicInsightRecord


CONTENT_FIELD_SPECS = [
    {"type": "text", "name": "record_key"},
    {
        "type": "select",
        "name": "platform",
        "multiple": False,
        "options": [
            {"name": "wechat_mp", "hue": "Green", "lightness": "Lighter"},
            {"name": "xiaohongshu", "hue": "Red", "lightness": "Lighter"},
        ],
    },
    {"type": "text", "name": "keyword"},
    {"type": "text", "name": "title"},
    {"type": "text", "name": "summary"},
    {"type": "text", "name": "author"},
    {"type": "datetime", "name": "publish_time", "style": {"format": "yyyy-MM-dd HH:mm"}},
    {"type": "text", "name": "url", "style": {"type": "url"}},
    {"type": "number", "name": "read_count", "style": {"type": "plain", "precision": 0}},
    {"type": "number", "name": "like_count", "style": {"type": "plain", "precision": 0}},
    {"type": "number", "name": "looking_count", "style": {"type": "plain", "precision": 0}},
    {"type": "number", "name": "share_count", "style": {"type": "plain", "precision": 0}},
    {"type": "number", "name": "collect_count", "style": {"type": "plain", "precision": 0}},
    {"type": "number", "name": "comment_count", "style": {"type": "plain", "precision": 0}},
    {"type": "text", "name": "raw_content"},
    {
        "type": "select",
        "name": "monitor_type",
        "multiple": False,
        "options": [
            {"name": "keyword", "hue": "Blue", "lightness": "Lighter"},
            {"name": "creator_watch", "hue": "Orange", "lightness": "Lighter"},
        ],
    },
    {"type": "text", "name": "creator_name"},
    {"type": "text", "name": "match_author"},
    {"type": "datetime", "name": "collect_date", "style": {"format": "yyyy-MM-dd"}},
]

ANALYSIS_FIELD_SPECS = [
    {"type": "text", "name": "analysis_key"},
    {
        "type": "select",
        "name": "platform",
        "multiple": False,
        "options": [
            {"name": "wechat_mp", "hue": "Green", "lightness": "Lighter"},
            {"name": "xiaohongshu", "hue": "Red", "lightness": "Lighter"},
        ],
    },
    {"type": "text", "name": "keyword"},
    {"type": "datetime", "name": "collect_date", "style": {"format": "yyyy-MM-dd"}},
    {"type": "number", "name": "sample_size", "style": {"type": "plain", "precision": 0}},
    {"type": "text", "name": "topic_direction"},
    {"type": "text", "name": "why_it_works"},
    {"type": "text", "name": "content_angle_suggestion"},
]


def _format_datetime(value: str) -> str:
    if not value:
        return ""
    return value.replace("T", " ").split("+", 1)[0].split(".", 1)[0]


class LarkBaseWriter:
    def __init__(
        self,
        *,
        lark_cli_bin: str,
        identity: str,
        base_token: str | None,
        base_name: str | None,
        folder_token: str | None,
        content_table_name: str,
        content_table_id: str | None,
        analysis_table_name: str,
        analysis_table_id: str | None,
    ) -> None:
        self._lark_cli_bin = lark_cli_bin
        self._identity = identity
        self._base_token = base_token
        self._base_name = base_name
        self._folder_token = folder_token
        self._content_table_name = content_table_name
        self._content_table_id = content_table_id
        self._analysis_table_name = analysis_table_name
        self._analysis_table_id = analysis_table_id

    def write_content_records(self, records: list[ContentRecord]) -> None:
        if not records:
            return
        base_token = self._ensure_base_token()
        table_id = self._ensure_table(
            base_token,
            self._content_table_name,
            CONTENT_FIELD_SPECS,
            preferred_table_id=self._content_table_id,
        )
        for record in records:
            payload = self._content_payload(record)
            record_id = self._find_existing_record_id(base_token, table_id, record.record_key)
            self._upsert_record(base_token, table_id, payload, record_id=record_id)

    def write_analysis_records(self, records: list[TopicInsightRecord]) -> None:
        if not records:
            return
        base_token = self._ensure_base_token()
        table_id = self._ensure_table(
            base_token,
            self._analysis_table_name,
            ANALYSIS_FIELD_SPECS,
            preferred_table_id=self._analysis_table_id,
        )
        for record in records:
            payload = self._analysis_payload(record)
            record_id = self._find_existing_record_id(base_token, table_id, record.analysis_key, key_field="analysis_key")
            self._upsert_record(base_token, table_id, payload, record_id=record_id)

    def _ensure_base_token(self) -> str:
        if self._base_token:
            return self._base_token
        command = [
            self._lark_cli_bin,
            "base",
            "+base-create",
            "--as",
            self._identity,
            "--name",
            self._base_name or "内容采集数据资产",
        ]
        if self._folder_token:
            command.extend(["--folder-token", self._folder_token])
        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        token = find_first_scalar(payload, ("base_token", "token"))
        if not token:
            raise RuntimeError("failed to determine base token from lark-cli output")
        self._base_token = token
        return token

    def _ensure_table(
        self,
        base_token: str,
        table_name: str,
        field_specs: list[dict[str, Any]],
        *,
        preferred_table_id: str | None,
    ) -> str:
        if preferred_table_id:
            self._ensure_missing_fields(base_token, preferred_table_id, field_specs)
            return preferred_table_id
        tables = self._list_tables(base_token)
        for table in tables:
            if self._extract_name(table) == table_name:
                table_id = str(table.get("id") or table.get("table_id") or table_name)
                self._ensure_missing_fields(base_token, table_id, field_specs)
                return table_id

        command = [
            self._lark_cli_bin,
            "base",
            "+table-create",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--name",
            table_name,
            "--fields",
            json.dumps(field_specs, ensure_ascii=False),
        ]
        for attempt in range(1, 8):
            try:
                result = run_command(command)
                payload = load_json_output(result.stdout, result.stderr)
                created = payload.get("data", {}).get("table", {})
                return str(created.get("id") or created.get("table_id") or table_name)
            except CommandExecutionError as exc:
                if "800004135" not in str(exc) or attempt == 7:
                    raise
                time.sleep(attempt)
        raise RuntimeError("failed to create table after retries")

    def _ensure_missing_fields(self, base_token: str, table_id: str, field_specs: list[dict[str, Any]]) -> None:
        existing_fields = {
            self._extract_name(field): field for field in self._list_fields(base_token, table_id)
        }
        for spec in field_specs:
            existing = existing_fields.get(spec["name"])
            if existing is None:
                self._create_field_with_retry(base_token, table_id, spec)
                continue
            if self._field_needs_update(existing, spec):
                self._update_field_with_retry(base_token, table_id, str(existing.get("field_id") or existing.get("id")), spec)

    def _list_tables(self, base_token: str) -> list[dict[str, Any]]:
        command = [
            self._lark_cli_bin,
            "base",
            "+table-list",
            "--as",
            self._identity,
            "--base-token",
            base_token,
        ]
        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        return find_first_mapping_list(payload, ("tables", "items", "data"))

    def _list_fields(self, base_token: str, table_name: str) -> list[dict[str, Any]]:
        command = [
            self._lark_cli_bin,
            "base",
            "+field-list",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--table-id",
            table_name,
        ]
        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        return find_first_mapping_list(payload, ("fields", "items", "data"))

    def _upsert_record(
        self,
        base_token: str,
        table_name: str,
        payload: dict[str, Any],
        *,
        record_id: str | None = None,
    ) -> None:
        command = [
            self._lark_cli_bin,
            "base",
            "+record-upsert",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--table-id",
            table_name,
            "--json",
            json.dumps(payload, ensure_ascii=False),
        ]
        if record_id:
            command.extend(["--record-id", record_id])
        run_command(command)

    def _create_field_with_retry(self, base_token: str, table_id: str, spec: dict[str, Any]) -> None:
        command = [
            self._lark_cli_bin,
            "base",
            "+field-create",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--json",
            json.dumps(spec, ensure_ascii=False),
        ]
        for attempt in range(1, 8):
            try:
                run_command(command)
                return
            except CommandExecutionError as exc:
                if "800004135" not in str(exc) or attempt == 7:
                    raise
                time.sleep(attempt)

    def _update_field_with_retry(self, base_token: str, table_id: str, field_id: str, spec: dict[str, Any]) -> None:
        command = [
            self._lark_cli_bin,
            "base",
            "+field-update",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--field-id",
            field_id,
            "--json",
            json.dumps(spec, ensure_ascii=False),
        ]
        for attempt in range(1, 8):
            try:
                run_command(command)
                return
            except CommandExecutionError as exc:
                if "800004135" not in str(exc) or attempt == 7:
                    raise
                time.sleep(attempt)

    @staticmethod
    def _field_needs_update(existing: dict[str, Any], spec: dict[str, Any]) -> bool:
        if existing.get("type") != spec.get("type"):
            return True
        if spec["name"] == "platform":
            return existing.get("type") != "select"
        if spec["name"] == "monitor_type":
            return existing.get("type") != "select"
        if spec["name"] == "collect_date":
            return existing.get("type") != "datetime"
        return False

    def _find_existing_record_id(
        self,
        base_token: str,
        table_id: str,
        record_key: str,
        *,
        key_field: str = "record_key",
    ) -> str | None:
        records = self._list_records(base_token, table_id)
        fields = records.get("fields", [])
        rows = records.get("data", [])
        record_ids = records.get("record_id_list", [])
        if key_field not in fields:
            return None
        index = fields.index(key_field)
        for position, row in enumerate(rows):
            if index >= len(row):
                continue
            if row[index] == record_key:
                return record_ids[position] if position < len(record_ids) else None
        return None

    def _list_records(self, base_token: str, table_id: str) -> dict[str, Any]:
        command = [
            self._lark_cli_bin,
            "base",
            "+record-list",
            "--as",
            self._identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            "200",
        ]
        result = run_command(command)
        payload = load_json_output(result.stdout, result.stderr)
        return payload.get("data", {})

    @staticmethod
    def _extract_name(payload: dict[str, Any]) -> str:
        return str(payload.get("name") or payload.get("table_name") or payload.get("field_name") or "")

    @staticmethod
    def _content_payload(record: ContentRecord) -> dict[str, Any]:
        return {
            "record_key": record.record_key,
            "platform": record.platform,
            "keyword": record.keyword,
            "title": record.title,
            "summary": record.summary,
            "author": record.author,
            "publish_time": _format_datetime(record.publish_time),
            "url": record.url,
            "read_count": record.read_count,
            "like_count": record.like_count,
            "looking_count": record.looking_count,
            "share_count": record.share_count,
            "collect_count": record.collect_count,
            "comment_count": record.comment_count,
            "raw_content": record.raw_content,
            "monitor_type": record.monitor_type,
            "creator_name": record.creator_name,
            "match_author": record.match_author,
            "collect_date": record.collect_date,
        }

    @staticmethod
    def _analysis_payload(record: TopicInsightRecord) -> dict[str, Any]:
        return {
            "analysis_key": record.analysis_key,
            "platform": record.platform,
            "keyword": record.keyword,
            "collect_date": record.collect_date,
            "sample_size": record.sample_size,
            "topic_direction": record.topic_direction,
            "why_it_works": record.why_it_works,
            "content_angle_suggestion": record.content_angle_suggestion,
        }


class StdoutWriter:
    def write_content_records(self, records: list[ContentRecord]) -> None:
        self.content_records = records

    def write_analysis_records(self, records: list[TopicInsightRecord]) -> None:
        self.analysis_records = records
