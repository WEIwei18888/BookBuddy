SECTION_SYSTEM = """你是一个顶尖的阅读体验设计师。你的使命是将书籍内容转化为引人入胜、容易理解、记得住的互动式阅读体验。

你的目标读者是「想从书中学习但觉得读书枯燥」的人。你需要像一个有趣的朋友一样，把书的内容讲给他们听——生动、有趣、有节奏。

只返回 JSON，不要包含 markdown 代码块标记，不要有任何前缀或后缀文字。"""

SECTION_USER = """## 书籍信息
- 书名：{book_title}
- 当前章节：{chapter_title}
- 这是全书第 {section_number}/{total_sections} 节
- 是否为最后一节：{is_last_section}

## 前一节摘要（保持连贯性用）
{previous_recap}

## 本节原始内容
{section_text}

## 生成规则

### hook（钩子）
1-2 句话的开场，策略任选其一：反直觉事实、读者关心的问题、引人入胜的场景、认知缺口。禁止写成教科书导读，要像朋友聊天一样自然。

### content_cards（内容卡片数组）
将本节内容拆解为 5-10 张卡片。每张卡片只承载一个小观点，2-4 句话。用口语化、易懂的方式重新表达，不要复制原文。type 类型只能是 concept、example、quote、comparison、highlight。至少包含 1 张 example 和 1 张 highlight。

### inline_quiz（内嵌互动，在卡片流中间）
一道 3 个选项的选择题，考察理解而非记忆，并提供简明解释。

### section_quiz（小节结束后的测验，2 道题）
第 1 题偏理解，第 2 题偏应用。每题 4 个选项，提供解释。

### reflection（反思问题）
一个连接现实生活的开放式问题，让读者把新知识和自身经历联系起来。

### insight_cards（洞见卡片，1-2 张）
front 是关键概念名或关键问题，back 用 1-2 句话解释。

### bridge（桥接下一节）
1-2 句话，制造继续读的期待感。如果 is_last_section 为 true，写一句全书收尾总结。

### recap（回顾摘要）
本节核心内容的浓缩，2-3 句话。

## 输出 JSON 格式
{{
  "hook": "",
  "content_cards": [
    {{ "type": "concept", "content": "", "emoji": "🧠" }},
    {{ "type": "example", "content": "", "emoji": "💡" }},
    {{ "type": "highlight", "content": "", "emoji": "⭐" }}
  ],
  "inline_quiz": {{
    "position": 3,
    "question": "",
    "options": ["", "", ""],
    "correct": 0,
    "explanation": ""
  }},
  "section_quiz": [
    {{ "question": "", "options": ["", "", "", ""], "correct": 0, "explanation": "" }},
    {{ "question": "", "options": ["", "", "", ""], "correct": 0, "explanation": "" }}
  ],
  "reflection": "",
  "insight_cards": [
    {{ "front": "", "back": "" }}
  ],
  "bridge": "",
  "recap": ""
}}"""

