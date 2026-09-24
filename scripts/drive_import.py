#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drive_import.py — 把「已填好 Drive 链接」的清单直接导入到对应产品。

与 drive_to_repo.py 的区别：这里不靠文件名自动匹配，而是清单里已经写明
slug（产品）+ kind（manual/firmware），所以你只需在 drive-manifest.csv 里
把每个文件的 Drive 链接填进 `drive_url` 列即可，脚本按 slug 直接挂到产品。

用法：
  python scripts/drive_import.py [manifest.csv]            # 试运行（只打印）
  python scripts/drive_import.py [manifest.csv] --write    # 生成 yml
  python scripts/drive_import.py [manifest.csv] --write --commit   # 生成并提交
  python scripts/drive_import.py [manifest.csv] --write --direct    # 固件走直链

清单列（scripts/drive-manifest.csv，已由目录预填）：
  slug, product, kind, docType, version, drive_url,
  title_es, title_en, date, releaseNotes_es, releaseNotes_en, checksum, fileSize, mandatory

规则：
  - `drive_url` 为空 = 你还没填，自动跳过（不生成空条目）。
  - kind=manual  -> src/content/manual/*.yml  （externalUrl = Drive 链接）
  - kind=firmware-> src/content/firmware/*.yml（downloadUrl = Drive 链接，需 version）
  - `drive_url` 支持：完整分享链接 / 文件 ID / uc?export=download&id= 链接，自动规整。
  - CSV 用 utf-8-sig 读取，Excel 另存为 CSV 的 BOM 不会破坏解析。

YAML 生成复用 drive_to_repo.build_yaml（与站点 schema 一致）。
"""
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive_to_repo as d  # noqa: E402


def main():
    args = sys.argv[1:]
    do_write = "--write" in args
    do_commit = "--commit" in args
    direct = "--direct" in args
    manifest = "scripts/drive-manifest.csv"
    for a in args:
        if not a.startswith("--"):
            manifest = a

    path = os.path.join(ROOT, manifest) if not os.path.isabs(manifest) else manifest
    if not os.path.exists(path):
        sys.exit(f"找不到清单: {path}")

    created, filled, pending, skipped = [], 0, 0, []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for rec in csv.DictReader(fh):
            slug = (rec.get("slug") or "").strip()
            kind = (rec.get("kind") or "").strip().lower()
            url = (rec.get("drive_url") or "").strip()
            if not slug:
                skipped.append((rec.get("product"), "无 slug"))
                continue
            if not url:
                pending += 1  # 你还没填链接，跳过
                continue
            if kind not in ("manual", "firmware"):
                skipped.append((slug, f"未知 kind={kind!r}"))
                continue
            norm_url = d.drive_link(url, direct=direct)
            dt = (rec.get("docType") or "user-guide").strip()
            version = (rec.get("version") or "").strip()
            if kind == "firmware" and not version:
                skipped.append((slug, "firmware 缺 version"))
                continue
            rec2 = {
                "filename": f"{slug}-{'fw' if kind == 'firmware' else dt}.pdf",
                "url": norm_url,
                "products": [slug],
                "title_es": (rec.get("title_es") or "").strip(),
                "title_en": (rec.get("title_en") or "").strip(),
                "date": (rec.get("date") or "").strip(),
                "duration": "",
                "version": version,
                "docType": dt,
            }
            content, out = d.build_yaml(kind, rec2)
            if content is None:
                skipped.append((slug, "firmware 缺 version（build 返回空）"))
                continue
            action = "WOULD CREATE" if not do_write else "CREATED"
            print(f"[{action}] {os.path.basename(out)}  ({kind} <- {slug})  {url[:60]}")
            filled += 1
            if do_write:
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w", encoding="utf-8") as of:
                    of.write(content)
                created.append(out)

    print(f"\n已填链接 {filled} 个，未填(跳过) {pending} 个，异常跳过 {len(skipped)} 个"
          + ("" if do_write else "  （试运行，加 --write 才真正写入）"))
    for s in skipped:
        print(f"[SKIP] {s[0]}: {s[1]}")

    if do_commit and created:
        subprocess.run(["git", "add", *created], check=True, cwd=ROOT)
        msg = f"chore: add {len(created)} Drive-linked resources (by slug)"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=ROOT)
        print("已提交到 git。")


if __name__ == "__main__":
    main()
