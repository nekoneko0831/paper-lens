---
name: paper-lens
description: "三模式论文阅读助手：速览(快速消化核心)、学习(大白话深度理解)、展示(准备演讲slides)。当用户提供论文PDF、要求分析/阅读论文、或说'帮我读这篇论文'时触发。"
allowed-tools: Read Write Edit Bash
---

# Paper Lens — 三模式论文阅读助手

通过三种不同的「镜头」阅读论文，满足不同场景的需求。

## 三种模式

| 模式 | 适合场景 | 耗时 | 交互方式 |
|------|----------|------|----------|
| **速览** | 快速判断是否值得深读 | 5分钟 | 一次性输出 |
| **学习** | 深度理解、实践落地 | 20-40分钟 | 多轮确认 |
| **展示** | 准备 slides 汇报 | 15-30分钟 | 逐页讨论 |
| **PDF 导出** | 导出排版精美的 PDF | 1分钟 | 一键导出 |

---

## Phase 0: 论文解析（所有模式共用）

### 0.1 获取论文 PDF

用户可能通过以下方式提供论文：

| 输入形式 | 处理方式 |
|----------|----------|
| 本地 PDF 路径 | 直接复制到 `paper-notes/<name>/paper.pdf` |
| arXiv URL（如 `https://arxiv.org/pdf/2506.07982`） | 用 `curl -L -o paper.pdf <url>` 下载 |
| arXiv abs URL（如 `https://arxiv.org/abs/2506.07982`） | 自动转换为 pdf URL 后下载 |
| 其他 URL（.pdf 结尾） | 用 `curl -L -o paper.pdf <url>` 下载 |

**下载命令**：

```bash
curl -L -o "paper-notes/<name>/paper.pdf" "<url>"
```

- 必须用 `-L` 跟随重定向
- 下载后用 PyMuPDF 验证文件有效性（`fitz.open()` 不报错即可）
- 如果下载失败，提示用户手动下载后提供本地路径

### 0.2 创建目录 + 提取内容

```bash
# 1. 创建标准目录
mkdir -p paper-notes/<name>/images

# 2. 提取全文文本
python3 -c "
import fitz
doc = fitz.open('paper-notes/<name>/paper.pdf')
text = ''
for i, page in enumerate(doc):
    text += f'\n\n===== PAGE {i+1} =====\n\n'
    text += page.get_text()
with open('paper-notes/<name>/extracted-text.md', 'w') as f:
    f.write(text)
doc.close()
"

# 3. 提取图片（动态定位脚本，兼容不同安装位置）
EXTRACT_SCRIPT=$(find .claude/skills/paper-lens/scripts ~/.claude/skills/paper-lens/scripts -name "extract_figures.py" 2>/dev/null | head -1)
python3 "$EXTRACT_SCRIPT" \
    paper-notes/<name>/paper.pdf \
    paper-notes/<name>/images/
```

### 标准输出目录

```
paper-notes/<paper-name>/
├── paper.pdf              # 原始论文
├── extracted-text.md      # 提取的全文文本
├── images/                # 提取的所有图表（矢量图 + 嵌入位图）
├── figures/               # 【展示模式】筛选后的关键图表（重命名为 fig1-xxx.png）
├── speed-read.md          # 速览模式输出
├── deep-learn.md          # 学习模式输出（增量保存，每步追加）
├── slides-content.md      # 展示模式输出
└── *.pdf                  # PDF 导出（与源 md 同名）
```

### 论文简称命名规则

- 小写，用 `-` 连接关键词
- 希腊字母写英文：`τ²-bench` → `tau2-bench`
- 特殊符号删除或转写：`@` → `at`，`#` → 删除
- 示例：`swe-compass`、`attention-is-all-you-need`、`tau2-bench`、`pass-at-k`

---

## Phase 1: 模式选择

**询问用户**：

> 论文已解析完成。你想用哪种模式来阅读？
>
> 1. **速览** — 5 分钟消化核心，快速判断值不值得深读
> 2. **学习** — 大白话深度理解，适合想真正搞懂这篇论文的人
> 3. **展示** — 准备一场论文讲解的 slides

**默认**：如果用户没有明确选择，默认使用速览模式。

**模式可串联**：用户可以先速览，觉得有价值再切换到学习或展示模式。速览的内容会被学习模式复用，不重复劳动。

---

## Phase 2: 执行模式

### 速览模式

加载 `references/speed-read.md` 执行。

核心输出：基本信息卡片 → 核心创新 → 主要方法 → 实验结果 → 总结与QA。

一次性输出到对话中，同时保存到 `paper-notes/<name>/speed-read.md`。

### 学习模式

加载 `references/deep-learn.md` 执行。

**核心体验：边学边存，随时可读。**

多轮交互流程：
1. 先输出速览内容（复用速览模式）→ 创建笔记文件
2. 名词提取 → **用 AskUserQuestion 工具交互选择**（多选 + 自定义输入）
3. 名词的大白话解释（英文术语后必须带中文注释）→ 追加到笔记
4. 核心方法的大白话拆解 → 追加到笔记
5. 公式确认 → **用 AskUserQuestion 工具交互选择** → 拆解后追加到笔记
6. 附录精华提炼 → 追加到笔记
7. 实践指导 → 追加到笔记

**关键机制**：
- **增量保存**：每个 Step 完成后自动追加到 `paper-notes/<name>/deep-learn.md`，用户全程可随时打开文件查看已学内容
- **交互选择**：术语和公式的确认环节使用 AskUserQuestion 工具，支持多选 + 自定义输入（用户可输入术语清单之外的任何想了解的内容）
- **全程可对话**：用户随时可用自然语言追问、补充术语、修改笔记、跳步或回溯，产生的新内容实时更新到笔记文件

### 展示模式

加载 `references/present.md` 执行。

**核心体验：图文并茂的 slides 内容，可直接生成带原文图片的 HTML 演示文稿。**

多轮交互流程：
1. 展示规划（场景/时长/听众/重点）
2. **图表筛选与映射**（从提取的图片中识别论文原图，重命名到 `figures/` 目录）
3. 生成 slides 大纲（每页标注引用的图表）
4. 逐页内容讨论与确认
5. 输出 slides 内容文档（含图片路径引用）

**关键机制**：
- **图表映射**：从 `images/` 中识别论文原图（Figure 1, 2, 3...），复制并重命名到 `figures/` 目录（如 `fig1-architecture.png`），方便后续引用
- **图片嵌入**：slides-content.md 中用 `![描述](figures/xxx.png)` 引用图片，`/frontend-slides` 生成 HTML 时会将图片 base64 编码嵌入，保证演示文稿完全自包含

最终保存到 `paper-notes/<name>/slides-content.md`。提示用户可用 `/frontend-slides` 生成 HTML 演示文稿。

### PDF 导出

加载 `references/export-pdf.md` 执行。

**核心体验：一键将任意模式的 md 笔记导出为排版精美的 PDF。**

- 支持三种排版样式：学术风格（academic）、简洁风格（clean）、紧凑风格（compact）
- 自动嵌入图片（`figures/`、`images/` 目录下的引用图片）
- LaTeX 公式渲染为数学符号图片（需 matplotlib）
- 中英混排、表格、代码块均正确渲染
- 自动添加页码

触发方式：用户说"导出 PDF"、"生成 PDF"、"转 PDF" 等。

---

## 通用写作规范

### 必须做

- 用中文输出所有内容
- **所有英文术语后必须带中文注释**：如 `Pass@1（单次通过率）`、`Active Learning（主动学习）`、`SWE-bench（软件工程评测基准）`。中文注释不超过 8 个字，优先用通用译法
- 保持客观准确，基于论文内容分析
- 公式和符号严格对应论文原文

### 必须避免

- **AI 套话**：不说"本文的核心贡献是..."、"值得注意的是..."、"综上所述..."
- **空洞评价**：不说"这是一篇重要的工作"、"为该领域提供了新思路"
- **过度装饰**：不滥用 emoji、不每句话都加粗
- **不必要的第一人称**：不说"我认为..."、"我的理解是..."

### 大白话风格指南（学习模式核心）

- 想象你在给一个聪明但非本领域的朋友解释
- 先给直觉，再给细节
- 用生活中的类比来解释抽象概念
- 避免"翻译原文"，要"用自己的话重新讲"
- 可以用「简单来说」「打个比方」「换句话说」这类过渡语

---

## 参考文件

- `references/speed-read.md` — 速览模式详细指令和输出模板
- `references/deep-learn.md` — 学习模式详细指令（名词提取、大白话拆解、公式解读、附录提炼）
- `references/present.md` — 展示模式详细指令（规划、大纲、逐页确认、输出规范）
- `references/export-pdf.md` — PDF 导出指令（样式选择、脚本执行）
- `scripts/extract_figures.py` — 论文图片提取脚本（依赖 PyMuPDF）
- `scripts/md_to_pdf.py` — Markdown → PDF 转换脚本（依赖 PyMuPDF + markdown）

## 依赖

```bash
# 核心依赖
pip install pymupdf markdown
# 推荐（LaTeX 公式渲染为数学符号）
pip install matplotlib
```
