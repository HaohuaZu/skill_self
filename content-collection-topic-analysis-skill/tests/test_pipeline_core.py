from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class CliTests(unittest.TestCase):
    def test_help_lists_core_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_pipeline.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--keyword", result.stdout)
        self.assertIn("--platform", result.stdout)
        self.assertIn("--days", result.stdout)
        self.assertIn("--top-n", result.stdout)
        self.assertIn("--with-analysis", result.stdout)
        self.assertIn("--dry-run", result.stdout)

    def test_help_lists_creator_watch_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_creator_watch.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--watchlist", result.stdout)
        self.assertIn("--days", result.stdout)
        self.assertIn("--top-n", result.stdout)
        self.assertIn("--collect-date", result.stdout)


class PipelineCoreTests(unittest.TestCase):
    def test_normalize_xiaohongshu_item(self) -> None:
        from content_collection_topic_analysis.normalize import normalize_xiaohongshu_item

        record = normalize_xiaohongshu_item(
            keyword="直播带货",
            raw_item={
                "title": "直播带货复盘模板",
                "author": "内容实验室",
                "likes": "123",
                "comments": 18,
                "published_at": "2026-04-04T10:00:00+08:00",
                "url": "https://www.xiaohongshu.com/explore/1",
                "summary": "一套直播复盘拆解框架",
            },
            collect_date="2026-04-05",
        )

        self.assertEqual(record.platform, "xiaohongshu")
        self.assertEqual(record.keyword, "直播带货")
        self.assertEqual(record.title, "直播带货复盘模板")
        self.assertEqual(record.like_count, 123)
        self.assertEqual(record.comment_count, 18)
        self.assertEqual(record.read_count, 0)
        self.assertEqual(record.collect_date, "2026-04-05")

    def test_normalize_wechat_mp_item_from_cn8n_shape(self) -> None:
        from content_collection_topic_analysis.normalize import normalize_wechat_mp_item

        record = normalize_wechat_mp_item(
            keyword="claude code",
            raw_item={
                "title": "盘一下Claude Code源码里的8个隐藏新功能。",
                "content": "今天的乐子事大家都知道了。",
                "wx_name": "数字生命卡兹克",
                "publish_time": 1774965068,
                "publish_time_str": "2026-03-31 21:51:08",
                "url": "https://mp.weixin.qq.com/s/example",
                "read": 80999,
                "praise": 1617,
                "looking": 591,
            },
            collect_date="2026-04-05",
        )

        self.assertEqual(record.platform, "wechat_mp")
        self.assertEqual(record.keyword, "claude code")
        self.assertEqual(record.author, "数字生命卡兹克")
        self.assertEqual(record.read_count, 80999)
        self.assertEqual(record.like_count, 1617)
        self.assertEqual(record.comment_count, 591)
        self.assertEqual(record.publish_time, "2026-03-31T21:51:08")

    def test_build_wechat_cn8n_payload(self) -> None:
        from content_collection_topic_analysis.adapters.wechat_mp import build_cn8n_payload

        payload = build_cn8n_payload(keyword="claude code", days=7, page=1)

        self.assertEqual(
            payload,
            {
                "kw": "claude code",
                "sort_type": 1,
                "mode": 1,
                "period": 7,
                "page": 1,
                "any_kw": "",
                "ex_kw": "",
                "verifycode": "",
                "type": 1,
            },
        )

    def test_calculate_wechat_fetch_pages(self) -> None:
        from content_collection_topic_analysis.adapters.wechat_mp import calculate_fetch_pages

        self.assertEqual(calculate_fetch_pages(top_n=5, page_size=20, max_pages=10), 1)
        self.assertEqual(calculate_fetch_pages(top_n=25, page_size=20, max_pages=10), 2)
        self.assertEqual(calculate_fetch_pages(top_n=250, page_size=20, max_pages=3), 3)

    def test_content_field_specs_use_select_and_datetime_where_needed(self) -> None:
        from content_collection_topic_analysis.lark_base import ANALYSIS_FIELD_SPECS, CONTENT_FIELD_SPECS

        content_spec_by_name = {item["name"]: item for item in CONTENT_FIELD_SPECS}
        analysis_spec_by_name = {item["name"]: item for item in ANALYSIS_FIELD_SPECS}

        self.assertEqual(content_spec_by_name["platform"]["type"], "select")
        self.assertEqual(content_spec_by_name["collect_date"]["type"], "datetime")
        self.assertEqual(content_spec_by_name["monitor_type"]["type"], "select")
        self.assertEqual(content_spec_by_name["creator_name"]["type"], "text")
        self.assertEqual(content_spec_by_name["match_author"]["type"], "text")
        self.assertEqual(analysis_spec_by_name["platform"]["type"], "select")
        self.assertEqual(analysis_spec_by_name["collect_date"]["type"], "datetime")

    def test_deduplicate_records_by_stable_key(self) -> None:
        from content_collection_topic_analysis.models import ContentRecord
        from content_collection_topic_analysis.pipeline import deduplicate_records

        first = ContentRecord(
            platform="xiaohongshu",
            keyword="AI",
            title="A",
            summary="",
            author="alice",
            publish_time="2026-04-05T08:00:00+08:00",
            url="https://example.com/1",
            read_count=0,
            like_count=10,
            comment_count=1,
            raw_content="",
            collect_date="2026-04-05",
        )
        duplicate = replace(first, like_count=999)

        records = deduplicate_records([first, duplicate])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].like_count, 10)

    def test_deduplicate_records_ignores_keyword_when_url_matches(self) -> None:
        from content_collection_topic_analysis.models import ContentRecord
        from content_collection_topic_analysis.pipeline import deduplicate_records

        first = ContentRecord(
            platform="wechat_mp",
            keyword="A",
            title="同一篇文章",
            summary="",
            author="数字生命卡兹克",
            publish_time="2026-04-05T09:00:00+08:00",
            url="https://example.com/1",
            read_count=0,
            like_count=10,
            comment_count=1,
            raw_content="",
            collect_date="2026-04-05",
        )
        duplicate = replace(first, keyword="B", like_count=999)

        records = deduplicate_records([first, duplicate])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].keyword, "A")

    def test_parse_topic_analysis_response(self) -> None:
        from content_collection_topic_analysis.analyzer import parse_analysis_response

        analysis = parse_analysis_response(
            keyword="直播带货",
            platform="wechat_mp",
            collect_date="2026-04-05",
            sample_size=8,
            payload=json.dumps(
                {
                    "topic_direction": "直播复盘方法论",
                    "why_it_works": "结果导向强，用户能直接套用。",
                    "content_angle_suggestion": "加入失败案例和模板拆解。",
                }
            ),
        )

        self.assertEqual(analysis.platform, "wechat_mp")
        self.assertEqual(analysis.keyword, "直播带货")
        self.assertEqual(analysis.sample_size, 8)
        self.assertEqual(analysis.topic_direction, "直播复盘方法论")

    def test_builtin_analyzer_generates_structured_analysis(self) -> None:
        from content_collection_topic_analysis.analyzer import BuiltinAnalyzer
        from content_collection_topic_analysis.models import ContentRecord

        analyzer = BuiltinAnalyzer()
        result = analyzer.analyze(
            [
                ContentRecord(
                    platform="wechat_mp",
                    keyword="claude code",
                    title="Claude Code源码泄露后，大家都在拆架构",
                    summary="围绕源码泄露、架构拆解和未发布功能做深度解读。",
                    author="作者A",
                    publish_time="2026-04-01T10:00:00",
                    url="https://example.com/1",
                    read_count=1000,
                    like_count=120,
                    comment_count=30,
                    raw_content="",
                    collect_date="2026-04-05",
                ),
                ContentRecord(
                    platform="wechat_mp",
                    keyword="claude code",
                    title="Claude Code上手命令与工作流",
                    summary="整理命令、教程和效率提升技巧。",
                    author="作者B",
                    publish_time="2026-04-02T10:00:00",
                    url="https://example.com/2",
                    read_count=800,
                    like_count=100,
                    comment_count=20,
                    raw_content="",
                    collect_date="2026-04-05",
                ),
            ]
        )

        self.assertEqual(result.platform, "wechat_mp")
        self.assertEqual(result.keyword, "claude code")
        self.assertEqual(result.sample_size, 2)
        self.assertTrue(result.topic_direction)
        self.assertTrue(result.why_it_works)
        self.assertTrue(result.content_angle_suggestion)

    def test_should_keep_record_handles_timezone_mismatch(self) -> None:
        from content_collection_topic_analysis.normalize import should_keep_record

        self.assertTrue(
            should_keep_record(
                publish_time="2026-04-05T09:00:00+08:00",
                collect_date="2026-04-05",
                days=7,
            )
        )

    def test_pipeline_runner_writes_content_and_analysis(self) -> None:
        from content_collection_topic_analysis.models import ContentRecord, PipelineRequest, TopicInsightRecord
        from content_collection_topic_analysis.pipeline import PipelineRunner

        class FakeCollector:
            def collect(self, request: PipelineRequest, platform: str) -> list[ContentRecord]:
                return [
                    ContentRecord(
                        platform=platform,
                        keyword=request.keywords[0],
                        title="示例标题",
                        summary="示例摘要",
                        author="作者",
                        publish_time="2026-04-05T09:00:00+08:00",
                        url=f"https://example.com/{platform}",
                        read_count=100,
                        like_count=20,
                        comment_count=5,
                        raw_content="正文",
                        collect_date="2026-04-05",
                    )
                ]

        class FakeWriter:
            def __init__(self) -> None:
                self.content_records: list[ContentRecord] = []
                self.analysis_records: list[TopicInsightRecord] = []

            def write_content_records(self, records: list[ContentRecord]) -> None:
                self.content_records.extend(records)

            def write_analysis_records(self, records: list[TopicInsightRecord]) -> None:
                self.analysis_records.extend(records)

        class FakeAnalyzer:
            def analyze(self, records: list[ContentRecord]) -> TopicInsightRecord:
                return TopicInsightRecord(
                    platform=records[0].platform,
                    keyword=records[0].keyword,
                    collect_date=records[0].collect_date,
                    sample_size=len(records),
                    topic_direction="高互动模板",
                    why_it_works="信息密度高",
                    content_angle_suggestion="加上案例拆解",
                )

        request = PipelineRequest(
            keywords=["直播带货"],
            platforms=["wechat_mp", "xiaohongshu"],
            days=1,
            top_n=5,
            sort_by="engagement",
            with_analysis=True,
            collect_date="2026-04-05",
        )
        writer = FakeWriter()
        runner = PipelineRunner(collector=FakeCollector(), writer=writer, analyzer=FakeAnalyzer())

        result = runner.run(request)

        self.assertEqual(result.content_count, 2)
        self.assertEqual(result.analysis_count, 2)
        self.assertEqual(len(writer.content_records), 2)
        self.assertEqual(len(writer.analysis_records), 2)

    def test_skill_config_reads_table_id_overrides(self) -> None:
        from content_collection_topic_analysis.config import SkillConfig

        with patch.dict(
            "os.environ",
            {
                "LARK_CONTENT_TABLE_ID": "tbl_content",
                "LARK_ANALYSIS_TABLE_ID": "tbl_analysis",
            },
            clear=False,
        ):
            config = SkillConfig.from_env()

        self.assertEqual(config.content_table_id, "tbl_content")
        self.assertEqual(config.analysis_table_id, "tbl_analysis")

    def test_skill_config_reads_creator_watchlist_override(self) -> None:
        from content_collection_topic_analysis.config import SkillConfig

        with patch.dict(
            "os.environ",
            {
                "CREATOR_WATCHLIST_PATH": "/tmp/watch.json",
            },
            clear=False,
        ):
            config = SkillConfig.from_env()

        self.assertEqual(config.creator_watchlist_path, "/tmp/watch.json")

    def test_find_existing_record_id_by_record_key(self) -> None:
        from content_collection_topic_analysis.lark_base import LarkBaseWriter

        writer = LarkBaseWriter(
            lark_cli_bin="lark-cli",
            identity="user",
            base_token="base_xxx",
            base_name=None,
            folder_token=None,
            content_table_name="content_items",
            analysis_table_name="topic_insights",
            content_table_id="tbl_content",
            analysis_table_id=None,
        )

        with patch.object(
            writer,
            "_list_records",
            return_value={
                "fields": ["record_key", "title"],
                "data": [["rk_1", "标题1"], ["rk_2", "标题2"]],
                "record_id_list": ["rec_1", "rec_2"],
            },
        ):
            record_id = writer._find_existing_record_id("base_xxx", "tbl_content", "rk_2")

        self.assertEqual(record_id, "rec_2")

    def test_content_payload_includes_creator_watch_fields(self) -> None:
        from content_collection_topic_analysis.lark_base import LarkBaseWriter
        from content_collection_topic_analysis.models import ContentRecord

        payload = LarkBaseWriter._content_payload(
            ContentRecord(
                platform="wechat_mp",
                keyword="数字生命卡兹克",
                title="示例",
                summary="摘要",
                author="数字生命卡兹克",
                publish_time="2026-04-05T09:00:00",
                url="https://example.com/a",
                read_count=1,
                like_count=2,
                comment_count=3,
                raw_content="正文",
                collect_date="2026-04-05",
                monitor_type="creator_watch",
                creator_name="数字生命卡兹克",
                match_author="数字生命卡兹克",
            )
        )

        self.assertEqual(payload["monitor_type"], "creator_watch")
        self.assertEqual(payload["creator_name"], "数字生命卡兹克")
        self.assertEqual(payload["match_author"], "数字生命卡兹克")

    def test_load_creator_watchlist_reads_exact_creators(self) -> None:
        from content_collection_topic_analysis.creator_watch import load_creator_watchlist

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "watch.json"
            path.write_text(
                json.dumps(
                    {
                        "platform": "wechat_mp",
                        "match_mode": "exact",
                        "creators": ["饼干哥哥 AGI", "数字生命卡兹克", "TATALAB"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            watch = load_creator_watchlist(str(path))

        self.assertEqual(watch.platform, "wechat_mp")
        self.assertEqual(watch.match_mode, "exact")
        self.assertEqual(watch.creators, ["饼干哥哥 AGI", "数字生命卡兹克", "TATALAB"])

    def test_filter_records_by_exact_author(self) -> None:
        from content_collection_topic_analysis.adapters.wechat_mp import filter_records_by_exact_author
        from content_collection_topic_analysis.models import ContentRecord

        base = ContentRecord(
            platform="wechat_mp",
            keyword="数字生命卡兹克",
            title="示例",
            summary="",
            author="数字生命卡兹克",
            publish_time="2026-04-05T09:00:00",
            url="https://example.com/1",
            read_count=1,
            like_count=2,
            comment_count=3,
            raw_content="",
            collect_date="2026-04-05",
        )
        records = [
            base,
            replace(base, author="数字生命卡兹克 Pro", url="https://example.com/2"),
        ]

        filtered = filter_records_by_exact_author(records, "数字生命卡兹克")

        self.assertEqual([item.author for item in filtered], ["数字生命卡兹克"])

    def test_creator_watch_runner_collects_multiple_creators(self) -> None:
        from content_collection_topic_analysis.creator_watch import CreatorWatchConfig, run_creator_watch
        from content_collection_topic_analysis.models import ContentRecord

        class FakeAdapter:
            def collect(self, keyword: str, days: int, top_n: int, sort_by: str, collect_date: str) -> list[ContentRecord]:
                return [
                    ContentRecord(
                        platform="wechat_mp",
                        keyword=keyword,
                        title=f"{keyword} 的新文章",
                        summary="摘要",
                        author=keyword,
                        publish_time="2026-04-05T09:00:00",
                        url=f"https://example.com/{keyword}",
                        read_count=1,
                        like_count=2,
                        comment_count=3,
                        raw_content="",
                        collect_date=collect_date,
                    )
                ]

        class FakeWriter:
            def __init__(self) -> None:
                self.content_records: list[ContentRecord] = []

            def write_content_records(self, records: list[ContentRecord]) -> None:
                self.content_records.extend(records)

        watch = CreatorWatchConfig(
            platform="wechat_mp",
            match_mode="exact",
            creators=["饼干哥哥 AGI", "TATALAB"],
        )
        writer = FakeWriter()

        records = run_creator_watch(
            watch=watch,
            adapter=FakeAdapter(),
            writer=writer,
            days=1,
            top_n=10,
            collect_date="2026-04-05",
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(len(writer.content_records), 2)
        self.assertTrue(all(record.monitor_type == "creator_watch" for record in records))
        self.assertEqual([record.creator_name for record in records], ["饼干哥哥 AGI", "TATALAB"])


if __name__ == "__main__":
    unittest.main()
