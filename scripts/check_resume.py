#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_resume.py —— 简历成品静态校验（不依赖浏览器）。

用法：
  python check_resume.py "D:\\out\\xx\\resume.html"

检查项：
  1. 占位符 / 模板示例内容残留
     - error：明确的虚构值（示例人名、示例电话、示例邮箱、TODO 等），必然需要替换
     - warning：真实机构名（北京师范、上海复旦等），用户可能真的属于该机构，仅提示核对
  2. 图片引用（src / url()）指向的本地文件是否存在
  3. 明显的空标签（元素内只有空白）

输出：人类可读摘要 + 问题分级；存在 error 时 exit code=1。
注意：本脚本只做静态检查，不验证排版页数——排版请另跑 check_layout.py。
"""
import argparse
import re
import sys
from pathlib import Path

# 明确的虚构占位值：出现在成品里必然需要替换
ERROR_PATTERNS = [
    r"文如菁", r"陈露露", r"赵\s?宇\s?明",
    r"135\s?0013\s?5000", r"150-0000-0000", r"138-0000-0000",
    r"xiaowangzi", r"chenlulu", r"123456789",
    r"TODO", r"待补充", r"待完善", r"占位", r"（此处", r"\(此处",
    # xxx 仅在独立成词时提示，避免误伤正常英文缩写
    r"(?<![A-Za-z0-9])[xX]{3}(?![A-Za-z0-9])",
]

# 真实机构名：模板示例用了它们，但用户本人可能真的属于该机构，只提示核对
WARN_PATTERNS = [
    r"北京百度", r"北京猫眼", r"北京乔布", r"北京师范", r"上海复旦", r"中国社会大学",
]

SRC_RE = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
URL_RE = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
# 仅检查应承载文字的 p / li；span / div 常作装饰容器（如灰条、线条），不检查
EMPTY_TAG_RE = re.compile(r"<(p|li)[^>]*>\s*</\1>")


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

    # 1. 示例/占位内容（error）+ 疑似真实机构名（warning）
    for pat in ERROR_PATTERNS:
        for m in re.finditer(pat, content):
            errors.append(f"示例/占位内容未替换: “{m.group(0)}”")
    for pat in WARN_PATTERNS:
        for m in re.finditer(pat, content):
            warnings.append(f"疑似模板示例机构，请确认是否已改为真实单位: “{m.group(0)}”")

    # 2. 本地资源引用
    refs = set(SRC_RE.findall(content)) | set(URL_RE.findall(content))
    for ref in refs:
        if ref.startswith(("data:", "http://", "https://", "#")):
            continue
        target = (html_path.parent / ref).resolve()
        if not target.is_file():
            errors.append(f"引用的本地文件不存在: {ref}")

    # 3. 空标签
    for m in EMPTY_TAG_RE.finditer(content):
        warnings.append(f"存在空标签: <{m.group(1)}>")

    # 去重（同一示例词可能多次出现）
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
        "\n[OK] 静态检查通过（示例残留 / 失效引用 / 空标签）。\n"
        "     本检查不包含排版页数，请另行运行 check_layout.py 验证 A4 单页。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
