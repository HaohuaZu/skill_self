# skill_self

个人技能仓库，当前包含两个本地 skill：

- `de-ai-writing`
- `content-collection-topic-analysis-skill`

## 目录

### `de-ai-writing`

用于把中文长文、公众号文章、个人表达类文本改写得更像真人写作，减少模板化和机器感。

入口文件：

- `de-ai-writing/SKILL.md`

参考资料：

- `de-ai-writing/references/checklist.md`
- `de-ai-writing/references/examples.md`

### `content-collection-topic-analysis-skill`

用于采集公众号与小红书内容，写入飞书多维表格，并支持结构化选题分析、公众号内容创作与发布链路。

入口文件：

- `content-collection-topic-analysis-skill/SKILL.md`

主要目录：

- `content-collection-topic-analysis-skill/scripts/`
- `content-collection-topic-analysis-skill/tests/`
- `content-collection-topic-analysis-skill/config/`
- `content-collection-topic-analysis-skill/agents/`

## 测试

在 `content-collection-topic-analysis-skill` 下可运行：

```bash
python3 -m unittest tests/test_pipeline_core.py -v
python3 -m unittest tests/test_skill_scaffold.py -v
```

## 说明

- 仓库当前以 skill 原始目录结构为主，方便直接同步到本地技能目录。
- `content-collection-topic-analysis-skill` 当前公众号检索链路已适配极致了接口。
