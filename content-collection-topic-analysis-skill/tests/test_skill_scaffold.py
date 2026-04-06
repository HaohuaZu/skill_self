from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillScaffoldTests(unittest.TestCase):
    def test_required_skill_files_exist(self) -> None:
        required_files = [
            ROOT / "SKILL.md",
            ROOT / "agents" / "openai.yaml",
            ROOT / "scripts" / "run_pipeline.py",
        ]

        for file_path in required_files:
            self.assertTrue(file_path.exists(), f"missing required file: {file_path}")

    def test_skill_metadata_mentions_supported_platforms(self) -> None:
        skill_md = ROOT / "SKILL.md"
        self.assertTrue(skill_md.exists(), "SKILL.md must exist before metadata validation")

        text = skill_md.read_text(encoding="utf-8")
        self.assertIn("微信公众号", text)
        self.assertIn("小红书", text)
        self.assertIn("飞书多维表格", text)


if __name__ == "__main__":
    unittest.main()
