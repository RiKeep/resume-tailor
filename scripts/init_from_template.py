#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_from_template.py —— 把指定 HTML 模板复制到输出目录，建立可编辑的工作副本。

用法：
  python init_from_template.py --template template-001 --output "D:\\out"
  python init_from_template.py --template template-002 --output "D:\\out" --name "武汉XX-Java"

说明：
  - 仅复制成品所需文件：resume.html 与 assets/（不复制 preview.jpg）
  - 目标目录已存在且非空时报错，避免覆盖用户文件
  - --name 只允许作为单级文件夹名，不允许路径分隔符或 ..
  - --photo 可直接把用户照片覆盖到工作副本 assets/photo.jpeg
  - 复制后打印工作副本的 HTML 绝对路径，供后续填充内容
"""
import argparse
import os
import shutil
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(SKILL_ROOT, "assets")
TEMPLATES = ("template-001", "template-002", "template-003")

# Windows 保留名（con、prn 等）建目录会失败或行为异常，一并拒绝
_WIN_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _safe_folder_name(name):
    """校验 --name 是单级合法文件夹名。返回 (ok, 原因)。"""
    if not name:
        return False, "--name 不能为空"
    if name in (".", ".."):
        return False, "--name 不能是 . 或 .."
    if any(sep in name for sep in ("/", "\\")):
        return False, "--name 不能包含路径分隔符（/ 或 \\），它只应是单级文件夹名"
    if "\x00" in name:
        return False, "--name 包含非法字符"
    # Windows 不允许的字符，提前拦掉以免报出难懂的 OSError
    for ch in ':*?"<>|':
        if ch in name:
            return False, f"--name 包含 Windows 不允许的字符: {ch}"
    if name.split(".")[0].lower() in _WIN_RESERVED:
        return False, f"--name 使用了系统保留名: {name}"
    if name != name.strip() or name.endswith("."):
        return False, "--name 首尾不能有空格，且不能以点结尾"
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
    ap = argparse.ArgumentParser(description="从模板初始化简历工作副本")
    ap.add_argument("--template", required=True, choices=TEMPLATES)
    ap.add_argument("--output", required=True, help="输出父目录（绝对路径）")
    ap.add_argument("--name", help="工作文件夹名（单级，不可含路径分隔符）")
    ap.add_argument("--photo", help="证件照路径，将覆盖工作副本的 assets/photo.jpeg")
    args = ap.parse_args()

    src = os.path.join(TEMPLATES_DIR, args.template)
    if not os.path.isdir(src):
        print(f"[ERROR] 模板目录不存在: {src}", file=sys.stderr)
        return 2

    folder = args.name or args.template
    ok, reason = _safe_folder_name(folder)
    if not ok:
        print(f"[ERROR] {reason}", file=sys.stderr)
        return 2

    if args.photo and not os.path.isfile(args.photo):
        print(f"[ERROR] 照片不存在: {args.photo}", file=sys.stderr)
        return 2

    output_root = os.path.abspath(args.output)
    os.makedirs(output_root, exist_ok=True)
    dst = os.path.join(output_root, folder)

    # 二次确认：目标必须落在 --output 之内，防止任何未预料的越界写法
    if os.path.commonpath([output_root, os.path.abspath(dst)]) != output_root:
        print(f"[ERROR] 目标路径越出输出目录，已拒绝: {dst}", file=sys.stderr)
        return 2

    if os.path.exists(dst):
        if os.path.isdir(dst) and os.listdir(dst):
            print(f"[ERROR] 目标已存在且非空，拒绝覆盖: {dst}", file=sys.stderr)
            return 2
    else:
        os.makedirs(dst, exist_ok=True)

    # 复制 HTML
    shutil.copy2(os.path.join(src, "resume.html"), os.path.join(dst, "resume.html"))
    # 复制 assets（照片等）
    src_assets = os.path.join(src, "assets")
    dst_assets = os.path.join(dst, "assets")
    if os.path.isdir(src_assets):
        shutil.copytree(src_assets, dst_assets, dirs_exist_ok=True)

    # 用户照片：同名覆盖，保证模板引用 assets/photo.jpeg 不变
    photo_note = "使用模板默认照片"
    if args.photo:
        os.makedirs(dst_assets, exist_ok=True)
        shutil.copy2(args.photo, os.path.join(dst_assets, "photo.jpeg"))
        photo_note = f"已替换为 {os.path.abspath(args.photo)}"

    result_html = os.path.join(dst, "resume.html")
    print("[OK] 工作副本已建立")
    print("  HTML:", result_html)
    print("  目录:", dst)
    print("  照片:", photo_note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
