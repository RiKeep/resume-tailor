# 模板 docx 原件

本目录存放三个简历模板的 Word 原件，供**自行重制或微调版式**时参考使用。

| 文件 | 对应模板 |
| --- | --- |
| `001.docx` | `assets/template-001`（灰条传统风） |
| `002.docx` | `assets/template-002`（蓝色箭头风） |
| `003.docx` | `assets/template-003`（深蓝图标风） |

## 说明

- 这些 docx **不参与**技能生成流程。技能读取的是 `assets/template-00X/resume.html`。
- 如果你想修改模板版式，建议先在 docx 中调整，再同步重制对应的 `resume.html`。
- 修改后请务必跑一次回归，确认模板仍是 A4 单页：

```bash
python scripts/check_layout.py --self-check
```

## 来源

模板设计复刻自 [mmmlllnnn/ResumeCollection](https://github.com/mmmlllnnn/ResumeCollection)（MIT License）。
