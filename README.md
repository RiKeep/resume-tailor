# Resume Tailor

> **发布前待办**
> 1. 把 3 处占位符 `YOUR_USERNAME` 替换为你的 GitHub 用户名（第 4 节的两条安装命令与 clone 地址）。
> 2. 第 6 节有 4 张截图待补，文件名见该节末尾的表格；补齐后图片会自动渲染。

## 1. 许可证

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

本项目基于 **MIT License** 开源（见 [LICENSE](LICENSE)），允许个人与商业用途的使用、复制、修改和分发，只需在使用时保留原始版权与许可声明。

## 2. 描述

Resume Tailor 是一个面向 AI Agent 的 **Skill（技能）**：根据岗位描述（JD）和你的真实素材，自动生成有针对性的 A4 单页 HTML 简历，并可一键导出 PDF。

通过自然语言触发后，AI 会读取你的真实材料、拆解岗位要求、套用内置模板，产出与岗位逐条对齐的简历。它不是简单的信息填空，而是：

- **JD 驱动**：拆解岗位的硬门槛、硬技能、职责与加分项，提取必备关键词并建立匹配矩阵
- **真实素材改写**：基于你提供的材料，用 STAR 法则和量化表达优化，严格区分"合理润色"与"编造"，不虚构经历、数据、证书
- **三套即选模板**：传统风、蓝色箭头风、深蓝技术风，选择时展示可视化预览，而非只报文件名
- **A4 精确排版**：三个模板统一使用标准 A4 `@page` 规则，并由 `check_layout.py` 在渲染后校验页数与页面尺寸
- **确定性脚本**：模板初始化、静态校验、排版校验、HTML 转 PDF 均由脚本保证可复现；环境不具备时会明确报 `[SKIP]`，不会假装通过
- **单文件自包含**：每个简历为一个 HTML + 本地图片，无外部依赖、可离线打开

## 3. 目录结构

```
resume-tailor/
├── SKILL.md                     # 技能主入口：触发条件与端到端工作流程
├── README.md                    # 项目说明文档
├── LICENSE                      # MIT 许可证
├── assets/                      # 输出用资源（模板，均为 A4 单页）
│   ├── template-001/
│   │   ├── resume.html          # 模板页面
│   │   ├── preview.jpg          # 可视化预览图
│   │   └── assets/photo.jpeg    # 默认证件照
│   ├── template-002/
│   │   ├── resume.html
│   │   ├── preview.jpg
│   │   └── assets/photo.jpeg
│   └── template-003/
│       ├── resume.html
│       ├── preview.jpg
│       └── assets/photo.jpeg
├── sources/                     # 模板 docx 原件（仅供改版式/重制，不参与生成）
│   ├── 001.docx
│   ├── 002.docx
│   └── 003.docx
├── references/                  # 方法论文档（按需加载）
│   ├── jd-analysis.md           # JD 拆解与关键词匹配
│   ├── resume-writing.md        # 真实性红线、STAR/量化写法
│   └── template-guide.md        # 模板结构与版式保护规则
├── scripts/                     # 确定性脚本
│   ├── init_from_template.py    # 复制模板到输出目录（可选带入证件照）
│   ├── check_resume.py          # 示例残留/占位符/失效引用静态校验
│   ├── check_layout.py          # 渲染后校验 A4 单页（含 --self-check 回归）
│   └── html_to_pdf.py           # 调用系统 Chrome/Edge 转 A4 PDF
└── examples/                    # 示例与测试素材
    └── sample-materials/        # 虚构个人素材知识库（含测试 JD），可直接用于体验
```

## 环境要求

- **Python 3.8+**：三个脚本只依赖标准库，无需 `pip install`。
- **Chrome / Edge / Chromium**：仅导出 PDF 与排版校验需要；脚本会自动探测 Windows / macOS / Linux 的常见安装位置，也可用 `--browser` 显式指定。
- 若安装了 `pypdf`，`check_layout.py` 会优先用它读取 PDF；未安装时自动回退到内置解析，不影响使用。

## 4. 安装

本技能基于开放的 Agent Skills 协议，可在任何 skills-compatible 的 AI agent runtime 中运行。

### 方式一：让 AI 安装（推荐）

打开你正在使用的 agent，直接告诉它：

> 帮我安装这个 skill：https://github.com/YOUR_USERNAME/resume-tailor

（将 `YOUR_USERNAME` 替换为你实际的 GitHub 用户名。）

也可以使用通用 CLI 安装器，它会自动识别当前 runtime 并把技能放到正确目录：

```bash
npx skills add YOUR_USERNAME/resume-tailor
```

### 方式二：手动安装

将仓库克隆到对应 runtime 的 `skills/` 目录即可：

| Runtime | 安装路径 |
| --- | --- |
| Claude Code | `~/.claude/skills/resume-tailor/` |
| Codex CLI | `~/.codex/skills/resume-tailor/` |
| 其他 runtime | clone 到对应 runtime 的 `skills/` 目录 |

```bash
git clone https://github.com/YOUR_USERNAME/resume-tailor <上面对应的路径>
```

即使 runtime 不支持自动加载，也可以直接把 `SKILL.md` 的内容粘贴进对话——它本质上就是一份 Markdown 加 YAML frontmatter。

### 安装后自检（推荐）

clone 下来后先跑一次回归，确认环境可用且三个模板仍是 A4 单页：

```bash
python scripts/check_layout.py --self-check
```

期望输出 `[OK] 全部 3 个模板均为 1 页且为 A4。`
若返回 `[SKIP]`，说明本机没找到 Chrome/Edge，导出 PDF 与排版校验将不可用（其余功能正常）。

## 5. 模板展示

| 模板 | 风格 | 适配场景 |
| --- | --- | --- |
| `template-001` | 灰条传统风 | 国企 / 事业单位 / 传统行业，或需要民族、政治面貌、身高字段的岗位，最通用稳妥 |
| `template-002` | 蓝色箭头风 | 行政 / 职能 / 运营 / 市场 / 人力等，现代清爽、设计感强 |
| `template-003` | 深蓝图标风 | 技术岗（Java / 开发 / 互联网），姓名突出、简洁专业 |

### template-001 灰条传统风

![template-001 预览](assets/template-001/preview.jpg)

### template-002 蓝色箭头风

![template-002 预览](assets/template-002/preview.jpg)

### template-003 深蓝图标风

![template-003 预览](assets/template-003/preview.jpg)

## 6. 效果示例

仓库已内置一套虚构测试素材 `examples/sample-materials/`（含测试 JD 和完整个人材料，人物与数据均为虚构，不对应真实个人），可直接把它当作素材文件夹快速体验；你自己的截图也可统一放在 `examples/` 目录下。以下是完整使用流程，可照着操作并在对应步骤截图。

### 第一步：准备四项输入

1. **岗位 JD**：从招聘网站复制完整职位描述文本（或保存为 txt 文件）。
2. **素材文件夹**：新建一个文件夹，放入能证明你真实经历的材料，例如旧简历、项目说明、技能清单、证书照片等，支持 `.txt / .md / .docx / .pdf / 图片`。
3. **输出目录**：新建一个空文件夹，建议按"公司-岗位"命名，例如 `D:\求职\某科技-Java后端`。
4. **证件照**（可选）：准备一张证件照；没有则使用模板默认照片。

### 第二步：发起对话

向 AI 发送类似下面的指令（路径替换为你自己的）：

```text
帮我根据岗位 JD 生成一份针对性简历。
JD 我直接贴给你：
（这里粘贴完整 JD）

我的素材文件夹：D:\求职\我的材料
输出目录：D:\求职\某科技-Java后端
证件照：D:\求职\photo.jpg（没有就用模板默认）
```

### 第三步：查看模板预览并选择

AI 会读取素材文件夹，并把三个模板的预览图连同风格、适配场景一起展示出来。此时可截图保存为 `examples/01-模板选择.png`。根据岗位和喜好回复模板编号，例如：

```text
我选 template-003，这是技术岗。
```

### 第四步：确认 JD 分析与内容

AI 会拆解 JD 的硬门槛、技能关键词和匹配情况，然后基于真实素材改写内容。若提示某项硬门槛缺失或信息存疑，会主动向你确认——如实回答即可，不要让 AI 编造。此步骤可截图保存为 `examples/02-JD分析.png`。

### 第五步：获取成品并校验

AI 会复制所选模板、填充内容、替换照片，并运行校验脚本确认无示例残留和失效引用，然后交付 `resume.html`。在浏览器中打开确认排版为 A4 一页、无溢出错位、照片正常。此步骤可截图保存为 `examples/03-HTML成品.png`。

### 第六步：导出 PDF（可选）

需要 PDF 时，让 AI 运行导出脚本，或自行执行：

```bash
python scripts/html_to_pdf.py "D:\求职\某科技-Java后端\resume.html"
```

脚本会自动调用系统 Chrome/Edge 生成同目录下的 `resume.pdf`。可截图保存为 `examples/04-PDF效果.png`。

### 截图占位（待补）

以下 4 张截图尚未提交到仓库。补齐后放入 `examples/`，本节即可直接展示：

| 文件名 | 应展示的内容 |
| --- | --- |
| `examples/01-模板选择.png` | 三个模板预览图并排呈现、用户回复模板编号的对话 |
| `examples/02-JD分析.png` | JD 硬门槛/关键词拆解与匹配矩阵，以及向用户确认疑点的对话 |
| `examples/03-HTML成品.png` | 浏览器中打开的成品，A4 一页、照片正常、三段对齐 |
| `examples/04-PDF效果.png` | 导出的 `resume.pdf` 页面效果 |

> 移动 HTML 文件时，请连同同级的 `assets/` 文件夹一起移动，否则照片会裂。

## 7. 模板来源与致谢

内置简历模板的**设计复刻自** [mmmlllnnn/ResumeCollection](https://github.com/mmmlllnnn/ResumeCollection)，该项目采用 MIT License，模板版权归原作者所有。本项目将其中的 docx 模板重制为 HTML 版本，并在此基础上构建了 JD 驱动的生成流程。感谢原作者的模板收集与分享。
