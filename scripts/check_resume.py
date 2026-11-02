#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_resume.py —— 简历成品静态校验（不依赖浏览器）。

用法：
  python check_resume.py "D:\\out\\xx\\resume.html"

检查项：
  1. 未填写的骨架：模板内应承载正文的容器（value/org/date/role/desc/li/p/h1 等）
     若仍为空，说明漏填，判为 error。
  2. 占位标记：TODO / 待补充 / xxx 等，判为 error。
  3. 图片与样式引用（src / url()）指向的本地文件是否存在。
  4. 空标签（仅剩装饰容器的属正常，不报）。

输出：人类可读摘要 + 问题分级；存在 error 时 exit code=1。
注意：本脚本只做静态检查，不验证排版页数——请用 check_all.py 或 check_layout.py。
"""
import argparse
import re
import sys
from pathlib import Path

# 通用占位标记（模板本身已挖空，这里只兜「人/AI 写了一半」的情况）
ERROR_PATTERNS = [
    r"TODO", r"待补充", r"待完善", r"（此处", r"\(此处",
    # xxx 仅在独立成词时命中，避免误伤正常英文缩写
    r"(?<![A-Za-z0-9])[xX]{3}(?![A-Za-z0-9])",
]

# 模板内承载正文的 class：为空即漏填
TEXT_CLASSES = (
    "value", "date", "org", "role", "desc",
    "plain-text", "paragraph", "slogan", "apply", "title", "v",
)

# <tag class="... 目标class ...">  后面直接跟闭合标签
EMPTY_CLASS_RE = re.compile(
    r'<(\w+)\b[^>]*\bclass="[^"]*(?<![\w-])(?:%s)(?![\w-])[^"]*"[^>]*>\s*</\1>'
    % "|".join(TEXT_CLASSES),
    re.S,
)

# <p>/<li> 完全空
EMPTY_TAG_RE = re.compile(r"<(p|li)[^>]*>\s*</\1>")

# 姓名标题为空
EMPTY_H1_RE = re.compile(r"<h1[^>]*>\s*</h1>")

# template-002 基本信息行：只剩标签 span，没有值
EMPTY_BLINE_RE = re.compile(
    r'<div class="b-line">\s*(?:<span class="ic">.*?</span>\s*)?'
    r'<span class="k">[^<]*</span>\s*</div>',
    re.S,
)

# template-002 技能行：只剩加粗标签，没有内容
EMPTY_LI_K_RE = re.compile(r"<li>\s*<span class=\"k\">[^<]*</span>\s*</li>")

SRC_RE = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
URL_RE = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")


def _force_utf8_stdout():
    """Windows 控制台默认 GBK，管道/重定向时会输出乱码；统一改为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main():
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(description="简历成品静态校验")
    ap.add_argument("html", help="resume.html 的绝对路径")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.is_file():
        print(f"[ERROR] 文件不存在: {html_path}", file=sys.stderr)
        return 2

    content = html_path.read_text(encoding="utf-8")
    errors, warnings = [], []

    # 1. 占位标记
    for pat in ERROR_PATTERNS:
        for m in re.finditer(pat, content):
            errors.append(f"占位标记未替换: “{m.group(0)}”")

    # 2. 未填写的骨架
    empty_cls = EMPTY_CLASS_RE.findall(content)
    if empty_cls:
        errors.append(
            f"有 {len(empty_cls)} 处正文容器为空（tag={'/'.join(sorted(set(empty_cls)))}），疑似漏填"
        )
    empty_tags = EMPTY_TAG_RE.findall(content)
    if empty_tags:
        errors.append(
            f"有 {len(empty_tags)} 处 <{'/'.join(sorted(set(empty_tags)))}> 为空，疑似漏填"
        )
    if EMPTY_H1_RE.search(content):
        errors.append("姓名为空（<h1> 未填写）")
    if EMPTY_BLINE_RE.search(content):
        errors.append(f"有 {len(EMPTY_BLINE_RE.findall(content))} 行基本信息只有标签、没有内容")
    if EMPTY_LI_K_RE.search(content):
        errors.append(f"有 {len(EMPTY_LI_K_RE.findall(content))} 条技能只有标签、没有内容")

    # 3. 本地资源引用
    refs = set(SRC_RE.findall(content)) | set(URL_RE.findall(content))
    for ref in refs:
        if ref.startswith(("data:", "http://", "https://", "#")):
            continue
        target = (html_path.parent / ref).resolve()
        if not target.is_file():
            errors.append(f"引用的本地文件不存在: {ref}")

    errors = sorted(set(errors))
    warnings = sorted(set(warnings))

    print(f"校验文件: {html_path}")
    print(f"error: {len(errors)}  warning: {len(warnings)}")
    for e in errors:
        print("  [ERROR]", e)
    for w in warnings:
        print("  [WARN] ", w)

    if errors:
        print("\n[FAIL] 静态检查未通过，请修复上述 error。")
        return 1

    print(
        "\n[OK] 静态检查通过（无漏填、无占位标记、无失效引用）。\n"
        "     本检查不包含排版页数，请另行运行 check_layout.py 验证 A4 单页。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
