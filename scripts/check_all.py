#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_all.py —— 一条命令跑完简历成品校验（静态 + 排版）。

用法：
  python check_all.py "D:\\out\\xx\\resume.html"
  python check_all.py --self-check          # 回归三个内置模板

它会依次执行：
  1. check_resume.py  静态校验（漏填容器 / 占位标记 / 失效引用）
  2. check_layout.py  排版校验（渲染后页数 + 页面尺寸）
任一失败即返回非 0，并给出要修什么。

退出码（取两步中最严重的）：
  0  两步都通过
  1  有校验未通过
  2  输入错误（文件不存在）
  3  排版无法验证（无浏览器等环境问题）—— 必须转人工截图核对
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def _force_utf8_stdout():
    """Windows 控制台默认 GBK，管道/重定向时会输出乱码；统一改为 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def run_step(title, script, args):
    print("=" * 60)
    print(f"▶ {title}")
    print("=" * 60)
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPTS / script)] + [str(a) for a in args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def main():
    _force_utf8_stdout()
    ap = argparse.ArgumentParser(
        description="一条命令跑完简历成品校验（静态 + 排版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出码: 0 通过 / 1 校验未通过 / 2 输入错误 / 3 排版无法验证",
    )
    ap.add_argument("html", nargs="?", help="resume.html 的绝对路径")
    ap.add_argument("--self-check", action="store_true", help="回归三个内置模板")
    ap.add_argument("--browser", help="浏览器可执行文件路径，默认自动探测")
    ap.add_argument(
        "--expect", type=int, default=1,
        help="期望页数，默认 1。用户在流程开始时确认过目标页数时按实际值传",
    )
    args = ap.parse_args()

    if args.expect < 1:
        ap.error("--expect 必须 >= 1")

    if args.self_check:
        # 回归模式：只跑排版基线（模板本身是空壳，静态校验无意义）
        code = run_step("模板排版回归", "check_layout.py", ["--self-check"])
        print()
        print("[OK] 回归通过。" if code == 0 else "[FAIL] 回归未通过，见上方明细。")
        return code

    if not args.html:
        ap.error("需要提供 html 路径，或使用 --self-check")

    layout_args = [args.html, "--expect", str(args.expect)]
    if args.browser:
        layout_args += ["--browser", args.browser]

    print(f"校验目标: {Path(args.html).resolve()}")
    print(f"目标页数: {args.expect}\n")
    static_code = run_step("1/2 静态校验（漏填 / 占位标记 / 失效引用）", "check_resume.py", [args.html])
    print()
    layout_code = run_step(f"2/2 排版校验（目标 {args.expect} 页 + A4）", "check_layout.py", layout_args)

    print()
    print("=" * 60)
    if static_code == 0 and layout_code == 0:
        print("[OK] 两项校验全部通过，可以交付。")
        return 0

    if layout_code == 3:
        print("[SKIP] 排版未能验证（环境不具备）。")
        print("       请务必在浏览器中打开并截图人工核对：A4 一页、无溢出、照片正常。")
        return 3

    print("[FAIL] 校验未通过，请按上方提示修复后重跑。")
    if static_code != 0:
        print("       - 静态校验：补全仍为空的正文容器，替换占位标记")
    if layout_code != 0:
        print("       - 排版校验：精简文字内容，不要调字号或页边距")
    return 1


if __name__ == "__main__":
    sys.exit(main())
