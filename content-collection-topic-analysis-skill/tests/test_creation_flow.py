from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class CreationCliTests(unittest.TestCase):
    def test_help_lists_creation_flags(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_creation.py"), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--topic-title", result.stdout)
        self.assertIn("--audience", result.stdout)
        self.assertIn("--pain-point", result.stdout)
        self.assertIn("--supporting-point", result.stdout)
        self.assertIn("--dry-run", result.stdout)


class WechatCreationTests(unittest.TestCase):
    def test_builtin_wechat_article_creator_generates_markdown(self) -> None:
        from content_collection_topic_analysis.creation_models import CreationBrief
        from content_collection_topic_analysis.wechat_article_creator import BuiltinWechatArticleCreator

        brief = CreationBrief(
            topic_title="Claude Code 爆火之后，普通人到底该怎么用",
            audience="想把 AI 真正接入工作流的内容创作者与独立开发者",
            pain_points=[
                "看了很多 Claude Code 讨论，但不知道跟自己有什么关系",
                "想上手，却不知道应该从哪个场景开始",
            ],
            content_goal="建立专业度并给出可直接执行的方法",
            core_claim="Claude Code 真正的价值不在于新鲜，而在于它把可复用的工作流前移了。",
            supporting_points=[
                "热点会过去，但工作流一旦形成就会沉淀为生产力",
                "多数人卡住，不是因为不会写提示词，而是不知道先接哪一段工作",
                "从一个高频、小闭环的任务切入，比追求全自动更容易跑通",
            ],
            source_materials=[
                "近期关于 Claude Code 源码、工作流和命令实践的内容热度较高",
                "用户更关注上手路径、命令范式和真实使用场景",
            ],
            brand_tone="专业、直接、不过度贩卖焦虑",
            cta="从你每天最重复的一项脑力任务开始，把它写成一个可复用流程。",
        )

        draft = BuiltinWechatArticleCreator().create(brief)

        self.assertEqual(draft.document_title, "《Claude Code 爆火之后，普通人到底该怎么用｜多平台内容成品》")
        self.assertIn("# Claude Code 爆火之后，普通人到底该怎么用", draft.markdown)
        self.assertIn("## 开头", draft.markdown)
        self.assertIn("## 为什么这个问题现在必须重视", draft.markdown)
        self.assertIn("## 常见误区", draft.markdown)
        self.assertIn("## 正确做法", draft.markdown)
        self.assertIn("## 案例或场景拆解", draft.markdown)
        self.assertIn("## 最后的建议", draft.markdown)
        self.assertIn("Claude Code", draft.markdown)
        self.assertIn("可复用流程", draft.markdown)

    def test_lark_doc_writer_creates_document_from_markdown(self) -> None:
        from content_collection_topic_analysis.commands import CommandResult
        from content_collection_topic_analysis.creation_models import WechatArticleDraft
        from content_collection_topic_analysis.lark_doc import LarkDocWriter

        draft = WechatArticleDraft(
            document_title="《测试标题｜多平台内容成品》",
            article_title="测试标题",
            markdown="# 测试标题\n\n## 开头\n这是一段测试内容。",
        )

        with patch(
            "content_collection_topic_analysis.lark_doc.run_command",
            return_value=CommandResult(
                stdout=json.dumps(
                    {
                        "data": {
                            "url": "https://my.feishu.cn/docx/example",
                            "document": {"document_id": "doccn123"},
                        }
                    },
                    ensure_ascii=False,
                ),
                stderr="",
                returncode=0,
            ),
        ) as mock_run:
            result = LarkDocWriter(
                lark_cli_bin="lark-cli",
                identity="user",
                folder_token="fldcn123",
            ).write_article(draft)

        command = mock_run.call_args.args[0]
        self.assertEqual(command[:3], ["lark-cli", "docs", "+create"])
        self.assertIn("--folder-token", command)
        self.assertIn("fldcn123", command)
        self.assertIn("--title", command)
        self.assertIn(draft.document_title, command)
        self.assertEqual(result.doc_token, "doccn123")
        self.assertEqual(result.url, "https://my.feishu.cn/docx/example")


if __name__ == "__main__":
    unittest.main()
