# BookBuddy

BookBuddy 是一个本地单用户读书应用。上传 PDF 后，后端提取文本并生成章节、小节和互动卡片流，前端提供书架、书籍总览和卡片式阅读体验。

## 启动

```bash
./start.sh
```

首次启动会自动复制 `backend/.env.example` 到 `backend/.env`，默认使用 `AI_MODE=mock`，不需要 API Key 就能跑通完整流程。

访问：

```text
http://localhost:5173
```

后端健康检查：

```text
http://localhost:8000/api/health
```

## 使用 DeepSeek

编辑 `backend/.env`：

```bash
AI_MODE=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

然后重新运行 `./start.sh`。

## 目录

```text
backend/   FastAPI + SQLite + PDF/AI 处理管线
frontend/  React + Vite + Tailwind 前端
start.sh   一键启动脚本
```

