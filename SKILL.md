---
name: resume-tailor
description: 根据岗位 JD（职位描述）和用户的真实素材，生成有针对性的 A4 单页 HTML 简历并可导出 PDF。当用户要求"根据 JD/岗位描述写简历、做针对性简历、定制简历、套模板生成简历、把简历转成 PDF"，或提供了招聘要求与个人素材文件夹时使用。内置三个可选 HTML 模板（灰条传统风、蓝色箭头风、深蓝图标技术风），支持关键词对齐、STAR/量化改写与真实性校验。
---

# JD 驱动的简历生成

基于用户真实素材和岗位 JD，套用内置 HTML 模板产出一份针对性简历（A4 单页），可直接导出 PDF。

## 资源导航

- `assets/template-001~003/`：三个模板，每个含 `resume.html`、`preview.jpg`（预览图）、`assets/photo.jpeg`（默认照片）。模板均为 A4 单页。
- `sources/`：三个模板的 docx 原件，仅在用户想改版式或重制模板时参考，不参与生成流程。
- `references/jd-analysis.md`：JD 拆解、关键词提取与匹配矩阵方法。
- `references/resume-writing.md`：真实性红线、STAR/量化写法、模块取舍与一页纸规则。
- `references/template-guide.md`：三个模板的结构、可编辑点、适配场景与版式保护规则。
- `scripts/init_from_template.py`：复制模板到输出目录（可选 `--photo` 直接带入证件照）。
- `scripts/check_resume.py`：示例残留/占位符/失效引用静态校验（不查排版）。
- `scripts/check_layout.py`：渲染后校验 A4 单页（`--self-check` 可回归三个内置模板）。
- `scripts/html_to_pdf.py`：调用系统 Chrome/Edge 转 A4 PDF。

## 工作流程

### 1. 收集四项输入，缺一先问

1. **JD**：用户直接粘贴文本，或提供 JD 文件路径。
2. **素材文件夹路径**：让用户给出包含其真实材料的文件夹（旧简历、项目说明、证书、技能清单等）。
3. **输出位置**：让用户指定成品保存目录（建议按"姓名-岗位"命名独立文件夹）。
4. **证件照**：用户提供照片路径则替换；未提供则保留模板默认照片，不删照片区块。

### 2. 读取素材文件夹，建立事实清单

- 遍历文件夹，按类型读取：`.txt/.md` 直接读；`.docx` 用 python-docx，**若内容在文本框（txbxContent）中，需解压 docx 解析 `word/document.xml`**；`.pdf` 用 PDF 读取能力；图片用读图能力。
- 只记录可核实的事实：教育背景、时间、学校、专业、项目、职责、技能、证书、数据。
- 事实存疑或互相矛盾时，先问用户，不猜测。

### 3. 展示模板预览，让用户选择

- 用图片展示能力把三个模板的 `assets/template-001/preview.jpg`、`template-002/preview.jpg`、`template-003/preview.jpg` 连同编号、风格、适配场景一起呈现给用户，**不能只发文件名或路径**。
- 用户选定后再继续；可参考 `references/template-guide.md` 给出建议，但由用户拍板。

### 4. 分析 JD 并匹配

- 按 `references/jd-analysis.md` 拆出硬门槛、硬技能、职责、软技能、加分项，提取必备关键词。
- 建立匹配/部分匹配/缺失矩阵；硬门槛缺失要明确告知风险，不编造。

### 5. 改写内容

- 按 `references/resume-writing.md` 把真实素材改写成对齐 JD 的条目：动词开头、STAR、尽量量化、使用 JD 原词。
- 强相关内容前置详写，无关内容弱化或删除；所有数据必须来自素材或可由事实直接推出。

### 6. 初始化工作副本并填充

- 运行：`python scripts/init_from_template.py --template <模板名> --output <用户指定目录> --name <文件夹名> [--photo <照片路径>]`
- 在产出的 `resume.html` 上替换文字，严格保留 `<style>` 与 class 结构；新增条目复制同类整块，路径只用相对路径。
- 照片：直接用 `--photo` 带入，或把用户照片同名覆盖到工作副本 `assets/photo.jpeg`；无则保留默认。

### 7. 校验与交付

按顺序执行两步校验，**两步都要过**：

1. **静态校验**：`python scripts/check_resume.py <resume.html>`
   - 必须修复全部 error（示例人名、示例电话邮箱等虚构值未替换）。
   - warning 为疑似模板示例机构名，需向用户确认是否已改为真实单位。
2. **排版校验**：`python scripts/check_layout.py <resume.html>`
   - 期望输出 `[OK] 1 页，页面 ...（A4）`。
   - 若报页数超出：精简文字内容，**不要调字号或页边距**，改完重跑。
   - 若返回码为 3（`[SKIP]`，表示未找到 Chrome/Edge）：**必须**改用浏览器打开并截图人工核对，不得跳过这一步。

交付 HTML 成品；用户需要 PDF 时运行 `python scripts/html_to_pdf.py <resume.html>`，再交付 PDF。
提醒用户：移动 HTML 时连同 `assets` 文件夹一起，否则照片会裂。

## 硬性约束

- 不编造经历、公司、时间、技能、证书、数据；熟练度与事实一致。
- 不改模板 CSS 与版式尺寸，只替换文字和照片。
- 拿不准的决定先问用户并取得同意。
