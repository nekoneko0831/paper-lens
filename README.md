# Paper Lens

一个用于论文阅读、深度理解和汇报准备的 Claude Code Skill。

## 它能做什么

Paper Lens 提供五种模式，覆盖从检索发现到深度理解再到汇报准备的完整工作流：

| 模式 | 用途 | 耗时 | 交互方式 |
|------|------|------|----------|
| **速览** | 5 分钟快速消化，判断是否值得深读 | ~5 分钟 | 一次性输出 |
| **学习** | 大白话深度理解，边学边存 | 20-40 分钟 | 多轮交互 |
| **展示** | 准备演讲 slides 内容 | 15-30 分钟 | 逐页讨论 |
| **批量检索** | 按主题搜索论文，生成表格 | 3-5 分钟 | 表格 + 选择下载 |
| **批量下载** | 粘贴多个链接批量下载 | 1-3 分钟 | 自动去重下载 |

## 快速开始

### 安装

**项目级安装**（推荐）：

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens <你的项目>/.claude/skills/
```

**用户级安装**（所有项目通用）：

```bash
git clone https://github.com/nekoneko0831/paper-lens.git /tmp/paper-lens
cp -r /tmp/paper-lens/.claude/skills/paper-lens ~/.claude/skills/
```

### 依赖

```bash
pip install pymupdf    # PDF 解析和图片提取
```

### 使用

在 Claude Code 中直接对话：

```
> 帮我读这篇论文：https://arxiv.org/pdf/1706.03762
> 搜索 LLM agent evaluation 相关论文
> 帮我下载这些论文：2501.12948 2309.12288 2401.05566
```

Claude 会自动识别意图并进入对应模式。

## 五种模式详解

### 速览模式

5 分钟快速消化一篇论文的核心内容。输出包括基本信息卡片、TL;DR、核心创新、主要方法、实验结果和深度问答。

**触发**：「帮我速览这篇论文」「快速读一下这个 PDF」

### 学习模式

20-40 分钟的交互式深度学习。所有概念用「大白话」解释——想象在给一个聪明但非本领域的朋友讲解。

核心特性：
- **边学边存**：每个步骤完成后自动追加到笔记文件，随时可查看
- **术语交互选择**：提取论文术语后通过分组多选让你选择想深入了解的部分
- **双层公式**：终端显示 ASCII 版本，文件保存 LaTeX 版本
- **断点恢复**：中断后可从上次进度继续

**触发**：「帮我学习这篇论文」「我想深度理解这个」

### 展示模式

15-30 分钟准备一场论文汇报的 slides 内容。

核心特性：
- **图表映射**：自动从提取的图片中识别论文原图，重命名到 `figures/` 目录
- **逐页讨论**：大纲确认后逐页讨论内容，包含 Speaker Notes
- **图片嵌入**：生成的 HTML 演示文稿通过 base64 编码嵌入图片，完全自包含

**触发**：「帮我准备这篇论文的 slides」「我要做论文汇报」

### 批量检索模式

按主题关键词搜索论文，生成带链接的排序表格，支持一键下载选中论文。

**触发**：「搜索 LLM agent evaluation 相关论文」「帮我找 coding benchmark 的最新工作」

### 批量下载模式

粘贴多个 arXiv 链接或 ID，自动去重后批量下载。支持混合格式输入（URL、abs 链接、裸 ID）。

**触发**：直接粘贴多个 arXiv 链接

## 模式串联

三种阅读模式可以自由串联，最常见的流程：

```
速览（判断值不值得读）→ 学习（深度理解）→ 展示（准备汇报）
```

速览的内容会被学习模式复用，不会重复劳动。

## 输出结构

每篇论文在 `paper-notes/` 下有独立目录：

```
paper-notes/<paper-name>/
├── paper.pdf              # 原始 PDF
├── extracted-text.md      # 提取的全文
├── images/                # 所有提取图片（矢量 + 位图）
├── figures/               # [展示] 筛选后的论文原图
├── speed-read.md          # 速览输出
├── deep-learn.md          # 学习输出（增量保存）
└── slides-content.md      # 展示模式输出
```

## Skill 目录结构

```
.claude/skills/paper-lens/
├── SKILL.md                     # 主入口（模式路由 + Phase 0 解析）
├── references/
│   ├── speed-read.md            # 速览模式指令
│   ├── deep-learn.md            # 学习模式指令
│   ├── present.md               # 展示模式指令
│   ├── export-pdf.md            # PDF 导出指令
│   ├── batch-search.md          # 批量检索指令
│   └── batch-download.md        # 批量下载指令
└── scripts/
    ├── extract_figures.py       # 图片提取（矢量图 + 位图 + 去重）
    └── md_to_pdf.py             # Markdown → PDF 转换
```

## HTML 演示文稿

展示模式生成 `slides-content.md`，其中包含图表引用。要转换为自包含的 HTML 演示文稿，可以使用 slides 生成工具（如 Claude Code 的 `frontend-slides` skill）或任何 Markdown 转 slides 工具。

## 写作规范

- 所有输出为中文
- 英文术语后必须带中文注释（不超过 8 字），如 `Pass@1（单次通过率）`
- 避免 AI 套话和空洞评价
- 学习模式使用「大白话」风格，先直觉后细节

## 开发日志

查看 [docs/dev-journal.md](docs/dev-journal.md) 了解设计思路和迭代过程。

## License

[MIT](LICENSE)
