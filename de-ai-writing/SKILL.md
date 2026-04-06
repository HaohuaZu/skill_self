---
name: de-ai-writing
description: Use when the user wants writing to feel less AI-generated, more human, more lived-in, or more like something a real person would actually say. Trigger for Chinese long-form articles, blog rewrites,公众号文案, personal essays, narrative posts, or any request mentioning 去AI味、像真人写、有人味、别太机器、别太模板化、公众号成稿.
---

# De-AI Writing

This skill removes the specific signals that make writing feel generated, over-smoothed, or template-driven.

The goal is not to make writing messy. The goal is to make it sound owned.

## When to Use

Use this skill when the user asks for any of the following:
- “去 AI 味”
- “像真人写”
- “有人味一点”
- “不要那么像模型生成”
- “不要太模板化”
- “像人在讲，不像在总结”

Also use it when the draft shows obvious generated-writing symptoms even if the user does not name them directly.

For public-account articles, use this skill both to remove AI flavor and to finish the piece into something that reads like a publishable Chinese公众号 draft.

## Core Rule

Do not merely paraphrase.

Rewrite from the point of view of a person who has actually lived through the thing being described.

That means:
- preserve the user’s meaning
- preserve useful structure
- remove visible generation artifacts
- restore judgment, friction, uncertainty, and narrative continuity

## Process

### 1. Diagnose Before Rewriting

Scan the draft for high-probability AI flavor:
- generic opening that could fit any article
- abstract labels repeated without new information
- tidy framework voice replacing lived narration
- prompt/tutorial/checklist residue
- over-explaining obvious points
- repeated adjacent restatements
- too many choppy short sentences
- emotion that feels declared rather than earned

If several of these appear, rewrite at paragraph level rather than sentence level.

### 2. Decide the Proper Voice

Pick the strongest human mode for the piece:
- **retelling voice**: “this is what happened, this is what I thought then”
- **reflection voice**: “I used to think X, later I realized Y”
- **judgment voice**: “this works, this doesn’t, here’s why”
- **confessional voice**: “I was unsure, embarrassed, cautious, or wrong”

Prefer one dominant mode. Do not mix all four unless the piece truly needs it.

### 3. Rewrite Toward Ownership

During rewrite:
- replace framework language with remembered experience
- keep concrete stakes over abstract summaries
- merge overly short sentences that break flow without adding force
- keep some edges; not every paragraph needs a polished lesson
- let the narrator sound like someone talking after having gone through it

Short sentences are allowed, but only when they create real emphasis.

### 4. Remove Generated Scaffolding

Delete or compress:
- obvious “核心是 / 本质上 / 关键在于 / 说白了” repetition
- formulaic transitions that do not move the thought forward
- explicit prompt artifacts
- “how-to” explanation when the paragraph should be narrative
- symmetrical list-like prose unless the content truly is list-shaped

If a paragraph sounds like it is trying to prove it is well-written, simplify it.

### 5. Preserve Human Structure

Strong Chinese long-form writing often feels human not because the words are fancy, but because the structure feels lived rather than assembled.

When revising:
- let one paragraph carry one main movement of thought
- do not collapse a full emotional or logical turn into one dense block
- if the narrator changes direction, add a bridge sentence explaining why
- make past projects or past attempts do real work: each one should reveal a limit, not just provide credentials
- alternate between concrete experience and interpretation instead of stacking abstractions
- keep some breathing room after dense technical or judgment-heavy paragraphs

For experience-sharing posts, a useful rhythm is:
- what I did before
- what each experience taught me could not work
- why that pushed me to change direction
- what I did next

### 6. Final Human Check

Before delivering, silently test:
- Does this sound like something the person would actually say out loud?
- Does the emotion come from the situation instead of adjectives?
- Is the rhythm natural, or is it chopped up for effect?
- Did I keep only one strongest version of each point?
- If a reader removed all headings, would the prose still feel human?

If not, rewrite again.

## Public Account Finishing Mode

Use this mode when the target output is a Chinese public-account article, newsletter-style long post, or founder/personal-brand article meant to be read top-to-bottom.

The job here is not just “remove AI flavor.” The job is to make the piece feel publishable.

### What good public-account finishing looks like

- the title is direct and human, not SEO sludge and not empty clickbait
- the opening establishes tension within the first 2-4 paragraphs
- the rhythm is readable on mobile, with paragraphs that breathe
- subheads help orientation but do not read like a consulting deck
- the piece has escalation: context -> friction -> turn -> method -> reflection
- the ending lands emotionally instead of fading into generic encouragement

### Rewrite rules for public-account mode

- compress over-explained logic into cleaner narrative flow
- keep headings, but make them sound spoken rather than “frameworked”
- remove “summary after every paragraph” habits
- keep useful repetition only when it builds emotional or rhetorical force
- favor medium-length paragraphs over sentence fragments
- let the opening hook a reader, not just introduce a topic
- make the final section feel earned; avoid generic uplift
- keep paragraph breaks generous enough for mobile reading; do not merge everything into giant walls
- preserve explicit bridge paragraphs when the narrator changes career direction, product direction, or point of view
- if a “personal IP / trust” section exists, explain the trust-building mechanism, not just the slogan

### Default structure for public-account mode

If the user did not provide a required template, prefer this progression:
1. title with a concrete claim or tension
2. opening with discomfort, contradiction, or surprise
3. identity/context section: who I am and why this mattered
4. turning point: what changed in how I saw the problem
5. main body: what happened and what I learned
6. closing reflection: what this means now

Do not force this structure if the user has already provided a better one.

### Experience-Sharing Post Mode

For Chinese experience-sharing posts, especially those about创业、接单、职业转向、技术商业化:

- let the opening create pressure before explanation
- use earlier projects as evidence, but make each one end with a revealed limitation
- add a direct transition when the narrator changes track: “because of those experiences, I moved from X to Y”
- say practical motives plainly when they matter, such as周期、现金流、验证速度、回款速度
- treat “personal IP” as a trust system: what the narrator publishes, how often, what a new reader learns, why that changes buying confidence
- keep the strongest “I realized…” moments, especially first encounters with doubt, mismatch, or changed judgment

This mode should feel like a person looking back and connecting the dots, not like a model arranging lessons into a clean deck.

## Output Style

Default output:
- provide the revised version directly
- do not over-explain the rewrite unless the user asks
- if useful, add a very short note on 2-4 principles you applied

Do not return a lecture on writing theory unless requested.

## Read Next

- For fast review questions, use [references/checklist.md](references/checklist.md)
- For concrete before/after rewrite patterns, use [references/examples.md](references/examples.md)
