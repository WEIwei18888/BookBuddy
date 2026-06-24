# BookBuddy（读伴）— 技术蓝图 最终版

> 上传一本书，AI 把它变成一段有互动、有节奏、记得住的阅读旅程。

---

## 一、产品概要

| 项目 | 说明 |
|------|------|
| 目标用户 | 想从书中获取知识，但觉得传统阅读枯燥、记不住的成年人 |
| 核心价值 | 把「一个人啃书」变成「有节奏、有互动、记得住」的阅读体验 |
| 使用方式 | 浏览器访问本地服务（localhost） |
| 语言支持 | 仅中文 |
| 用户模式 | 单用户，无需注册登录 |
| AI 服务 | DeepSeek API（deepseek-chat 模型） |

---

## 二、分期规划

### Phase 1 — 核心阅读体验（MVP）

这一期完成后产品就可用，能体验到核心价值。

包含功能：
- 上传 PDF，提取文本
- AI 将内容拆分为章节，算法将章节拆分为小节，AI 为每个小节生成结构化卡片流
- 卡片式阅读界面（hook → 内容卡片 → 内嵌互动 → 小节测验 → 桥接下一节）
- 阅读进度自动保存
- 书架页（展示已上传书籍和阅读进度）

不包含：间隔复习、AI 聊天、成就系统、前情回顾

### Phase 2 — 记忆增强

- 洞见卡片管理页
- 间隔复习系统（SM-2 算法）
- 「前情回顾」机制（每次继续阅读时回顾上次内容）
- 阅读统计仪表盘

### Phase 3 — 深度交互

- AI 聊天伴读（侧边栏，可就当前内容提问）
- 「用自己的话复述」功能 + AI 反馈
- 多本书知识关联
- 界面精细打磨

---

## 三、技术架构

```
┌─────────────────────────────────────────────┐
│                  浏览器                       │
│        React + Vite (localhost:5173)         │
│        Vite 代理 /api → localhost:8000       │
└─────────────────┬───────────────────────────┘
                  │ HTTP /api/*
┌─────────────────▼───────────────────────────┐
│         Python FastAPI (localhost:8000)       │
│                                              │
│  ┌──────────┐  ┌───────────┐ ┌───────────┐  │
│  │ PDF 处理  │  │ AI 处理    │ │ 数据存取   │  │
│  │ PyMuPDF  │  │ DeepSeek  │ │ SQLite    │  │
│  └──────────┘  └───────────┘ └───────────┘  │
└──────────────────────────────────────────────┘
```

### 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 前端 | React 18 + Vite + TailwindCSS | 生态成熟，code agent 友好，Tailwind 快速出 UI |
| 路由 | React Router v6 | 前端页面导航 |
| 状态管理 | Zustand | 比 Redux 轻量，API 简单 |
| HTTP 客户端 | Axios | 前端请求后端 API |
| 后端 | Python 3.11+ FastAPI | PDF 处理库生态最好，异步友好 |
| 数据库 | SQLite（标准库 sqlite3） | 单用户本地工具，零运维，一个文件 |
| PDF 提取 | PyMuPDF (pymupdf) | 速度快，中文支持好，提取质量高 |
| AI | DeepSeek API（通过 openai SDK 调用） | 中文理解力一流，JSON 输出稳定，成本极低 |

### 跨域与代理配置

前端运行在 5173 端口，后端运行在 8000 端口。通过 Vite 开发代理解决跨域问题，不需要在 FastAPI 中配置 CORS（生产环境可前后端同域部署）。

**vite.config.js 代理配置：**
```js
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

同时在 FastAPI 中加上 CORS 中间件作为保底（某些场景 Vite 代理可能未生效）：

**main.py CORS 配置：**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 四、项目目录结构

```
bookbuddy/
├── backend/
│   ├── main.py                 # FastAPI 入口，注册路由、CORS、启动事件
│   ├── config.py               # 配置（从 .env 读取 API Key、数据库路径）
│   ├── database.py             # SQLite 建表和连接管理
│   ├── models.py               # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── books.py            # 书籍 API（上传、列表、详情、删除）
│   │   ├── sections.py         # 小节 API（获取内容、处理状态）
│   │   ├── progress.py         # 阅读进度 API
│   │   └── quiz.py             # 测验提交和结果 API
│   ├── services/
│   │   ├── pdf_service.py      # PDF 文本提取和清洗
│   │   ├── ai_service.py       # DeepSeek API 调用封装（含重试、JSON解析）
│   │   └── processing.py       # 书籍处理管线（章节拆分 + 小节拆分 + AI生成）
│   ├── prompts/
│   │   ├── book_info.py        # 书籍信息提取 prompt
│   │   ├── split_chapters.py   # 章节拆分 prompt
│   │   └── generate_section.py # 小节内容生成 prompt（核心）
│   ├── requirements.txt
│   ├── .env                    # 环境变量（不提交到 git）
│   └── data/                   # SQLite 数据库文件存放处
│       └── .gitkeep
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js          # 含 /api 代理配置
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx             # React Router 路由定义
│   │   ├── stores/
│   │   │   └── useStore.js     # Zustand 全局状态
│   │   ├── pages/
│   │   │   ├── Bookshelf.jsx   # 书架页（首页）
│   │   │   ├── BookOverview.jsx # 书籍总览页
│   │   │   └── Reader.jsx      # 阅读页（核心页面）
│   │   ├── components/
│   │   │   ├── BookCard.jsx    # 书架上的书籍卡片
│   │   │   ├── UploadArea.jsx  # 上传 PDF 区域（支持拖放）
│   │   │   ├── ProgressBar.jsx # 阅读进度条
│   │   │   ├── HookCard.jsx    # 钩子卡片
│   │   │   ├── ContentCard.jsx # 内容卡片（根据 type 渲染不同样式）
│   │   │   ├── QuizCard.jsx    # 测验卡片（选择题 + 反馈）
│   │   │   ├── ReflectionCard.jsx # 反思提问卡片
│   │   │   ├── InsightCard.jsx # 洞见翻转卡片
│   │   │   └── BridgeCard.jsx  # 桥接下一节卡片
│   │   ├── api/
│   │   │   └── client.js       # Axios 实例和所有 API 调用函数
│   │   └── styles/
│   │       └── index.css       # Tailwind @layer 入口 + 全局样式
│   └── public/
│
├── start.sh                    # 一键启动脚本（同时启动前后端）
├── .gitignore
└── README.md
```

---

## 五、数据库设计

使用 Python 标准库 `sqlite3`（同步），简单可靠。FastAPI 路由函数用 `def`（非 `async def`），FastAPI 会自动在线程池中执行，不会阻塞事件循环。

### 建表 SQL

```sql
-- books：书籍元信息
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    file_name TEXT NOT NULL,
    total_chapters INTEGER DEFAULT 0,
    total_sections INTEGER DEFAULT 0,
    cover_emoji TEXT DEFAULT '📖',
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'processing',  -- processing | ready | error
    error_message TEXT DEFAULT '',
    raw_text TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- chapters：章节
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_index INTEGER NOT NULL,   -- 从 0 开始
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL
);

-- sections：小节
CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    section_index INTEGER NOT NULL,       -- 全书序号，从 0 开始
    section_in_chapter INTEGER NOT NULL,  -- 章节内序号
    raw_text TEXT NOT NULL,
    content_json TEXT,                    -- AI 生成的结构化内容（JSON 字符串）
    status TEXT DEFAULT 'pending',        -- pending | processing | ready | error
    created_at TEXT DEFAULT (datetime('now'))
);

-- reading_progress：阅读进度
CREATE TABLE IF NOT EXISTS reading_progress (
    book_id TEXT PRIMARY KEY REFERENCES books(id) ON DELETE CASCADE,
    current_section_index INTEGER DEFAULT 0,
    current_position TEXT DEFAULT 'start',  -- start | card:N | quiz | reflection | complete
    last_read_at TEXT DEFAULT (datetime('now'))
);

-- quiz_results：测验记录
CREATE TABLE IF NOT EXISTS quiz_results (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    quiz_type TEXT NOT NULL,          -- inline | section
    question_index INTEGER NOT NULL,
    user_answer INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,      -- 0 或 1
    answered_at TEXT DEFAULT (datetime('now'))
);

-- insight_cards：洞见卡片（Phase 2 用，Phase 1 先建表）
CREATE TABLE IF NOT EXISTS insight_cards (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    book_id TEXT NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    next_review_at TEXT,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id, chapter_index);
CREATE INDEX IF NOT EXISTS idx_sections_book ON sections(book_id, section_index);
CREATE INDEX IF NOT EXISTS idx_sections_chapter ON sections(chapter_id, section_in_chapter);
CREATE INDEX IF NOT EXISTS idx_quiz_section ON quiz_results(section_id);
CREATE INDEX IF NOT EXISTS idx_insight_book ON insight_cards(book_id);
CREATE INDEX IF NOT EXISTS idx_insight_review ON insight_cards(next_review_at);
```

### content_json 的完整结构

存储在 sections.content_json 中，是 JSON 字符串：

```json
{
  "hook": "一个引发好奇心的问题或反直觉事实",
  "content_cards": [
    {
      "type": "concept",
      "content": "核心概念阐述，2-4句话",
      "emoji": "🧠"
    },
    {
      "type": "example",
      "content": "一个生活化的例子来说明上面的概念",
      "emoji": "💡"
    },
    {
      "type": "quote",
      "content": "书中原文的关键句子",
      "emoji": "📖"
    },
    {
      "type": "comparison",
      "content": "很多人以为是A，其实是B",
      "emoji": "⚖️"
    },
    {
      "type": "highlight",
      "content": "特别重要的结论或洞见",
      "emoji": "⭐"
    }
  ],
  "inline_quiz": {
    "position": 3,
    "question": "根据刚才的内容，以下哪个说法是正确的？",
    "options": ["选项A", "选项B", "选项C"],
    "correct": 0,
    "explanation": "答对/答错的解释"
  },
  "section_quiz": [
    {
      "question": "这一节的核心观点是什么？",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct": 2,
      "explanation": "解释为什么是这个答案"
    },
    {
      "question": "第二道题",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct": 1,
      "explanation": "解释"
    }
  ],
  "reflection": "一个连接现实生活的开放式问题",
  "insight_cards": [
    {
      "front": "关键词/概念名",
      "back": "用一两句话解释这个概念"
    }
  ],
  "bridge": "引向下一节的过渡文案，制造好奇心",
  "recap": "本节核心摘要，2-3句话"
}
```

---

## 六、后端 API 设计

基地址：`/api`（前端通过 Vite 代理到 `http://localhost:8000/api`）

### 书籍相关

```
POST   /api/books/upload
  请求：multipart/form-data，字段名 file，仅接受 .pdf
  限制：文件大小不超过 50MB
  响应：{ book_id, title, status: "processing" }
  行为：提取文本 → 存入数据库 → 启动 BackgroundTask 处理

GET    /api/books
  响应：[{ id, title, author, cover_emoji, description, status,
           total_sections, read_sections, last_read_at }]
  说明：read_sections 和 last_read_at 通过 JOIN reading_progress 获取

GET    /api/books/{book_id}
  响应：{ ...书籍全部字段,
          chapters: [{ id, title, section_count, sections: [{ id, section_index, status }] }] }
  说明：chapters 含各章节的小节列表，用于总览页展示目录

DELETE /api/books/{book_id}
  行为：级联删除书籍、章节、小节、进度、测验记录、洞见卡片
  响应：{ success: true }
```

### 小节相关

```
GET    /api/books/{book_id}/sections/{section_index}
  响应（ready）：{ id, section_index, total_sections, chapter_title,
                   content_json（已解析为对象）, status, has_next, has_prev }
  响应（pending）：触发该小节的 AI 处理，返回 HTTP 202 + { status: "processing" }
  响应（processing）：返回 HTTP 202 + { status: "processing" }
  响应（error）：返回 HTTP 500 + { status: "error", message: "..." }
  附加行为：当触发处理时，同时预处理下一节（section_index + 1），减少用户等待

GET    /api/books/{book_id}/sections/{section_index}/status
  响应：{ status: "pending" | "processing" | "ready" | "error" }
  用途：前端轮询，每 2 秒调用一次
```

### 进度相关

```
PUT    /api/progress/{book_id}
  请求：{ section_index: number, position: string }
  响应：{ success: true }
  说明：position 格式为 "start" | "card:5" | "quiz" | "reflection" | "complete"

GET    /api/progress/{book_id}
  响应：{ current_section_index, current_position, last_read_at }
  说明：如果没有进度记录，返回 { current_section_index: 0, current_position: "start" }
```

### 测验相关

```
POST   /api/quiz/submit
  请求：{ section_id, quiz_type: "inline"|"section", question_index, user_answer }
  响应：{ is_correct: boolean, correct_answer: number, explanation: string }
  行为：查找 content_json 中对应的题目，比较答案，存入 quiz_results
```

---

## 七、DeepSeek API 调用层

### 核心调用封装（ai_service.py 参考实现）

```python
import json
import time
from openai import OpenAI
from config import DEEPSEEK_API_KEY

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def call_deepseek(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = 3,
    temperature: float = 0.7
) -> dict | str:
    """
    调用 DeepSeek API 的统一入口。
    expect_json=True 时强制 JSON 输出并自动解析。
    含指数退避重试。
    """
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": 4096,
            }
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            if expect_json:
                # 清理可能的 markdown 代码块包裹
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]  # 去掉第一行
                    cleaned = cleaned.rsplit("```", 1)[0]  # 去掉最后的 ```
                return json.loads(cleaned)
            else:
                return content

        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise ValueError(f"AI 返回的 JSON 解析失败（重试 {max_retries} 次后）: {e}")

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
```

### 关键设计说明

- DeepSeek API 兼容 OpenAI SDK 格式，用 `openai` Python 包即可调用
- `response_format={"type": "json_object"}` 让 DeepSeek 强制输出合法 JSON
- 额外做了 markdown 代码块清理，作为 JSON 解析的保底措施
- 指数退避重试处理网络波动和偶发错误

---

## 八、AI Prompt 设计

### Prompt 1：书籍信息提取

调用时机：PDF 上传后，用书籍前 3000 字 + 文件名调用。

```python
BOOK_INFO_SYSTEM = "你是一个阅读顾问。你的任务是从书籍内容中提取关键信息。只返回 JSON，不要有其他任何文字。"

BOOK_INFO_USER = """根据以下书籍的开头内容和文件名，提取书籍信息。

文件名：{file_name}

书籍开头内容：
{first_3000_chars}

返回以下 JSON：
{{
  "title": "书名（如果能从内容中识别出来就用内容中的，否则从文件名推断）",
  "author": "作者（如无法确定则为空字符串）",
  "cover_emoji": "一个最能代表这本书主题的 emoji",
  "description": "用一句吸引人的话介绍这本书（像朋友推荐一样，不超过50字）"
}}"""
```

### Prompt 2：章节识别

调用时机：提取书籍信息后。发送全书文本（DeepSeek 支持 64K+ tokens 上下文）。

对于超长书籍（超过 10 万字），分两步：先发前 1 万字让 AI 识别章节标题模式，再用正则在全文中匹配。

```python
CHAPTER_SPLIT_SYSTEM = "你是一个文本结构分析专家。只返回 JSON，不要有其他任何文字。"

CHAPTER_SPLIT_USER = """以下是一本中文书籍的完整文本。请识别其章节结构。

规则：
1. 识别所有章节的标题。常见格式：第X章、第X节、Chapter X、Part X、数字+标题 等
2. 如果没有明确章节划分，按主题自然转换划分，每章 3000-8000 字
3. 忽略目录页、版权页、序言、前言、附录、参考文献等非正文内容
4. 对每个章节，提供标题和该章节第一句完整的话（用于在原文中精确定位）

书籍文本：
{full_text}

返回 JSON：
{{
  "chapters": [
    {{
      "title": "章节标题",
      "first_sentence": "该章节正文的第一句完整的话（必须与原文完全一致，一个字都不能改）"
    }}
  ]
}}"""
```

**定位算法（在 processing.py 中实现）：**

```python
def split_text_by_chapters(full_text: str, chapters_info: list[dict]) -> list[dict]:
    """
    根据 AI 返回的 first_sentence 在原文中定位章节边界。
    """
    chapter_texts = []
    positions = []

    for ch in chapters_info:
        pos = full_text.find(ch["first_sentence"])
        if pos == -1:
            # 容错：尝试模糊匹配（取前15个字搜索）
            short = ch["first_sentence"][:15]
            pos = full_text.find(short)
        if pos != -1:
            positions.append({"title": ch["title"], "start": pos})

    # 按位置排序
    positions.sort(key=lambda x: x["start"])

    # 切分文本
    for i, p in enumerate(positions):
        start = p["start"]
        end = positions[i + 1]["start"] if i + 1 < len(positions) else len(full_text)
        chapter_texts.append({
            "title": p["title"],
            "text": full_text[start:end].strip()
        })

    return chapter_texts
```

### 小节拆分（纯算法，不调用 AI）

调用时机：对每个章节执行。这一步不需要 AI，用算法按段落边界切分即可，省钱且快。

```python
def split_chapter_into_sections(chapter_text: str, min_chars=800, max_chars=1500) -> list[str]:
    """
    按段落边界将章节切分为小节，每节 800-1500 字。
    """
    paragraphs = [p.strip() for p in chapter_text.split('\n') if p.strip()]
    sections = []
    current_section = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)

        # 如果当前小节加上新段落超过最大值，且当前已达到最小值 → 切分
        if current_length + para_len > max_chars and current_length >= min_chars:
            sections.append('\n\n'.join(current_section))
            current_section = [para]
            current_length = para_len
        else:
            current_section.append(para)
            current_length += para_len

    # 处理最后一节
    if current_section:
        last_text = '\n\n'.join(current_section)
        # 如果最后一节太短且前面有小节，合并到前一节
        if current_length < min_chars // 2 and sections:
            sections[-1] += '\n\n' + last_text
        else:
            sections.append(last_text)

    return sections
```

### Prompt 3：小节内容生成（最关键的 Prompt）

调用时机：对每个小节调用。这是 AI token 消耗最多的步骤，也是产品质量的核心。

```python
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
1-2 句话的开场，策略任选其一：
- 抛出一个反直觉的事实
- 提出一个读者可能关心的问题
- 描述一个引人入胜的场景
- 制造认知缺口——让读者意识到自己不知道某件重要的事
禁止写成教科书导读（"本节将介绍..."），要像朋友聊天一样自然。

### content_cards（内容卡片数组）
将本节内容拆解为 5-10 张卡片。规则：
- 每张卡片只承载一个小观点（2-4 句话）
- 用口语化、易懂的方式重新表达（不是复制原文）
- type 类型：
  - concept：核心概念阐述
  - example：生活化的例子（原文没有好例子就创造一个）
  - quote：书中特别精彩的原句
  - comparison：对比或纠正常见误解（"很多人以为…其实…"）
  - highlight：特别重要的结论（本节最关键的 1-2 个点）
- 每张卡片选择一个贴切的 emoji
- concept 和 example 应交替出现
- 至少包含 1 张 example 和 1 张 highlight
- 语气像在跟朋友解释，不要学术腔

### inline_quiz（内嵌互动，在卡片流中间）
- position：在第几张 content_card 之后插入（通常第 3-5 张）
- 一道选择题（3 个选项），考察理解而非记忆
- 提供简明的解释

### section_quiz（小节结束后的测验，2 道题）
- 第 1 题偏理解：考察对核心概念的准确把握
- 第 2 题偏应用：给一个场景，让读者用学到的知识判断
- 每题 4 个选项，提供解释

### reflection（反思问题）
一个连接现实生活的开放式问题，让读者把新知识和自身经历联系起来。

### insight_cards（洞见卡片，1-2 张）
- front：关键概念名或关键问题（5-10 个字）
- back：清晰解释（1-2 句话）

### bridge（桥接下一节）
1-2 句话，制造「且听下回分解」的期待感。
如果 is_last_section 为 true，写一句全书收尾总结。

### recap（回顾摘要）
本节核心内容的浓缩，2-3 句话。

## 输出 JSON 格式
{{
  "hook": "",
  "content_cards": [
    {{ "type": "concept|example|quote|comparison|highlight", "content": "", "emoji": "" }}
  ],
  "inline_quiz": {{
    "position": 0,
    "question": "",
    "options": ["", "", ""],
    "correct": 0,
    "explanation": ""
  }},
  "section_quiz": [
    {{ "question": "", "options": ["", "", "", ""], "correct": 0, "explanation": "" }}
  ],
  "reflection": "",
  "insight_cards": [
    {{ "front": "", "back": "" }}
  ],
  "bridge": "",
  "recap": ""
}}"""
```

---

## 九、后端处理管线

### 书籍上传处理流程

```
用户上传 PDF
    │
    ▼
[同步] 1. PyMuPDF 提取全文
    │  - 逐页提取文本
    │  - 清除页眉页脚（识别每页重复出现的行并删除）
    │  - 清除页码（匹配 "- 12 -"、"12"、"第12页" 等独立行）
    │  - 合并被分页打断的段落
    │  - 规范化空白
    │
    ▼
[同步] 2. 生成 book_id，存入 books 表（status="processing"）
    │  立即返回响应给前端：{ book_id, title: 文件名, status: "processing" }
    │
    ▼
[BackgroundTask] 3. 调用 DeepSeek → 提取书籍信息
    │  更新 books 表（title, author, cover_emoji, description）
    │
    ▼
[BackgroundTask] 4. 调用 DeepSeek → 识别章节结构
    │  用 first_sentence 定位算法从原文切分章节
    │  存入 chapters 表
    │
    ▼
[BackgroundTask] 5. 对每个章节 → 算法切分小节（不调用 AI）
    │  存入 sections 表，content_json=NULL, status="pending"
    │  更新 books.total_chapters 和 books.total_sections
    │
    ▼
[BackgroundTask] 6. 对前 3 个小节 → 调用 DeepSeek 生成结构化内容
    │  存入 sections.content_json，更新 status="ready"
    │
    ▼
[BackgroundTask] 7. 更新 books.status = "ready"
    │  此时用户可以开始阅读
    │
    ▼
剩余小节：用户翻到时按需处理（见下方流程）
```

### 小节按需处理流程

```
前端请求 GET /api/books/{id}/sections/{index}
    │
    ▼
查询 sections 表
    │
    ├── status = "ready"
    │   → 直接返回 200 + content_json
    │
    ├── status = "processing"
    │   → 返回 202 + { status: "processing" }
    │   → 前端每 2 秒轮询 /status 端点
    │
    └── status = "pending"
        → 更新 status = "processing"
        → 启动 BackgroundTask：
        │   1. 获取前一节的 recap（如果有）
        │   2. 调用 DeepSeek 生成内容
        │   3. 存入 content_json，status = "ready"
        │   4. 同时检查下一节（index+1），如果是 pending 也开始处理（预加载）
        → 返回 202 + { status: "processing" }
```

### PDF 文本清洗细节

```python
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 提取并清洗文本"""
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()

    # 识别页眉页脚：统计每页首行/末行，超过 50% 页面重复的视为页眉页脚
    if len(pages) > 5:
        first_lines = [p.split('\n')[0].strip() for p in pages if p.strip()]
        last_lines = [p.strip().split('\n')[-1].strip() for p in pages if p.strip()]
        from collections import Counter
        header_candidates = {line for line, count in Counter(first_lines).items()
                           if count > len(pages) * 0.5 and line}
        footer_candidates = {line for line, count in Counter(last_lines).items()
                           if count > len(pages) * 0.5 and line}

        cleaned_pages = []
        for page_text in pages:
            lines = page_text.split('\n')
            if lines and lines[0].strip() in header_candidates:
                lines = lines[1:]
            if lines and lines[-1].strip() in footer_candidates:
                lines = lines[:-1]
            cleaned_pages.append('\n'.join(lines))
        pages = cleaned_pages

    full_text = '\n'.join(pages)

    # 清除独立的页码行
    import re
    full_text = re.sub(r'\n\s*[-—]?\s*\d+\s*[-—]?\s*\n', '\n', full_text)
    full_text = re.sub(r'\n\s*第\s*\d+\s*页\s*\n', '\n', full_text)

    # 规范化空白
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    full_text = re.sub(r' {2,}', ' ', full_text)

    return full_text.strip()
```

---

## 十、前端页面设计

### 设计方向

整体风格：温暖、轻松、不像教育软件。像一个精心设计的阅读 app，不像课堂。

色彩方案：
- 背景：暖白 #FAFAF8
- 卡片背景：纯白 #FFFFFF
- 主色调：深蓝 #2B4C7E（沉稳、专注）
- 强调色：琥珀 #E8A838（温暖、活力，用于钩子和成就）
- 成功色：翠绿 #4CAF78（测验答对）
- 错误色：#E85D4A（测验答错）
- 辅助背景：#F0F0EC（分隔区域）
- 正文色：#1A1A1A
- 次要文字：#666666

字体栈：
```css
font-family: -apple-system, "PingFang SC", "Hiragino Sans GB",
             "Microsoft YaHei", "Helvetica Neue", sans-serif;
```
- 卡片正文：16px, line-height: 1.8（中文阅读最舒适）
- 标题：20-24px, font-weight: 600

### 页面 1：书架页（Bookshelf）

路由：`/`

```
┌──────────────────────────────────────┐
│  📚 读伴 BookBuddy                    │
├──────────────────────────────────────┤
│                                      │
│  ┌──────────┐  ┌──────────┐          │
│  │  📘      │  │  ➕      │          │
│  │ 思考快与慢│  │          │          │
│  │ ████░░░  │  │  上传新书 │          │
│  │ 进度 60% │  │          │          │
│  └──────────┘  └──────────┘          │
│                                      │
└──────────────────────────────────────┘
```

功能要素：
- 书籍卡片网格（封面 = 大 emoji + 书名 + 作者）
- 每张卡片：进度条 + 上次阅读时间
- 上传区域：虚线框 + 拖放 + 点击选择，仅接受 .pdf
- 处理中的书：显示加载动画 + "正在解析书籍..."
- 空状态："上传你的第一本书，开始阅读之旅 📖"
- 点击书籍 → 进入总览页

### 页面 2：书籍总览页（BookOverview）

路由：`/book/:bookId`

```
┌──────────────────────────────────────┐
│  ← 返回书架                          │
├──────────────────────────────────────┤
│  📘 思考，快与慢                      │
│  丹尼尔·卡尼曼                        │
│  "这本书要解决一个你每天都在面对的     │
│   问题——你以为自己在理性思考..."      │
│                                      │
│  ■■■■■■░░░░ 60%（12/20 节）         │
│  [  继续阅读 →  ]                    │
│                                      │
│  章节目录                             │
│  ┌────────────────────────────────┐  │
│  │ ▸ 第一章 两个系统       3/3 ✅  │  │
│  │ ▸ 第二章 注意力与努力   2/4    │  │
│  │ ▸ 第三章 惰性思维       0/3    │  │
│  │ ...                            │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

- 「继续阅读」跳转到上次未完成的小节
- 章节目录可折叠展开，显示每个小节的完成状态
- 点击任一小节可直接跳转阅读

### 页面 3：阅读页（Reader）← 核心页面

路由：`/book/:bookId/read/:sectionIndex`

整体布局：单列居中，max-width 640px，垂直滚动卡片流。

```
┌──────────────────────────────────────┐
│  ← 第一章 · 第2节       3/20 ██░░░  │
├──────────────────────────────────────┤
│                                      │
│  ┌─ 🎣 ──────────────────────────┐  │
│  │ 你知道吗？你现在做的 90% 的    │  │
│  │ 决定，其实不是「你」在做。     │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ 🧠 概念 ─────────────────────┐  │
│  │ 卡尼曼把人的思维分成两个系统。 │  │
│  │ 系统1 是快速、自动、直觉的...  │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ 💡 例子 ─────────────────────┐  │
│  │ 想想你今天早上的通勤路线。     │  │
│  │ 你有「思考」过怎么走吗？...    │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ 🤔 想一想 ───────────────────┐  │
│  │ 当你在超市选择一个品牌时，     │  │
│  │ 这更可能是哪个系统在工作？     │  │
│  │  ○ 系统1（快速直觉）          │  │
│  │  ○ 系统2（慢速理性）          │  │
│  │  ○ 两者共同协作                │  │
│  └────────────────────────────────┘  │
│                                      │
│  ... 更多内容卡片 ...                │
│                                      │
│  ┌─ 📝 小测验 ───────────────────┐  │
│  │ 恭喜读完这一节！检验下收获 ✨   │  │
│  │ 第 1/2 题                     │  │
│  │ 以下哪个最准确地描述了...？   │  │
│  │  ○ A  ○ B  ○ C  ○ D          │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ 💭 思考题 ───────────────────┐  │
│  │ 想想你最近做的一个购物决定...  │  │
│  │       [ 思考完了，继续 → ]     │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ ⭐ 知识卡片 ─────────────────┐  │
│  │  ┌────────┐  ┌────────┐       │  │
│  │  │系统1   │  │系统2   │       │  │
│  │  │（点击  │  │（点击  │       │  │
│  │  │ 翻转） │  │ 翻转） │       │  │
│  │  └────────┘  └────────┘       │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌─ 🌉 下一节预告 ──────────────┐  │
│  │ 你以为系统1只是帮你做小事？   │  │
│  │ 接下来你会发现，它在你人生     │  │
│  │ 最重大的决定中也在暗中操控...  │  │
│  │       [  继续下一节 →  ]      │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 卡片视觉样式对照表

每种卡片通过左边框颜色（4px 宽）和浅色背景区分：

| 卡片类型 | 左边框色 | 背景色 | 角标 emoji |
|----------|---------|--------|-----------|
| hook（钩子） | #E8A838 琥珀 | #FFF9F0 | 🎣 |
| concept（概念） | #2B4C7E 深蓝 | #FFFFFF | 🧠 |
| example（例子） | #4CAF78 翠绿 | #F8FFF8 | 💡 |
| quote（引用） | #999999 灰色 | #F8F8F6 | 📖 |
| comparison（对比） | #7C5CBF 紫色 | #F8F5FF | ⚖️ |
| highlight（要点） | #E85D4A 红色 | #FFF5F5 | ⭐ |
| inline_quiz（互动） | #E8A838 琥珀 | #FFF9F0 | 🤔 |
| section_quiz（测验） | #2B4C7E 深蓝 | #F0F4FF | 📝 |
| reflection（反思） | #4CAF78 翠绿 | #F0FFF4 | 💭 |
| bridge（桥接） | #E8A838 琥珀 | #FFF9F0 | 🌉 |

### 关键交互细节

**测验卡片交互（QuizCard）：**
1. 显示题目 + 选项（未选状态）
2. 点击选项 → 高亮选中
3. 点击「确认」按钮
4. 答对：选中项背景变绿 + ✅ + 显示 "答对了！" + 解释文字
5. 答错：选中项背景变红 + ❌ + 正确选项背景变绿 + 显示解释
6. 点击「继续」→ 下一张卡片

**洞见翻转卡片（InsightCard）：**
1. 默认显示正面（关键词，大字居中）
2. 点击 → CSS 3D 翻转动画 → 显示反面（解释）
3. 再点击 → 翻回正面

**进度自动保存：**
- 用户滚动到新卡片时，通过 IntersectionObserver 检测，自动调用 PUT /api/progress
- 离开页面（beforeunload）时保存一次
- 重新进入时恢复到 last position

**AI 处理中等待态：**
- 居中显示："📖 正在为你准备这一节的阅读体验..."
- 柔和的脉冲动画（不是转圈 spinner）
- 每 2 秒轮询 status 端点
- ready 后自动渲染内容，无需手动刷新

---

## 十一、实施步骤（按顺序执行）

以下是 code agent 的执行清单，每步有明确的验证标准：

### Step 1：项目初始化
- 创建完整目录结构
- 后端：创建 FastAPI 项目，安装依赖，配置 CORS
- 前端：用 `npm create vite@latest` 初始化 React 项目，安装 Tailwind + React Router + Zustand + Axios，配置 Vite 代理
- 编写 start.sh
- **验证：** 前后端都能启动，前端能通过 /api 代理调通后端的 `GET /api/health` → `{ status: "ok" }`

### Step 2：数据库 + 数据模型
- 实现 config.py（读取 .env）
- 实现 database.py（建表 SQL、get_connection 函数）
- 实现 models.py（Pydantic 模型）
- **验证：** 后端启动时自动在 data/ 下创建 bookbuddy.db，所有表已建立

### Step 3：PDF 上传 + 文本提取
- 实现 pdf_service.py（extract_text_from_pdf 函数）
- 实现 POST /api/books/upload（接收文件、提取文本、存 books 表、返回 book_id）
- 实现 GET /api/books（返回书籍列表）
- 前端：实现 Bookshelf 页 + UploadArea 组件 + BookCard 组件
- **验证：** 上传 PDF → 后端提取文本存入数据库 → 前端显示书籍卡片（此时 status=processing）

### Step 4：AI 处理管线
- 实现 ai_service.py（call_deepseek 函数，含重试和 JSON 解析）
- 实现三个 prompt 模板文件
- 实现 processing.py（完整管线：书籍信息提取 → 章节拆分 → 小节拆分 → 前 3 节内容生成）
- 在 books router 中用 BackgroundTasks 调用 processing
- **验证：** 上传 PDF → 等待 1-2 分钟 → books.status 变为 ready → sections 表中前 3 条 status=ready 且 content_json 非空

### Step 5：小节 API + 按需处理
- 实现 GET /api/books/{id}/sections/{index}（含按需触发处理 + 预加载下一节）
- 实现 GET /api/books/{id}/sections/{index}/status
- **验证：** 请求第 4 节（status=pending）→ 返回 202 → 几秒后轮询 status 变为 ready → 再次请求返回完整 content_json

### Step 6：阅读页（核心 UI）
- 实现 Reader.jsx 页面整体框架（顶栏 + 进度条 + 卡片流容器）
- 逐个实现所有卡片组件：HookCard → ContentCard → QuizCard → ReflectionCard → InsightCard → BridgeCard
- 在 Reader 中组装卡片流：根据 content_json 按顺序渲染，inline_quiz 插入到 content_cards 的 position 位置
- 实现测验交互逻辑（选择 → 确认 → 反馈）
- 实现「处理中」等待态 + 轮询
- 实现「继续下一节」按钮（路由跳转到 sectionIndex+1）
- **验证：** 能完整走通一个小节的全部阅读流程

### Step 7：进度与导航
- 实现 PUT/GET /api/progress/{book_id}
- 实现 POST /api/quiz/submit
- 前端：IntersectionObserver 自动保存进度 + beforeunload 保存
- 前端：进入 Reader 页时恢复到 last position
- 实现 BookOverview 页（书籍信息 + 章节目录 + 继续阅读按钮）
- 实现 GET /api/books/{book_id}（含章节小节详情）
- **验证：** 读到第 3 节中间 → 关闭浏览器 → 重新打开 → 点击继续阅读 → 恢复到第 3 节

### Step 8：串联打磨
- 所有页面间的导航链路完善（书架 ↔ 总览 ↔ 阅读）
- 错误处理：AI 返回格式异常时的容错、PDF 无法提取时的提示、网络错误提示
- 各种加载状态和空状态的 UI
- DELETE 书籍功能（带确认弹窗）
- 响应式：桌面（max-width 容器居中）和移动端（全宽）都可用
- 整体 UI 一致性检查和微调
- **验证：** 完整跑通：上传 → 等待处理 → 开始阅读 → 翻过多个小节 → 关闭重开 → 继续阅读 → 读完全书

---

## 十二、配置与启动

### 环境变量

```bash
# backend/.env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DATABASE_PATH=./data/bookbuddy.db
MAX_UPLOAD_SIZE_MB=50
```

### 依赖清单

**backend/requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.12
pymupdf==1.24.10
openai==1.52.0
python-dotenv==1.0.1
pydantic==2.9.0
```

注意：
- 用 `pymupdf` 而非 `PyMuPDF`（PyPI 上的新包名）
- 用 `openai` SDK 调用 DeepSeek（兼容接口）
- 不需要 aiosqlite，用标准库 sqlite3 即可
- `uvicorn[standard]` 包含 websockets 等可选依赖

**frontend/package.json 依赖：**
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vite": "^5.4.0"
  }
}
```

### 启动脚本

```bash
#!/bin/bash
# start.sh — 一键启动 BookBuddy

echo "🚀 启动 BookBuddy..."

# 检查 .env
if [ ! -f backend/.env ]; then
    echo "❌ 请先创建 backend/.env 文件并填入 DEEPSEEK_API_KEY"
    exit 1
fi

# 启动后端
echo "📦 启动后端..."
cd backend
pip install -r requirements.txt -q
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# 启动前端
echo "🎨 启动前端..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ BookBuddy 已启动！"
echo "   打开浏览器访问 → http://localhost:5173"
echo ""
echo "   按 Ctrl+C 停止所有服务"

# 捕获退出信号，同时关闭前后端
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
```

---

## 十三、成本估算

使用 DeepSeek API (deepseek-chat) 处理一本典型中文非虚构书（约 6-8 万字，约 40-60 个小节）：

| 处理步骤 | 调用次数 | 预估 Token 消耗 |
|----------|---------|----------------|
| 书籍信息提取 | 1 次 | ~3K |
| 章节识别 | 1 次 | ~20K（发送全文） |
| 小节拆分 | 0 次 | 纯算法，不消耗 token |
| 小节内容生成 | ~50 次 | ~200K（每次 ~4K） |
| **合计** | ~52 次 | **~220K tokens** |

DeepSeek 定价（deepseek-chat）：
- 输入：¥1/百万 tokens（缓存命中 ¥0.1/百万）
- 输出：¥2/百万 tokens

**每本书成本约 ¥0.5 - 1.5 元**

对比参考：
| | DeepSeek | Claude Sonnet | GPT-4o |
|--|---------|---------------|--------|
| 每本书成本 | ¥0.5-1.5 | ¥15-30 | ¥10-20 |

DeepSeek 的成本优势让你可以大量测试和迭代而不心疼。

---

## 十四、错误处理策略

### AI 调用失败
- 网络超时/API 报错：指数退避重试 3 次
- JSON 解析失败：重试 3 次（换一次 temperature 为 0.3 再试）
- 重试全部失败：sections.status 设为 "error"，前端显示 "这一节处理失败了，点击重试"
- 重试按钮：前端调用 sections API 时传 `?force=true`，后端重置 status 为 pending 并重新处理

### PDF 提取失败
- 文件不是 PDF / 损坏：上传时返回 400 + 错误信息
- 提取出的文本太少（<500 字）：返回 400 + "这本 PDF 可能是扫描版或图片版，暂不支持"
- 文本太长（>50 万字）：返回 400 + "这本书太长了，建议分册上传"

### 前端错误处理
- API 请求失败：toast 提示 + 可选重试
- 页面未找到（错误的 bookId/sectionIndex）：重定向到书架页
- 网络断开：离线提示条

---

## 十五、已知限制与后续演进

### Phase 1 已知限制
- 仅支持 PDF（不支持 EPUB、TXT、MOBI）
- 扫描版/图片版 PDF 无法处理（无 OCR）
- 章节识别对排版不规范的书可能不准确
- AI 处理每节约 3-8 秒，首次上传需等待 1-2 分钟
- 无导出功能
- 单机使用，数据不同步

### Phase 2/3 演进方向
- 间隔复习系统（SM-2 算法）
- AI 聊天伴读（基于当前小节上下文）
- 前情回顾机制
- 支持 EPUB 和 TXT 格式
- 自定义偏好（卡片密度、互动频率、内容深浅度）
- 阅读数据统计可视化
- 浏览器通知提醒复习
- 未来可选接入其他模型（Claude、GPT 等），只需修改 config 中的 base_url 和 model 名
