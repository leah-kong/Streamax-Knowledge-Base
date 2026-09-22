#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drive_to_repo.py — 根据 Google Drive 文件名自动匹配产品，并生成网站内容条目。

工作流：
  1) 把文件传到 Google Drive（任意文件夹，文件对“任何人可查看/链接”开放）。
  2) 准备一份清单 CSV（最少列：filename, drive_url）：
       filename     原始文件名（含产品型号），如 "DS100_Instalacion.mp4"
       drive_url    Google Drive 分享链接、文件 ID、或 uc?export=download&id= 链接
       type        可选: video | manual | firmware（缺省按扩展名推断）
       title_es / title_en / date / duration / docType / version  可选覆盖
     也可以直接用 --folder-id <ID> 让脚本通过 Drive API 自动列出文件夹里的文件
     （需要 google-api-python-client + google-auth，并配置服务账号 credentials.json）。
  3) 试运行（默认只打印，不写文件）：
       python drive_to_repo.py manifest.csv
  4) 确认匹配无误后真正写入仓库：
       python drive_to_repo.py manifest.csv --write
  5) 写入并提交到 git：
       python drive_to_repo.py manifest.csv --write --commit

文件名匹配：
  - 对每个产品取 model / name(es,en) / series(es,en) / slug 作为匹配词，
    整体归一化（小写、非字母数字变空格）后，取“是文件名子串且最长”的词算分。
  - 同一文件名里最匹配的产品胜出；短型号（<3 字符）不会误命中。
  - 若匹配不到，或想手动纠正，可用 --mapping mapping.csv（列：filename,slug）强制指定。

生成的条目：
  - video    -> src/content/video/*.yml     (url=Drive 分享链接, external:true)
  - manual   -> src/content/manual/*.yml    (externalUrl=Drive 链接)
  - firmware -> src/content/firmware/*.yml  (downloadUrl=Drive 链接, 需 version)
"""
import csv
import glob
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_DIR = os.path.join(ROOT, "src", "content", "products")
COLLECTIONS = {
    "video": os.path.join(ROOT, "src", "content", "video"),
    "manual": os.path.join(ROOT, "src", "content", "manual"),
    "firmware": os.path.join(ROOT, "src", "content", "firmware"),
}
VIDEO_EXT = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}
MANUAL_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx"}
FIRMWARE_EXT = {".zip", ".bin", ".img", ".exe", ".pkg", ".tar", ".gz", ".rar", ".cab"}

MIN_TOK = 3  # 短于该长度的产品型号不会参与匹配，避免误命中


# --------------------------------------------------------------------------- #
# 归一化 / 匹配
# --------------------------------------------------------------------------- #
def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_products():
    out = []
    for f in sorted(glob.glob(os.path.join(PRODUCTS_DIR, "*.yml"))):
        try:
            import yaml  # 延迟导入，缺失时给出清晰报错
        except ImportError:
            sys.exit("需要 PyYAML：在 venv 中执行  pip install pyyaml")
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        slug = os.path.basename(f)[:-4]
        out.append((slug, data))
    return out


def build_index(products):
    idx = []
    for slug, data in products:
        model = data.get("model") or ""
        chunks = [model]
        for key in ("name", "series"):
            v = data.get(key)
            if isinstance(v, dict):
                chunks += [v.get("es", ""), v.get("en", "")]
            elif isinstance(v, str):
                chunks.append(v)
        toks = {norm(t) for t in chunks if norm(t)}
        toks.add(norm(slug))
        idx.append((slug, norm(model), toks))
    return idx


def match_product(fn_norm, index, mapping):
    # 1) 显式映射优先
    if fn_norm in mapping:
        return mapping[fn_norm], -1
    # 2) 最长匹配词
    best, best_len = None, 0
    for slug, _model, toks in index:
        bl = max((len(t) for t in toks if len(t) >= MIN_TOK and t in fn_norm), default=0)
        if bl > best_len:
            best_len, best = bl, slug
    return best, best_len


# --------------------------------------------------------------------------- #
# Drive 链接规整
# --------------------------------------------------------------------------- #
def drive_link(raw, direct=False):
    raw = (raw or "").strip()
    if not raw:
        return None
    fid = None
    m = re.search(r"/file/d/([\w-]+)", raw)
    if m:
        fid = m.group(1)
    else:
        m = re.search(r"[?&]id=([\w-]+)", raw)
        if m:
            fid = m.group(1)
    if not fid and re.fullmatch(r"[\w-]{20,}", raw):
        fid = raw
    if fid:
        return (
            f"https://drive.google.com/uc?export=download&id={fid}"
            if direct
            else f"https://drive.google.com/file/d/{fid}/view?usp=sharing"
        )
    return raw  # 已是完整链接则原样保留


# --------------------------------------------------------------------------- #
# 类型推断
# --------------------------------------------------------------------------- #
def infer_type(filename, explicit):
    if explicit in COLLECTIONS:
        return explicit
    ext = os.path.splitext(filename)[1].lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in MANUAL_EXT:
        return "manual"
    if ext in FIRMWARE_EXT:
        return "firmware"
    return None


# --------------------------------------------------------------------------- #
# YAML 生成
# --------------------------------------------------------------------------- #
def yml_quote(s):
    return '"' + (s or "").replace('"', "'") + '"'


def derive_title(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    return re.sub(r"\s+", " ", base.replace("_", " ").replace("-", " ")).strip()


def unique_filename(directory, primary):
    base = re.sub(r"[^a-z0-9-]", "-", primary.lower())
    path = os.path.join(directory, f"{base}.yml")
    if not os.path.exists(path):
        return path
    i = 2
    while os.path.exists(os.path.join(directory, f"{base}-{i}.yml")):
        i += 1
    return os.path.join(directory, f"{base}-{i}.yml")


def build_yaml(rtype, rec):
    title_es = rec["title_es"] or derive_title(rec["filename"])
    title_en = rec["title_en"] or title_es
    products_yaml = "\n".join(f"  - {p}" for p in rec["products"])
    date_val = rec["date"] or date.today().isoformat()
    if rtype == "video":
        return (
            f"# Auto-generated by scripts/drive_to_repo.py (type=video)\n"
            f"title:\n  es: {yml_quote(title_es)}\n  en: {yml_quote(title_en)}\n"
            f"products:\n{products_yaml}\n"
            f"date: {date_val}\n"
            f'duration: "{rec["duration"] or ""}"\n'
            f"url: {yml_quote(rec['url'])}\n"
            f"external: true\n"
            f"cover: ''\n"
            f"summary: ''\n"
        ), unique_filename(COLLECTIONS["video"], rec["title_es"] or rec["filename"])
    if rtype == "manual":
        doctype = rec.get("docType") or "user-guide"
        return (
            f"# Auto-generated by scripts/drive_to_repo.py (type=manual)\n"
            f"title:\n  es: {yml_quote(title_es)}\n  en: {yml_quote(title_en)}\n"
            f"docType: {doctype}\n"
            f"products:\n{products_yaml}\n"
            f"version: {yml_quote(rec.get('version') or '')}\n"
            f"date: {date_val}\n"
            f"fileEs: ''\n"
            f"fileEn: ''\n"
            f"externalUrl: {yml_quote(rec['url'])}\n"
            f"summary: ''\n"
        ), unique_filename(COLLECTIONS["manual"], rec["title_es"] or rec["filename"])
    # firmware
    version = rec.get("version") or ""
    if not version:
        return None, None  # 缺 version，调用方报错
    return (
        f"# Auto-generated by scripts/drive_to_repo.py (type=firmware)\n"
        f"version: {yml_quote(version)}\n"
        f"products:\n{products_yaml}\n"
        f"date: {date_val}\n"
        f"releaseNotes:\n  es: ''\n  en: ''\n"
        f"fileSize: ''\n"
        f"checksum: ''\n"
        f"downloadUrl: {yml_quote(rec['url'])}\n"
        f"mandatory: false\n"
        f"type: firmware\n"
    ), unique_filename(COLLECTIONS["firmware"], f"fw-{rec['products'][0]}-{version}")


# --------------------------------------------------------------------------- #
# Drive API 文件夹列举（可选，需凭据）
# --------------------------------------------------------------------------- #
def list_drive_folder(folder_id):
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build as gc_build
    except ImportError:
        sys.exit(
            "Drive API 模式需要安装：pip install google-api-python-client google-auth\n"
            "并准备服务账号 credentials.json（GOOGLE_APPLICATION_CREDENTIALS 指向它）。"
        )
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    svc = gc_build("drive", "v3", credentials=creds)
    rows = []
    page = None
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces="drive",
            fields="nextPageToken, files(id, name)",
            pageToken=page,
        ).execute()
        for f in resp.get("files", []):
            rows.append({"filename": f["name"], "drive_url": f["id"]})
        page = resp.get("nextPageToken")
        if not page:
            break
    return rows


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def load_mapping(path):
    m = {}
    if not path:
        return m
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            fn = (row.get("filename") or "").strip()
            slug = (row.get("slug") or row.get("products") or "").strip()
            if fn and slug:
                m[norm(fn)] = slug
    return m


def main():
    args = sys.argv[1:]
    manifest_paths, folder_id, do_write, do_commit, mapping_path, direct = [], None, False, False, None, False
    for a in args:
        if a == "--write":
            do_write = True
        elif a == "--commit":
            do_write, do_commit = True, True
        elif a == "--direct":
            direct = True
        elif a.startswith("--folder-id="):
            folder_id = a.split("=", 1)[1]
        elif a.startswith("--mapping="):
            mapping_path = a.split("=", 1)[1]
        elif not a.startswith("--"):
            manifest_paths.append(a)

    if folder_id:
        print(f"Listing Drive folder {folder_id} ...")
        folder_rows = list_drive_folder(folder_id)
        print(f"  found {len(folder_rows)} files")
    else:
        if not manifest_paths:
            sys.exit("用法: python drive_to_repo.py manifest.csv [--write] [--commit] [--mapping=map.csv] [--direct]\n"
                     "   或: python drive_to_repo.py --folder-id=<ID> [--write] [--commit]")
        folder_rows = None

    products = load_products()
    if not products:
        sys.exit(f"未在 {PRODUCTS_DIR} 找到任何产品")
    index = build_index(products)
    mapping = load_mapping(mapping_path)

    rows = folder_rows if folder_rows is not None else []
    if folder_rows is None:
        for mp in manifest_paths:
            with open(mp, newline="", encoding="utf-8-sig") as fh:
                for r in csv.DictReader(fh):
                    rows.append(r)

    created, skipped, matched = [], [], 0
    for rec in rows:
        filename = (rec.get("filename") or "").strip()
        if not filename:
            continue
        url = drive_link((rec.get("drive_url") or "").strip(), direct=direct)
        if not url:
            skipped.append((filename, "无 drive_url"))
            continue
        rtype = infer_type(filename, (rec.get("type") or "").strip().lower())
        if not rtype:
            skipped.append((filename, "无法推断类型（请指定 type 列）"))
            continue
        slug, score = match_product(norm(filename), index, mapping)
        if not slug:
            skipped.append((filename, "未匹配到产品"))
            continue
        rec.update({
            "filename": filename, "url": url, "products": [slug],
            "title_es": (rec.get("title_es") or "").strip(),
            "title_en": (rec.get("title_en") or "").strip(),
            "date": (rec.get("date") or "").strip(),
            "duration": (rec.get("duration") or "").strip(),
        })
        content, out_path = build_yaml(rtype, rec)
        if content is None:
            skipped.append((filename, "firmware 缺少 version"))
            continue
        action = "WOULD CREATE" if not do_write else "CREATED"
        print(f"[{action}] {os.path.basename(out_path)}  ({rtype} <- {slug})  {filename}")
        matched += 1
        if do_write:
            with open(out_path, "w", encoding="utf-8") as of:
                of.write(content)
            created.append(out_path)

    for fn, why in skipped:
        print(f"[SKIP] {fn}: {why}")

    print(f"\n匹配成功 {matched} 个，跳过 {len(skipped)} 个"
          + ("" if do_write else "  （试运行，加 --write 才真正写入）"))

    if do_commit and created:
        subprocess.run(["git", "add", *created], check=True, cwd=ROOT)
        msg = f"chore: add {len(created)} resources from Google Drive (auto-matched by filename)"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=ROOT)
        print("已提交到 git。")


if __name__ == "__main__":
    main()
