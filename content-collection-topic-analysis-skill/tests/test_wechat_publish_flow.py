from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PublishCliTests(unittest.TestCase):
    def test_help_lists_publish_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_wechat_publish.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--doc", result.stdout)
        self.assertIn("--theme", result.stdout)
        self.assertIn("--author", result.stdout)
        self.assertIn("--cover-image", result.stdout)
        self.assertIn("--dry-run", result.stdout)


class WechatPublishCoreTests(unittest.TestCase):
    def test_extract_feishu_doc_token_from_url(self) -> None:
        from content_collection_topic_analysis.feishu_doc import extract_doc_token

        self.assertEqual(
            extract_doc_token("https://www.feishu.cn/docx/ZiHRdzzUrolRuoxFgtDcp5Djnwd"),
            "ZiHRdzzUrolRuoxFgtDcp5Djnwd",
        )
        self.assertEqual(
            extract_doc_token("ZiHRdzzUrolRuoxFgtDcp5Djnwd"),
            "ZiHRdzzUrolRuoxFgtDcp5Djnwd",
        )

    def test_extract_markdown_image_urls(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import (
            extract_markdown_image_urls,
            replace_feishu_image_tokens,
        )

        markdown = "\n".join(
            [
                "# 标题",
                "![封面](https://example.com/cover.png)",
                '<image token="imgtok123" width="888" height="378" align="center"/>',
                "正文",
                '<img src="https://example.com/body.jpg" alt="body" />',
            ]
        )

        normalized = replace_feishu_image_tokens(markdown, {"imgtok123": "/tmp/imgtok123.png"})
        self.assertEqual(
            extract_markdown_image_urls(normalized),
            ["https://example.com/cover.png", "/tmp/imgtok123.png", "https://example.com/body.jpg"],
        )

    def test_replace_image_urls_in_html(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import replace_image_urls

        html = '<p><img src="https://example.com/a.png" /></p><p><img src="https://example.com/b.png" /></p>'
        updated = replace_image_urls(
            html,
            {
                "https://example.com/a.png": "https://mmbiz.qpic.cn/a.png",
                "https://example.com/b.png": "https://mmbiz.qpic.cn/b.png",
            },
        )

        self.assertIn('src="https://mmbiz.qpic.cn/a.png"', updated)
        self.assertIn('src="https://mmbiz.qpic.cn/b.png"', updated)

    def test_render_bauhaus_html_applies_key_styles(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html("# 标题\n\n## 小标题\n\n正文段落。")

        self.assertIn("<section", html)
        self.assertIn("color: #e30613", html)
        self.assertIn("color: #004d9f", html)
        self.assertIn("正文段落。", html)

    def test_render_bauhaus_html_preserves_unordered_list_markup(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html("- 第一项\n- 第二项")

        self.assertIn("<ul", html)
        self.assertIn("<li", html)
        self.assertIn('class="list-unordered"', html)
        self.assertIn('class="list-marker"', html)
        self.assertIn(">•</span>", html)
        self.assertIn("list-style: none", html)

    def test_render_bauhaus_html_preserves_ordered_list_markup(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html("1. 第一项\n2. 第二项\n3. 第三项")

        self.assertIn("<ol", html)
        self.assertIn("<li", html)
        self.assertIn('class="list-ordered"', html)
        self.assertIn(">1.</span>", html)
        self.assertIn(">2.</span>", html)
        self.assertIn(">3.</span>", html)
        self.assertIn("list-style: none", html)

    def test_render_bauhaus_html_supports_markdown_tables(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            "\n".join(
                [
                    "| 功能 | 说明 |",
                    "| --- | --- |",
                    "| 表格 | 应该渲染成 table |",
                ]
            )
        )

        self.assertIn("<table", html)
        self.assertIn("<th", html)
        self.assertIn("<td", html)
        self.assertIn("应该渲染成 table", html)

    def test_render_bauhaus_html_supports_feishu_lark_table_markup(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            """
### 表格测试

<lark-table rows="3" cols="2" header-row="true">
  <lark-tr>
    <lark-td>元素</lark-td>
    <lark-td>说明</lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>表格</lark-td>
    <lark-td>需要渲染成微信可用表格</lark-td>
  </lark-tr>
</lark-table>
            """.strip()
        )

        self.assertIn("<table", html)
        self.assertIn("<th", html)
        self.assertIn("需要渲染成微信可用表格", html)

    def test_render_bauhaus_html_treats_first_lark_table_row_as_header_by_default(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            """
<lark-table rows="2" cols="2">
  <lark-tr>
    <lark-td>功能</lark-td>
    <lark-td>说明</lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>表格</lark-td>
    <lark-td>第一行默认表头</lark-td>
  </lark-tr>
</lark-table>
            """.strip()
        )

        self.assertIn("<thead", html)
        self.assertIn("<th", html)
        self.assertIn("background-color: #004d9f", html)
        self.assertIn("color: #ffffff", html)

    def test_render_bauhaus_html_converts_quote_container_to_blockquote(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            """
## 引用样式

<quote-container>
每套主题都有独特的引用样式。
</quote-container>
            """.strip()
        )

        self.assertIn("<blockquote", html)
        self.assertNotIn("<quote-container>", html)
        self.assertIn("background-color: #fff4d6", html)

    def test_render_bauhaus_html_converts_grid_block_to_image_grid(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            """
<grid cols="2">
  <column width="50">
    <image token="img1" width="600" height="400" align="center"/>
  </column>
  <column width="50">
    <image token="img2" width="600" height="400" align="center"/>
  </column>
</grid>
            """.strip()
        )

        self.assertIn('class="image-grid"', html)
        self.assertIn('class="image-grid-table"', html)
        self.assertIn('class="grid-card"', html)
        self.assertIn('class="grid-img"', html)
        self.assertIn("overflow-x: scroll", html)
        self.assertIn("overflow-y: hidden", html)
        self.assertIn("border-collapse: separate", html)
        self.assertRegex(html, r'width:\s*\d+px')
        self.assertIn("background-color: #ffffff", html)
        self.assertIn("object-fit: contain", html)
        self.assertNotIn("<grid", html)
        self.assertNotIn("<column", html)

    def test_render_bauhaus_html_wraps_code_block_with_mac_header(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html("```python\nif True:\n  print('hello')\n```")
        self.assertIn("background: #ff5f56", html)
        self.assertIn("background: #ffbd2e", html)
        self.assertIn("background: #27c93f", html)
        self.assertIn("class=\"hljs", html)
        self.assertIn("background-color: #f0f0f0", html)
        self.assertIn("border-left: 6px solid #e30613", html)
        self.assertNotIn('class="code-block-panel"', html)
        self.assertIn('class="code-line"', html)
        self.assertIn("white-space: pre !important", html)
        self.assertIn("word-break: keep-all !important", html)
        self.assertIn("overflow-wrap: normal !important", html)
        self.assertIn("<pre", html)
        self.assertIn("<br", html)
        self.assertIn("print", html)

    def test_render_bauhaus_html_groups_consecutive_images_into_grid(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            "\n".join(
                [
                    "![图一](https://example.com/a.png)",
                    "",
                    "![图二](https://example.com/b.png)",
                ]
            )
        )

        self.assertIn('class="image-grid"', html)
        self.assertIn('class="grid-img"', html)
        self.assertIn("https://example.com/a.png", html)
        self.assertIn("https://example.com/b.png", html)

    def test_render_bauhaus_html_keeps_four_images_in_one_scroll_track(self) -> None:
        from content_collection_topic_analysis.wechat_formatting import render_bauhaus_html

        html = render_bauhaus_html(
            "\n".join(
                [
                    "![图一](https://example.com/a.png)",
                    "",
                    "![图二](https://example.com/b.png)",
                    "",
                    "![图三](https://example.com/c.png)",
                    "",
                    "![图四](https://example.com/d.png)",
                ]
            )
        )

        self.assertIn('class="image-grid"', html)
        self.assertIn('class="image-grid-table"', html)
        self.assertEqual(html.count('class="grid-card"'), 4)
        self.assertEqual(html.count('class="grid-img"'), 4)
        self.assertIn("overflow-x: scroll", html)

    def test_fetcher_reads_markdown_from_lark_docs_output(self) -> None:
        from content_collection_topic_analysis.commands import CommandResult
        from content_collection_topic_analysis.feishu_doc import FeishuDocFetcher

        with patch(
            "content_collection_topic_analysis.feishu_doc.run_command",
            return_value=CommandResult(
                stdout='{"data":{"doc_id":"docx123","title":"标题","markdown":"# 正文"}}',
                stderr="",
                returncode=0,
            ),
        ):
            fetched = FeishuDocFetcher(lark_cli_bin="lark-cli", identity="user").fetch("docx123")

        self.assertEqual(fetched.doc_token, "docx123")
        self.assertEqual(fetched.title, "标题")
        self.assertEqual(fetched.markdown, "# 正文")

    def test_build_draft_payload_uses_cover_and_rendered_html(self) -> None:
        from content_collection_topic_analysis.wechat_publish import WechatArticleDraftInput, WechatPublisher

        publisher = WechatPublisher(app_id="appid", app_secret="secret")
        payload = publisher.build_draft_payload(
            WechatArticleDraftInput(
                title="测试标题",
                author="测试作者",
                digest="测试摘要",
                content="<section><h1>测试标题</h1><p>正文</p></section>",
                content_source_url="",
                thumb_media_id="thumb123",
            )
        )

        article = payload["articles"][0]
        self.assertEqual(article["title"], "测试标题")
        self.assertEqual(article["author"], "测试作者")
        self.assertEqual(article["thumb_media_id"], "thumb123")
        self.assertIn("<section>", article["content"])

    def test_select_cover_prefers_explicit_then_first_doc_image(self) -> None:
        from content_collection_topic_analysis.wechat_publish import select_cover_image

        self.assertEqual(
            select_cover_image("https://example.com/explicit.png", ["https://example.com/doc1.png"]),
            "https://example.com/explicit.png",
        )
        self.assertEqual(
            select_cover_image(None, ["https://example.com/doc1.png", "https://example.com/doc2.png"]),
            "https://example.com/doc1.png",
        )


if __name__ == "__main__":
    unittest.main()
