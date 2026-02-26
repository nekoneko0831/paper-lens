# Paper Lens

A Claude Code skill for reading, understanding, and presenting academic papers — through three complementary modes.

## Features

- **Three reading modes**: Speed Read (5 min digest), Deep Learn (interactive study), Present (slide preparation)
- **Smart figure extraction**: Extracts vector graphics and embedded bitmaps from PDF via PyMuPDF, with rectangle merging for split figures and caption-aware cross-column expansion
- **Incremental note-saving**: Deep Learn mode saves progress after each step — you can review notes at any time during the session
- **Interactive term selection**: Choose which terms and formulas to study via grouped multi-select (AskUserQuestion), no tedious multi-step confirmations
- **Dual-layer formulas**: ASCII rendering in the terminal for readability, LaTeX in saved files for precision
- **"Big Whitepaper" explanations**: Complex concepts explained in plain language with analogies, not academic jargon
- **Base64 image embedding**: HTML presentations are fully self-contained — no external image dependencies
- **Mode chaining**: Start with Speed Read, then seamlessly continue to Deep Learn or Present without re-parsing

## Three Modes

| Mode | Purpose | Time | Interaction |
|------|---------|------|-------------|
| **Speed Read** | Quick digest — decide if the paper is worth a deep read | ~5 min | One-shot output |
| **Deep Learn** | Thorough understanding with plain-language explanations | 20-40 min | Multi-turn, interactive |
| **Present** | Prepare slides for a talk or team sharing | 15-30 min | Page-by-page discussion |

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (latest version)
- Python 3.8+ with [PyMuPDF](https://pymupdf.readthedocs.io/) (`pip install pymupdf`)

## Installation

**Project-level** (recommended — skill lives inside your project):

```bash
# Clone the repo, then copy into your project
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens <your-project>/.claude/skills/
```

**User-level** (available across all projects):

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens ~/.claude/skills/
```

The skill directory contains:

```
.claude/skills/paper-lens/
├── SKILL.md                     # Main entry point (mode router + Phase 0 parsing)
├── references/
│   ├── speed-read.md            # Speed Read mode instructions
│   ├── deep-learn.md            # Deep Learn mode instructions
│   ├── present.md               # Present mode instructions
│   └── export-pdf.md            # PDF export instructions
└── scripts/
    ├── extract_figures.py       # Figure extraction script
    └── md_to_pdf.py             # Markdown → PDF conversion script
```

## Usage

1. Open Claude Code in your project directory
2. Provide a paper — local PDF path or arXiv URL
3. Choose a mode when prompted (or say "speed read this paper" / "help me learn this paper" / "prepare slides for this paper")

```
> Help me read this paper: https://arxiv.org/pdf/2511.05459v3
```

Claude will parse the PDF, extract figures, and ask which mode you want.

## Output Structure

Each paper gets its own directory under `paper-notes/`:

```
paper-notes/<paper-name>/
├── paper.pdf              # Original PDF
├── extracted-text.md      # Full text extracted from PDF
├── images/                # All extracted images (vector + bitmap)
├── figures/               # [Present] Selected figures, semantically renamed
├── speed-read.md          # Speed Read output
├── deep-learn.md          # Deep Learn output (incrementally saved)
└── slides-content.md      # Present mode output
```

## Optional: HTML Slide Generation

Paper Lens generates `slides-content.md` with figure references. To convert it into a self-contained HTML presentation with base64-embedded images, use a slides generation skill (e.g., `frontend-slides` for Claude Code) or any Markdown-to-slides tool.

## Examples

See the [examples/](examples/) directory for real outputs from analyzing the SWE-Compass paper (arXiv 2511.05459v3).

## License

[MIT](LICENSE)

---

# Paper Lens（中文说明）

一个用于论文阅读、深度理解和汇报准备的 Claude Code Skill。

## 它能做什么

Paper Lens 提供三种「镜头」来阅读论文，覆盖从快速消化到深度理解再到汇报准备的完整工作流：

### 速览模式（Speed Read）

5 分钟快速消化一篇论文的核心内容。输出包括基本信息卡片、TL;DR、核心创新、主要方法、实验结果和深度问答。适合快速判断一篇论文是否值得深读。

**触发方式**：「帮我速览这篇论文」「快速读一下这个 PDF」

### 学习模式（Deep Learn）

20-40 分钟的交互式深度学习。所有概念用「大白话」解释——想象在给一个聪明但非本领域的朋友讲解。

核心特性：
- **边学边存**：每个步骤完成后自动追加到笔记文件，随时可查看已学内容
- **术语交互选择**：自动提取论文专有术语和领域通用术语，通过分组多选让你选择想深入了解的部分
- **双层公式**：终端显示 ASCII 版本方便阅读，文件保存 LaTeX 版本保证精确
- **大白话风格**：先给直觉再给细节，用生活类比解释抽象概念

**触发方式**：「帮我学习这篇论文」「我想深度理解这个」

### 展示模式（Present）

15-30 分钟准备一场论文汇报的 slides 内容。

核心特性：
- **图表映射**：自动从提取的图片中识别论文原图，重命名到 `figures/` 目录
- **逐页讨论**：大纲确认后逐页讨论内容，包含 Speaker Notes
- **图片嵌入**：生成的 HTML 演示文稿通过 base64 编码嵌入图片，完全自包含

**触发方式**：「帮我准备这篇论文的 slides」「我要做论文汇报」

## 模式可串联

三种模式可以自由串联。最常见的流程：

```
速览（判断值不值得读）→ 学习（深度理解）→ 展示（准备汇报）
```

速览的内容会被学习模式复用，不会重复劳动。

## 安装

**项目级安装**（推荐）：

```bash
# 克隆仓库后，将 skill 目录复制到你的项目中
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens <你的项目>/.claude/skills/
```

**用户级安装**（所有项目通用）：

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens ~/.claude/skills/
```

## 依赖

```bash
pip install pymupdf    # PDF 解析和图片提取
```

## 快速开始

```
> 帮我读这篇论文：https://arxiv.org/pdf/2511.05459v3
```

Claude 会自动下载 PDF、提取文本和图片，然后询问你想用哪种模式。

## 输出示例

查看 [examples/](examples/) 目录，包含用 SWE-Compass 论文测试的三种模式完整输出。

## 写作规范

- 所有输出为中文
- 英文术语后必须带中文注释（不超过 8 字），如 `Pass@1（单次通过率）`
- 避免 AI 套话和空洞评价
- 学习模式使用「大白话」风格，先直觉后细节

## 开发日志

查看 [docs/dev-journal.md](docs/dev-journal.md) 了解 Paper Lens 的设计思路和迭代过程。
