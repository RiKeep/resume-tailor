#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_layout.py —— 渲染后校验「A4 单页」这条核心承诺。

用法：
  python check_layout.py "D:\\out\\xx\\resume.html"
  python check_layout.py "D:\\out\\xx\\resume.html" --expect 1
  python check_layout.py --pdf "D:\\out\\xx\\resume.pdf"      # 复用已有 PDF，不重新渲染
  python check_layout.py --self-check                         # 回归：三个内置模板应均为 1 页 A4

检查项：
  1. 渲染后的 PDF 页数是否等于 --expect（默认 1）
  2. 页面尺寸是否为标准 A4（210x297mm，容差 ±2pt）

退出码：
  0  通过
  1  不满足（页数超出 / 尺寸非 A4）
  2  输入错误（文件不存在、参数非法）
  3  环境不具备或无法判定（无浏览器、无法解析 PDF）

重要：环境不具备时只输出 [SKIP] 并返回 3，绝不输出 [OK] 冒充通过。
     调用方（agent）必须据退出码决定是否转入人工截图核对。
"""
import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "assets"
TEMPLATES = ("template-001", "template-002", "template-003")

# 标准 A4（pt）。1mm = 72/25.4 pt
A4_W = 210 * 72 / 25.4  # 595.276
A4_H = 297 * 72 / 25.4  # 841.890
TOLERANCE = 2.0         # pt，容纳渲染器取整差异

_MEDIABOX_RE = re.compile(
    rb"/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]"
)
_COUNT_RE = re.compile(rb"/Count\s+(\d+)")


def _info_via_pypdf(pdf_path):
    """用 pypdf 读页数与首页尺寸；不可用时返回 None。"""
    try:
        import pypdf  # 可选依赖
    except ImportError:
        return None
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        pages = len(reader.pages)
        box = reader.pages[0].mediabox
        return pages, (float(box.width), float(box.height))
    except Exception:
        return None


def _info_via_regex(pdf_path):
    """不依赖任何库，从 PDF 字节流里解析页数与 MediaBox。"""
    raw = pdf_path.read_bytes()

    counts = [int(c) for c in _COUNT_RE.findall(raw)]
    pages = max(counts) if counts else None
    if pages is None:
        # 退路：数页面对象（排除 /Pages 节点）
        pages = len(re.findall(rb"/Type\s*/Page(?![s])", raw)) or None

    boxes = _MEDIABOX_RE.findall(raw)
    size = None
    if boxes:
        x0, y0, x1, y1 = (float(v) for v in boxes[0])
        size = (abs(x1 - x0), abs(y1 - y0))

    if pages is None or size is None:
        return None
    return pages, size


def read_pdf_info(pdf_path):
    """返回 (pages, (w, h))；无法判定时返回 (None, None)。"""
    info = _info_via_pypdf(pdf_path) or _info_via_regex(pdf_path)
    if not info:
        return None, None
    return info


def is_a4(size):
    if not size:
        return False
    w, h = size
    return abs(w - A4_W) <= TOLERANCE and abs(h - A4_H) <= TOLERANCE


def evaluate(pdf_path, expect=1, label=""):
    """校验一个 PDF，返回 (exit_code, lines)。"""
    pages, size = read_pdf_info(pdf_path)
    prefix = f"{label}: " if label else ""

    if pages is None:
        return 3, [
            f"{prefix}[SKIP] 未能判定页数与页面尺寸（PDF 结构无法解析）。",
            "       请人工在浏览器中打开并截图核对。",
        ]

    lines = []
    ok = True
    if pages != expect:
        ok = False
        lines.append(f"{prefix}[ERROR] 页数为 {pages}，应为 {expect} 页。")
        if pages > expect:
            lines.append("        请精简文字内容（不要调整字号或页边距）。")
    if not is_a4(size):
        ok = False
        w, h = size
        lines.append(
            f"{prefix}[ERROR] 页面尺寸 {w * 25.4 / 72:.1f}x{h * 25.4 / 72:.1f}mm "
            f"不是标准 A4（210.0x297.0mm）。请检查模板 @page 规则。"
        )
    if ok:
        w, h = size
        lines.append(
            f"{prefix}[OK] {pages} 页，页面 {w * 25.4 / 72:.1f}x{h * 25.4 / 72:.1f}mm（A4）"
        )
        return 0, lines
    return 1, lines


def _render(html_path, browser):
    """渲染到临时 PDF。

    返回 (pdf_path, tmpdir, exit_code, message)：
      - 成功时 exit_code 为 0，tmpdir 需由调用方负责清理
      - 失败时 pdf_path 与 tmpdir 为 None
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from html_to_pdf import find_browser, render_pdf

    exe = browser or find_browser()
    if not exe:
        return None, None, 3, (
            "[SKIP] 未执行排版校验：未找到 Chrome / Edge / Chromium。\n"
            "       请安装其中之一，或用 --browser 指定可执行文件路径。"
        )

    tmp = Path(tempfile.mkdtemp(prefix="resume-layout-"))
    pdf = tmp / (html_path.stem + ".pdf")
    ok, message = render_pdf(html_path, pdf, browser=exe)
    if not ok:
        # 渲染失败也要清掉刚建的临时目录，避免反复运行堆积
        shutil.rmtree(tmp, ignore_errors=True)
        return None, None, 3, f"[SKIP] 未执行排版校验：渲染失败。\n       {message}"
    return pdf, tmp, 0, ""


def check_one(html_path, expect=1, browser=None, pdf=None):
    html_path = Path(html_path).resolve()
    tmpdir = None
    if pdf:
        pdf_path = Path(pdf).resolve()
        if not pdf_path.is_file():
            print(f"[ERROR] PDF 不存在: {pdf_path}", file=sys.stderr)
            return 2
        target = pdf_path
    else:
        if not html_path.is_file():
            print(f"[ERROR] HTML 不存在: {html_path}", file=sys.stderr)
            return 2
        print(f"渲染: {html_path}")
        target, tmpdir, code, message = _render(html_path, browser)
        if code:
            print(message)
            return code

    try:
        code, lines = evaluate(target, expect=expect)
        for line in lines:
            print(line)
        if code == 1:
            print("\n[FAIL] 排版校验未通过。")
        return code
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def self_check(browser=None, expect=1):
    """回归：三个内置模板应均为 expect 页且 A4。"""
    print(f"回归检查内置模板（期望 {expect} 页 / A4）\n")
    failed = 0
    skipped = 0
    for name in TEMPLATES:
        html = TEMPLATES_DIR / name / "resume.html"
        if not html.is_file():
            print(f"{name}: [ERROR] 模板缺失 {html}")
            failed += 1
            continue
        target, tmpdir, code, message = _render(html, browser)
        if code:
            print(f"{name}: {message}")
            skipped += 1
            continue
        try:
            code, lines = evaluate(target, expect=expect, label=name)
            for line in lines:
                print(line)
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)
        if code == 1:
            failed += 1
        elif code == 3:
            skipped += 1

    print()
    if skipped and not failed:
        print(f"[SKIP] {skipped} 个模板未能校验（环境不具备或无法解析）。")
        return 3
    if failed:
        print(f"[FAIL] {failed} 个模板不满足「{expect} 页 + A4」。")
        return 1
    print(f"[OK] 全部 {len(TEMPLATES)} 个模板均为 {expect} 页且为 A4。")
    return 0


def _force_utf8_stdout():
    """Windows 控制台默认 GBK，管道/重定向时会输出乱码；统一改为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main():
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(
        description="校验简历渲染结果是否为 A4 单页",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出码: 0 通过 / 1 不符合 / 2 输入错误 / 3 环境不具备",
    )
    ap.add_argument("html", nargs="?", help="resume.html 的绝对路径")
    ap.add_argument("--expect", type=int, default=1, help="期望页数，默认 1")
    ap.add_argument("--pdf", help="复用已有 PDF，跳过渲染")
    ap.add_argument("--browser", help="浏览器可执行文件路径，默认自动探测")
    ap.add_argument("--self-check", action="store_true", help="回归检查三个内置模板")
    args = ap.parse_args()

    if args.self_check:
        return self_check(browser=args.browser, expect=args.expect)

    if not args.html and not args.pdf:
        ap.error("需要提供 html 路径，或使用 --pdf / --self-check")
    if args.expect < 1:
        ap.error("--expect 必须 >= 1")

    return check_one(args.html or "", expect=args.expect, browser=args.browser, pdf=args.pdf)


if __name__ == "__main__":
    sys.exit(main())
