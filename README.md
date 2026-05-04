# Paper Lens

A Claude Code skill for reading, understanding, and presenting academic papers.

一个用于论文阅读、深度理解和汇报准备的 Claude Code Skill。

<!-- 在这里插入一张主截图，展示整体效果 -->
<!-- ![Paper Lens Demo](docs/screenshots/hero.png) -->

---

## Features / 功能概览

| Mode / 模式 | Purpose / 用途 | Time / 耗时 | Interaction / 交互 |
|---|---|---|---|
| **Speed Read / 速览** | Quick digest / 快速消化，判断是否值得深读 | ~5 min | One-shot / 一次性输出 |
| **Deep Learn / 学习** | In-depth study / 大白话深度理解，边学边存 | 20-40 min | Multi-turn / 多轮交互 |
| **Present / 展示** | Slide preparation / 准备演讲 slides | 15-30 min | Page-by-page / 逐页讨论 |
| **Batch Search / 批量检索** | Search by topic / 按主题搜索论文 | 3-5 min | Table + select / 表格 + 选择 |
| **Batch Download / 批量下载** | Download multiple papers / 粘贴链接批量下载 | 1-3 min | Auto-dedup / 自动去重 |

---

## Quick Start / 快速开始

### Install / 安装

The CLI skill is a single folder you copy. The optional Web UI lives in the same repo — see [Web UI](#web-ui-optional--网页界面可选) below.

CLI skill 只是一个文件夹。可选的 Web UI 在同一仓库里——见下方 [Web UI](#web-ui-optional--网页界面可选) 章节。

**Project-level (recommended) / 项目级安装（推荐）：**

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens <your-project>/.claude/skills/
```

**User-level (global) / 用户级安装（全局可用）：**

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens ~/.claude/skills/
```

> Note: copying just the skill folder gives you the CLI experience. To use the browser UI, keep the full repo and follow the [Web UI](#web-ui-optional--网页界面可选) instructions.
>
> 注意：只拷 skill 文件夹只会得到 CLI 模式。如果想用浏览器界面，请保留整个仓库并按 [Web UI](#web-ui-optional--网页界面可选) 章节启动。

### Requirements / 依赖

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (latest version)
- Python 3.8+ with [PyMuPDF](https://pymupdf.readthedocs.io/)

```bash
pip install pymupdf
```

### Usage / 使用

Just talk to Claude Code: / 在 Claude Code 中直接对话：

```
> Help me read this paper: https://arxiv.org/pdf/1706.03762
> 帮我读这篇论文：https://arxiv.org/pdf/1706.03762

> Search for LLM agent evaluation papers
> 搜索 LLM agent evaluation 相关论文

> Download these: 2501.12948 2309.12288 2401.05566
> 帮我下载这些论文：2501.12948 2309.12288 2401.05566
```

Claude will auto-detect your intent and enter the matching mode.

Claude 会自动识别意图并进入对应模式。

---

## Modes in Detail / 模式详解

### Speed Read / 速览模式

5-minute digest of any paper. Outputs an info card, TL;DR, key innovation, methodology, results, and discussion questions.

5 分钟快速消化一篇论文。输出基本信息卡片、TL;DR、核心创新、主要方法、实验结果和深度问答。

<!-- 速览模式截图 -->
<!-- ![Speed Read](docs/screenshots/speed-read.png) -->

**Trigger**: "speed read this paper" / 「帮我速览这篇论文」

---

### Deep Learn / 学习模式

20-40 minute interactive deep dive. All concepts explained in plain language — like explaining to a smart friend outside the field.

20-40 分钟交互式深度学习。所有概念用「大白话」解释——想象在给一个聪明但非本领域的朋友讲解。

<!-- 学习模式截图 -->
<!-- ![Deep Learn](docs/screenshots/deep-learn.png) -->

Key features / 核心特性：

- **Incremental saving / 边学边存** — Progress auto-saved after each step / 每步完成后自动追加到笔记文件
- **Interactive term selection / 术语交互选择** — Choose which terms to study via grouped multi-select / 分组多选想深入的术语
- **Dual-layer formulas / 双层公式** — ASCII in terminal, LaTeX in saved files / 终端 ASCII，文件 LaTeX
- **Resume from checkpoint / 断点恢复** — Continue from where you left off / 中断后可从上次进度继续

**Trigger**: "help me learn this paper" / 「帮我学习这篇论文」

---

### Present / 展示模式

Prepare slide content for a paper talk in 15-30 minutes.

15-30 分钟准备一场论文汇报的 slides 内容。

<!-- 展示模式截图 -->
<!-- ![Present](docs/screenshots/present.png) -->

Key features / 核心特性：

- **Figure mapping / 图表映射** — Auto-identify paper figures from extracted images / 自动识别论文原图并重命名
- **Page-by-page discussion / 逐页讨论** — Each slide discussed with Speaker Notes / 每页含演讲备注
- **Self-contained HTML / 图片嵌入** — Base64-embedded images, no external dependencies / base64 编码，完全自包含

**Trigger**: "prepare slides for this paper" / 「帮我准备 slides」

---

### Batch Search / 批量检索

Search papers by topic keywords. Returns a ranked table with links, then offers to download selected papers.

按主题关键词搜索论文，生成带链接的排序表格，支持一键下载。

**Trigger**: "search for X papers" / 「搜索 X 相关论文」

### Batch Download / 批量下载

Paste multiple arXiv URLs or IDs to download in batch. Supports mixed format input with 3-layer dedup.

粘贴多个 arXiv 链接或 ID，自动去重后批量下载。

**Trigger**: paste multiple arXiv links / 直接粘贴多个链接

---

## Mode Chaining / 模式串联

The three reading modes chain seamlessly: / 三种阅读模式可自由串联：

```
Speed Read → Deep Learn → Present
速览（值不值得读？）→ 学习（深度理解）→ 展示（准备汇报）
```

Content from Speed Read is reused by Deep Learn — no repeated work.

速览的内容会被学习模式复用，不会重复劳动。

---

## Output Structure / 输出结构

```
paper-notes/<paper-name>/
├── paper.pdf              # Original PDF / 原始 PDF
├── extracted-text.md      # Full text / 提取的全文
├── images/                # All extracted images / 所有提取图片
├── figures/               # [Present] Selected figures / 筛选后的论文原图
├── speed-read.md          # Speed Read output / 速览输出
├── deep-learn.md          # Deep Learn output / 学习输出（增量保存）
└── slides-content.md      # Present mode output / 展示模式输出
```

## Skill Directory / Skill 目录

```
.claude/skills/paper-lens/
├── SKILL.md                     # Entry point / 主入口
├── references/
│   ├── speed-read.md            # Speed Read instructions / 速览指令
│   ├── deep-learn.md            # Deep Learn instructions / 学习指令
│   ├── present.md               # Present instructions / 展示指令
│   ├── export-pdf.md            # PDF export instructions / PDF 导出指令
│   ├── batch-search.md          # Batch Search instructions / 批量检索指令
│   └── batch-download.md        # Batch Download instructions / 批量下载指令
└── scripts/
    ├── extract_figures.py       # Figure extraction / 图片提取
    └── md_to_pdf.py             # Markdown → PDF / MD 转 PDF
```

---

## Web UI (optional) / 网页界面（可选）

The CLI skill works on its own. If you want a chat-style browser UI, this repo also ships an optional Web UI: a FastAPI backend that wraps the skill, plus a Next.js frontend.

CLI skill 本身已可独立使用。如果你想要浏览器聊天界面，仓库还提供可选的 Web UI：FastAPI 后端封装 skill，Next.js 前端。

```
paper-lens-backend/   # FastAPI server (port 8765) — drives Claude Code CLI via stream-json + MCP
paper-lens-web/       # Next.js app (port 3000)   — chat UI, paper browser
```

### Prerequisites / 先决条件

- Node.js 18+ and npm
- Python 3.8+ with FastAPI dependencies
- Claude Code CLI **must already be logged in** as your user (run `claude` once and complete `/login`)
- Claude Code CLI **必须已登录**当前用户（先跑一次 `claude` 完成 `/login`）

> ⚠️ Do **not** run the backend with `sudo`. The backend spawns a `claude` subprocess that inherits the invoking user's credentials. A `sudo`-spawned subprocess won't find your login token and every chat will fail with `Not logged in · Please run /login`.
>
> ⚠️ **不要**用 `sudo` 启动后端。后端会 spawn `claude` 子进程，并继承调用者的凭证；用 `sudo` 起的子进程拿不到你的登录态，每次对话都会失败。

The backend keeps one long-lived Claude subprocess per browser session. Structured questions in the UI are routed through a tiny local MCP server so the agent truly waits for the user's answer before continuing.

后端会为每个浏览器会话保留一个长寿命 Claude 子进程；结构化选择题通过本地 MCP 小服务中转，确保模型真的等用户回答后再继续。

### Install / 安装

```bash
# Backend
cd paper-lens-backend
pip install -r requirements.txt

# Frontend
cd ../paper-lens-web
cp .env.local.example .env.local   # adjust NEXT_PUBLIC_BACKEND_URL if needed
npm install
```

### Run / 启动

Open two terminals:

```bash
# Terminal 1 — backend
cd paper-lens-backend && python3 server.py

# Terminal 2 — frontend
cd paper-lens-web && npm run dev
```

Then open http://localhost:3000 in your browser.

### Skill auto-detection / Skill 自动探测

When the skill loads, **Phase -1** detects whether ports 3000 and 8765 are alive and tells you the URL — no auto-launch, no auto-open. If the Web UI is running you'll see a one-line hint and can keep using the CLI or switch to the browser as you wish.

Skill 加载时，**Phase -1** 会探测 3000 和 8765 端口，活着就给你一行 URL 提示——不会自动启动也不会自动打开浏览器。

---

## HTML Slides / HTML 演示文稿

Present mode generates `slides-content.md` with figure references. To convert into a self-contained HTML presentation, use a slides tool (e.g., `frontend-slides` for Claude Code) or any Markdown-to-slides tool.

展示模式生成 `slides-content.md`。要转换为 HTML 演示文稿，可以使用 slides 工具（如 Claude Code 的 `frontend-slides` skill）或任何 Markdown 转 slides 工具。

## License

[MIT](LICENSE)
