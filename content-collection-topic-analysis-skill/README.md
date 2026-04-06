# 内容采集、分析与创作 Skill

一个纯后端的 Codex Skill，用于把选题采集、结构化分析、公众号内容创作，以及飞书文档到微信公众号草稿箱的发布链串起来。

## 能力范围

- 微信公众号关键词采集
- 微信公众号博主监控
- 小红书关键词采集
- 结构化选题分析并写入飞书多维表格
- 公众号文章创作并写入飞书文档
- 飞书文档排版后发布到微信公众号草稿箱

## 目录结构

- `SKILL.md`：Skill 说明
- `agents/openai.yaml`：Agent 元数据
- `scripts/run_pipeline.py`：采集与分析入口
- `scripts/run_creator_watch.py`：公众号博主监控入口
- `scripts/run_creation.py`：公众号创作入口
- `scripts/run_wechat_publish.py`：飞书文档到公众号草稿发布入口
- `scripts/content_collection_topic_analysis/`：核心实现
- `tests/`：单元测试

## 运行入口

```bash
python3 scripts/run_pipeline.py --help
python3 scripts/run_creator_watch.py --help
python3 scripts/run_creation.py --help
python3 scripts/run_wechat_publish.py --help
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
