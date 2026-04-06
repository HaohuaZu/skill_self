---
name: content-collection-topic-analysis
description: 采集微信公众号与小红书内容，支持关键词采集与公众号博主监控，统一结构化后写入飞书多维表格，并可选生成结构化选题分析；也支持基于结构化 brief 生成公众号成品写入飞书文档，以及把飞书文档按 Bauhaus 风格排版后写入微信公众号草稿箱。适用于手动触发或定时触发的数据流水线场景，依赖 opencli、cn8n API 与 lark-cli。
---

# Content Collection, Topic Analysis And Content Creation

这是一个纯后端 Codex Skill，不提供前端页面、Web 服务或交互式 UI。

## 适用场景

- 按关键词采集微信公众号文章
- 按公众号名精确监控指定博主的新文章
- 按关键词采集小红书笔记
- 将内容统一整理后写入飞书多维表格
- 对单次采集结果进行结构化选题分析
- 基于结构化选题 brief 生成公众号文章成品
- 将公众号成品写入飞书文档
- 从飞书文档抓取内容并按 Bauhaus 风格排版
- 上传正文图片到微信公众号后台并创建草稿
- 由人工手动触发，或由 cron/automation 定时触发

## 运行前提

- 已安装 `opencli`
- 已安装 `lark-cli`
- 可访问微信公众号采集所需的 cn8n API
- 如需模型分析，可提供兼容 OpenAI 接口的模型配置

## 入口

采集与分析入口为 `python3 scripts/run_pipeline.py ...`

公众号博主监控入口为 `python3 scripts/run_creator_watch.py ...`

公众号内容创作入口为 `python3 scripts/run_creation.py ...`

核心流程：

1. 解析参数与环境变量
2. 调用平台 adapter 采集微信公众号或小红书内容
3. 统一整理为稳定字段结构
4. 将内容写入飞书多维表格
5. 可选调用模型生成结构化选题分析并写入分析表

公众号博主监控流程：

1. 读取公众号监控名单配置
2. 调用公众号搜索接口按公众号名抓取候选文章
3. 通过 `wx_name == creator_name` 做精确匹配
4. 过滤最近 N 天的新文章
5. 写入现有飞书内容表，并标记 `monitor_type=creator_watch`

公众号创作流程：

1. 接收结构化 `CreationBrief`
2. 生成可直接发布的公众号 Markdown 成稿
3. 使用 `lark-cli docs +create` 写入飞书文档

公众号发布流程：

1. 读取飞书文档 Markdown
2. 生成微信公众号兼容的 Bauhaus 风格 HTML
3. 上传正文图片与封面图到微信公众号后台
4. 调用草稿接口写入公众号草稿箱

## 输出数据

内容记录会按稳定字段写入飞书多维表格，包括：

- `platform`
- `keyword`
- `title`
- `summary`
- `author`
- `publish_time`
- `url`
- `read_count`
- `like_count`
- `comment_count`
- `raw_content`
- `collect_date`

分析记录会写入独立分析表，包含：

- `topic_direction`
- `why_it_works`
- `content_angle_suggestion`

公众号创作输入建议包含：

- `topic_title`
- `audience`
- `pain_points`
- `content_goal`
- `core_claim`
- `supporting_points`
- `source_materials`
- `brand_tone`
- `cta`

## 说明

- 数据读取、筛选、统计、复盘由 opencli 在飞书侧完成，不在本 Skill 内实现
- 平台能力通过 adapter 扩展，后续可增加更多内容平台
- 内容创作与采集分析分为独立入口，避免把整条流水线耦合在一个脚本中
- 微信公众号发布默认写入草稿箱，不直接群发
