#!/usr/bin/env python3
"""
Bulk-import Streamax KB documents from CSV into the content collections:
  - src/content/manual/*.yml    (Datasheet / User Guide / Wiring Diagram / Certification)
  - src/content/firmware/*.yml  (firmware + tool releases with release notes)

Usage:
  python scripts/import_docs.py manuals  [path] [--dry-run]
  python scripts/import_docs.py firmware [path] [--dry-run]
  python scripts/import_docs.py all      [--dry-run]

Defaults:
  manuals  -> scripts/manuals-import.csv
  firmware -> scripts/firmware-import.csv

Manual CSV columns:
  product, products, docType, title_es, title_en, version, date,
  fileEs, fileEn, externalUrl, summary
  A row is imported only if at least one of fileEs/fileEn/externalUrl is set.

Firmware CSV columns:
  product, products, type, version, date,
  releaseNotes_es, releaseNotes_en, downloadUrl, checksum, fileSize, mandatory
  A row is imported only if downloadUrl is set; version is required.

URLs are taken as-is (no YouTube normalization — that is video-only).
CSVs are read with utf-8-sig so Excel 'Save as CSV' BOM does not break parsing.
"""
import csv
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL_DIR = os.path.join(ROOT, "src", "content", "manual")
FIRMWARE_DIR = os.path.join(ROOT, "src", "content", "firmware")

MANUAL_DOC_TYPES = {"datasheet", "user-guide", "wiring-diagram", "certification"}
FIRMWARE_TYPES = {"firmware", "tool"}


def yml_quote(s):
    return '"' + (s or "").replace('"', "'") + '"'


def i18n_block(field, es, en):
    es = (es or "").strip()
    en = (en or "").strip()
    if not es and not en:
        return f"{field}: ''"
    return f"{field}:\n  es: {yml_quote(es)}\n  en: {yml_quote(en)}"


def unique_filename(dirpath, base):
    base = re.sub(r"[^a-z0-9-]", "-", base.lower())
    path = os.path.join(dirpath, f"{base}.yml")
    if not os.path.exists(path):
        return path
    i = 2
    while os.path.exists(os.path.join(dirpath, f"{base}-{i}.yml")):
        i += 1
    return os.path.join(dirpath, f"{base}-{i}.yml")


def resolve_products(row):
    primary = (row.get("products") or "").strip() or (row.get("product") or "").strip()
    if not primary:
        return None
    return [p.strip() for p in primary.split(",") if p.strip()]


def products_yaml(products):
    return "\n".join(f"  - {p}" for p in products)


def import_manuals(path, dry_run=False):
    created = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            products = resolve_products(row)
            if not products:
                print(f"SKIP (no product): {row.get('product')}")
                continue
            file_es = (row.get("fileEs") or "").strip()
            file_en = (row.get("fileEn") or "").strip()
            ext = (row.get("externalUrl") or "").strip()
            if not file_es and not file_en and not ext:
                continue  # nothing to import for this manual row
            doc = (row.get("docType") or "user-guide").strip()
            if doc not in MANUAL_DOC_TYPES:
                print(f"SKIP (bad docType {doc!r}): {products}")
                continue
            title_es = (row.get("title_es") or "").strip()
            title_en = (row.get("title_en") or "").strip()
            if not title_es and not title_en:
                title_es = title_en = products[0]
            version = (row.get("version") or "").strip()
            date_val = (row.get("date") or "").strip() or date.today().isoformat()
            summary = (row.get("summary") or "").strip()
            content = (
                "# Imported via scripts/import_docs.py (manual)\n"
                f"title:\n  es: {yml_quote(title_es)}\n  en: {yml_quote(title_en)}\n"
                f"docType: {doc}\n"
                f"products:\n{products_yaml(products)}\n"
                f"version: {yml_quote(version) if version else '""'}\n"
                f"date: {date_val}\n"
                f"fileEs: {yml_quote(file_es) if file_es else '""'}\n"
                f"fileEn: {yml_quote(file_en) if file_en else '""'}\n"
                f"externalUrl: {yml_quote(ext) if ext else '""'}\n"
                f"summary: {yml_quote(summary) if summary else '""'}\n"
            )
            out = unique_filename(MANUAL_DIR, f"{products[0]}-{doc}")
            created += 1
            if dry_run:
                print(f"[DRY-RUN] would CREATE {os.path.basename(out)} -> {products}")
                print("---8<---\n" + content.rstrip("\n") + "\n---8<---")
            else:
                os.makedirs(MANUAL_DIR, exist_ok=True)
                with open(out, "w", encoding="utf-8") as of:
                    of.write(content)
                print(f"CREATED {os.path.basename(out)} -> {products}")
    print(f"Manuals total created: {created}" + ("  (dry-run, nothing written)" if dry_run else ""))


def import_firmware(path, dry_run=False):
    created = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            products = resolve_products(row)
            if not products:
                print(f"SKIP (no product): {row.get('product')}")
                continue
            download = (row.get("downloadUrl") or "").strip()
            if not download:
                continue  # firmware needs a download url
            version = (row.get("version") or "").strip()
            if not version:
                print(f"SKIP (no version): {products}")
                continue
            ftype = (row.get("type") or "firmware").strip()
            if ftype not in FIRMWARE_TYPES:
                ftype = "firmware"
            date_val = (row.get("date") or "").strip() or date.today().isoformat()
            mand = (row.get("mandatory") or "").strip().lower() in ("y", "yes", "true", "1")
            notes = i18n_block(
                "releaseNotes", row.get("releaseNotes_es", ""), row.get("releaseNotes_en", "")
            )
            checksum = (row.get("checksum") or "").strip()
            file_size = (row.get("fileSize") or "").strip()
            content = (
                "# Imported via scripts/import_docs.py (firmware)\n"
                f"version: {yml_quote(version)}\n"
                f"products:\n{products_yaml(products)}\n"
                f"date: {date_val}\n"
                f"{notes}\n"
                f"fileSize: {yml_quote(file_size) if file_size else '""'}\n"
                f"checksum: {yml_quote(checksum) if checksum else '""'}\n"
                f"downloadUrl: {yml_quote(download)}\n"
                f"mandatory: {str(mand).lower()}\n"
                f"type: {ftype}\n"
            )
            out = unique_filename(FIRMWARE_DIR, f"{products[0]}-{ftype}-{version}")
            created += 1
            if dry_run:
                print(f"[DRY-RUN] would CREATE {os.path.basename(out)} -> {products}")
                print("---8<---\n" + content.rstrip("\n") + "\n---8<---")
            else:
                os.makedirs(FIRMWARE_DIR, exist_ok=True)
                with open(out, "w", encoding="utf-8") as of:
                    of.write(content)
                print(f"CREATED {os.path.basename(out)} -> {products}")
    print(f"Firmware total created: {created}" + ("  (dry-run, nothing written)" if dry_run else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    positional = [a for a in args if not a.startswith("--")]
    if not positional:
        print("Usage: import_docs.py (manuals|firmware|all) [csv] [--dry-run]")
        sys.exit(1)
    kind = positional[0]
    csv_path = positional[1] if len(positional) > 1 else None
    if kind in ("manuals", "all"):
        p = csv_path or os.path.join(ROOT, "scripts", "manuals-import.csv")
        import_manuals(p, dry_run=dry_run)
    if kind in ("firmware", "all"):
        p = csv_path or os.path.join(ROOT, "scripts", "firmware-import.csv")
        import_firmware(p, dry_run=dry_run)
    if kind not in ("manuals", "firmware", "all"):
        print(f"Unknown kind: {kind!r} (use 'manuals', 'firmware' or 'all')")
        sys.exit(1)
