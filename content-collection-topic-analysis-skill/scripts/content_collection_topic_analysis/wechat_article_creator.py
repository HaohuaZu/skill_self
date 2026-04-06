from __future__ import annotations

from .creation_models import CreationBrief, WechatArticleDraft


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item.strip())


class BuiltinWechatArticleCreator:
    def create(self, brief: CreationBrief) -> WechatArticleDraft:
        article_title = brief.topic_title.strip()
        document_title = f"《{article_title}｜多平台内容成品》"

        pain_points = [item.strip() for item in brief.pain_points if item.strip()]
        supporting_points = [item.strip() for item in brief.supporting_points if item.strip()]
        source_materials = [item.strip() for item in brief.source_materials if item.strip()]

        why_now = (
            f"{brief.audience}最近持续被这类话题吸引，不是因为工具名字更热，而是因为它开始真实影响工作方式。"
            f"如果一个工具只能带来一阵围观，它很快就会被下一个热点替代；"
            f"但如果它能把一段脑力劳动压缩成可复用流程，它就会从“新鲜感”变成“生产力”。"
            f"这也是这篇内容要解决的问题：{brief.core_claim}"
        )

        misconception_lines = []
        if pain_points:
            misconception_lines.append(
                f"第一种误区，是把自己的犹豫当成“还没准备好”，其实真正卡住的是这些具体问题：\n{_bullet_lines(pain_points)}"
            )
        misconception_lines.extend(
            [
                "第二种误区，是上来就想做一整套自动化系统。这样的目标听起来很高级，但对大多数人来说，第一步太重，反而更容易放弃。",
                "第三种误区，是只盯着工具界面和命令，不去思考它应该接入哪段业务流程。工具本身不会产生价值，只有嵌进真实任务里，才会变成可积累的成果。",
            ]
        )

        approach_paragraphs = [
            f"更有效的做法，是先围绕一个核心判断来搭建内容和行动路径：{brief.core_claim}",
            "先找一个高频、重复、小闭环的任务。它最好每天都会出现，最好有明确的输入和输出，最好你现在正因为它耗时而烦。",
            "然后把这个任务拆成三层：第一层是信息输入，第二层是判断过程，第三层是结果输出。只有拆开之后，你才知道哪些环节适合交给工具，哪些环节仍然必须由人来负责。",
        ]
        approach_paragraphs.extend(
            [
                f"接下来，再把支撑这件事成立的依据讲透：{point}"
                for point in supporting_points
            ]
        )
        approach_paragraphs.append(
            f"你的内容目标不是空泛地说“这个工具很强”，而是明确告诉读者：{brief.content_goal}。"
        )

        example_material = (
            "、".join(source_materials[:2])
            if source_materials
            else "近期这类内容里，读者尤其在意上手路径、真实工作流和具体命令范式"
        )
        example_section = (
            "举一个最实际的场景。假设你是一个内容创作者，每天都要把零散信息整理成一篇能发出去的文章。"
            "过去你的流程可能是：看资料、做判断、写提纲、改措辞、补结尾，全都在一个脑内流程里完成。"
            "这会导致两个问题：一是每次都从头开始，二是你根本不知道自己到底慢在哪。"
            f"而现在你可以把这条链拆开，先用工具完成资料归拢和初步结构化，再把精力集中在观点判断和表达打磨。"
            f"这类内容之所以最近容易获得高关注，本质上也和 {example_material} 这些信号有关：它们都在告诉用户，工具价值必须落到可复制的工作流里。"
        )

        final_section = (
            f"如果你只记住一句话，我希望是这句：{brief.core_claim}\n\n"
            "真正值得写、也值得做的内容，不是把新工具讲得更热，而是把使用路径讲得更清楚。"
            f"你接下来最应该做的动作也很简单：{brief.cta or '从一个高频任务开始，把它拆成输入、判断、输出三段，再决定哪一段交给工具。'}"
            f"\n\n写这类公众号内容时，语气上保持 {brief.brand_tone or '清晰、克制、直接'} 就够了。不要追求制造焦虑，而要帮助读者少走弯路。"
        )

        markdown = "\n\n".join(
            [
                f"# {article_title}",
                "## 开头",
                f"每次一个新工具火起来，最容易发生的事，不是更多人真的用起来，而是更多人开始围观。"
                f"可对 {brief.audience} 来说，围观没有意义，真正有意义的是：它能不能接进现有工作，能不能帮自己少走一段重复劳动。"
                f"所以这篇文章不打算讨论热闹，而是只讨论一件事：{brief.core_claim}",
                "## 为什么这个问题现在必须重视",
                why_now,
                "## 常见误区",
                "\n\n".join(misconception_lines),
                "## 正确做法",
                "\n\n".join(approach_paragraphs),
                "## 案例或场景拆解",
                example_section,
                "## 最后的建议",
                final_section,
            ]
        )

        return WechatArticleDraft(
            document_title=document_title,
            article_title=article_title,
            markdown=markdown,
        )
