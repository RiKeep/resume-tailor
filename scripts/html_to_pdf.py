#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
html_to_pdf.py —— 使用系统 Chrome / Edge 的 headless 模式把简历 HTML 打印为 A4 PDF。

用法：
  python html_to_pdf.py "D:\\out\\xx\\resume.html"
  python html_to_pdf.py "D:\\out\\xx\\resume.html" --pdf "D:\\out\\xx\\简历.pdf"
  python html_to_pdf.py "D:\\out\\xx\\resume.html" --browser "C:\\...\\chrome.exe"

说明：
  - 不依赖 playwright，依次探测 Chrome / Edge / Brave / Chromium（Windows / macOS / Linux）
  - --browser 可显式指定浏览器可执行文件，跳过自动探测
  - 页面尺寸/边距由 HTML 内 @page 规则控制（模板已内置 A4、margin:0）
  - 模板已设置 print-color-adjust:exact，灰条/蓝条等背景色会被打印
  - --virtual-time-budget 给字体和本地图片留出加载时间
  - 本文件的 render_pdf() 也可被 check_layout.py 直接导入复用
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows 下 Chrome/Edge 的常见安装位置
_WIN_CANDIDATES = (
    (r"Google\Chrome\Application\chrome.exe", ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)")),
    (r"Microsoft\Edge\Application\msedge.exe", ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")),
)

# macOS 下 Chromium 系浏览器的常见安装位置（相对 /Applications 与 ~/Applications）
_MAC_APPS = (
    "Google Chrome.app/Contents/MacOS/Google Chrome",
    "Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "Brave Browser.app/Contents/MacOS/Brave Browser",
    "Chromium.app/Contents/MacOS/Chromium",
)

# 可由 PATH 找到的可执行名
_PATH_NAMES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge",
    "chrome",
    "msedge",
)


def find_browser():
    """返回可用的浏览器可执行文件路径；找不到返回 None。"""
    mac_roots = ("/Applications", os.path.expanduser("~/Applications"))
    for app in _MAC_APPS:
        for root in mac_roots:
            c = os.path.join(root, app)
            if os.path.isfile(c):
                return c

    for rel, envs in _WIN_CANDIDATES:
        for env in envs:
            base = os.environ.get(env)
            if base:
                c = os.path.join(base, rel)
                if os.path.isfile(c):
                    return c

    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def render_pdf(html_path, pdf_path, browser=None, timeout=120):
    """把 html 渲染为 pdf。

    返回 (ok, message)：ok 为 bool；message 在失败时说明原因。
    """
    html_path = Path(html_path).resolve()
    if not html_path.is_file():
        return False, f"HTML 不存在: {html_path}"

    pdf_path = Path(pdf_path).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    exe = browser or find_browser()
    if not exe:
        return False, (
            "未找到 Chrome / Edge / Chromium。请安装其中之一，"
            "或用 --browser 显式指定浏览器可执行文件路径。"
        )
    if browser and not Path(browser).is_file():
        return False, f"--browser 指定的文件不存在: {browser}"

    cmd = [
        exe,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=3000",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"浏览器渲染超时（>{timeout}s）"
    except OSError as exc:
        return False, f"无法启动浏览器: {exc}"

    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return False, f"PDF 生成失败。{detail}" if detail else "PDF 生成失败（浏览器未输出文件）"
    return True, ""


def _force_utf8_stdout():
    """Windows 控制台默认 GBK，管道/重定向时会输出乱码；统一改为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main():
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(description="HTML 转 A4 PDF")
    ap.add_argument("html", help="简历 HTML 的绝对路径")
    ap.add_argument("--pdf", help="输出 PDF 路径，默认与 HTML 同目录同名 .pdf")
    ap.add_argument("--browser", help="浏览器可执行文件路径，默认自动探测 Chrome/Edge")
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    if not html_path.is_file():
        print(f"[ERROR] HTML 不存在: {html_path}", file=sys.stderr)
        return 2

    pdf_path = Path(args.pdf).resolve() if args.pdf else html_path.with_suffix(".pdf")

    ok, message = render_pdf(html_path, pdf_path, browser=args.browser)
    if not ok:
        print(f"[ERROR] {message}", file=sys.stderr)
        return 3

    print("[OK] PDF 已生成")
    print(" ", pdf_path)
    print("  大小:", pdf_path.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
