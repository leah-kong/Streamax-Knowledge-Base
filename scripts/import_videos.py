#!/usr/bin/env python3
"""
Bulk-import Streamax KB videos from a CSV into src/content/video/*.yml.

Usage:
  python scripts/import_videos.py --template
      -> writes scripts/videos-import.csv with one row per product (url empty).
  python scripts/import_videos.py [path/to/videos-import.csv] [--dry-run]
      -> creates one yml record per row that has a non-empty url.
         --dry-run prints what would be written without touching the repo.

CSV columns:
  product    primary product slug (used for the filename + default products)
  products   optional override: comma-separated slugs sharing ONE video
  url        YouTube link / youtu.be / embed / shorts / pasted <iframe> / direct .mp4
  title_es   optional Spanish title (falls back to product slug)
  title_en   optional English title (falls back to product slug)
  date       YYYY-MM-DD (defaults to today)
  duration   optional "MM:SS"

URLs are normalized:
  - pasted <iframe> HTML -> src extracted
  - YouTube -> canonical watch?v= (inline-embeddable)
  - .mp4/.webm/.mov -> external:false (native <video> player)
  - anything else -> external link
"""
import csv
import glob
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "src", "content", "video")


def normalize_url(url):
    url = (url or "").strip()
    if not url:
        return None, True
    if "<iframe" in url.lower():
        m = re.search(r'src=["\']([^"\']+)["\']', url, re.I)
        if m:
            url = m.group(1)
    m = re.search(
        r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([\w-]{11})", url
    )
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}", True
    if url.lower().endswith((".mp4", ".webm", ".ogg", ".mov")):
        return url, False
    return url, True


def unique_filename(primary):
    base = re.sub(r"[^a-z0-9-]", "-", primary.lower())
    path = os.path.join(VIDEO_DIR, f"{base}.yml")
    if not os.path.exists(path):
        return path
    i = 2
    while os.path.exists(os.path.join(VIDEO_DIR, f"{base}-{i}.yml")):
        i += 1
    return os.path.join(VIDEO_DIR, f"{base}-{i}.yml")


def make_template():
    products = sorted(
        os.path.basename(f)[:-4]
        for f in glob.glob(os.path.join(ROOT, "src", "content", "products", "*.yml"))
    )
    out = os.path.join(ROOT, "scripts", "videos-import.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["product", "products", "url", "title_es", "title_en", "date", "duration"])
        for p in products:
            w.writerow([p, "", "", "", "", "", ""])
    print(f"Wrote template with {len(products)} product rows -> {out}")


def yml_quote(s):
    return '"' + s.replace('"', "'") + '"'


def import_csv(path, dry_run=False):
    created = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            url_raw = (row.get("url") or "").strip()
            if not url_raw:
                continue
            primary = (row.get("products") or "").strip() or (row.get("product") or "").strip()
            if not primary:
                print(f"SKIP (no product): {row}")
                continue
            products = [p.strip() for p in primary.split(",") if p.strip()]
            norm, external = normalize_url(url_raw)
            title_es = (row.get("title_es") or "").strip()
            title_en = (row.get("title_en") or "").strip()
            if not title_es and not title_en:
                title_es = title_en = products[0]
            date_val = (row.get("date") or "").strip() or date.today().isoformat()
            duration = (row.get("duration") or "").strip()
            products_yaml = "\n".join(f"  - {p}" for p in products)
            content = (
                "# Imported via scripts/import_videos.py\n"
                f"title:\n  es: {yml_quote(title_es)}\n  en: {yml_quote(title_en)}\n"
                f"products:\n{products_yaml}\n"
                f"date: {date_val}\n"
                f'duration: "{duration}"\n'
                f"url: {yml_quote(norm)}\n"
                f"external: {str(external).lower()}\n"
                "cover: ''\n"
                "summary: ''\n"
            )
            out = unique_filename(products[0])
            created += 1
            if dry_run:
                print(f"[DRY-RUN] would CREATE {os.path.basename(out)} -> {products} ({norm})")
                print("---8<---")
                print(content.rstrip("\n"))
                print("---8<---")
            else:
                with open(out, "w", encoding="utf-8") as of:
                    of.write(content)
                print(f"CREATED {os.path.basename(out)} -> {products} ({norm})")
    print(f"Total created: {created}" + ("  (dry-run, nothing written)" if dry_run else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    positional = [a for a in args if not a.startswith("--")]
    if "--template" in args:
        make_template()
    else:
        csv_path = positional[0] if positional else os.path.join(ROOT, "scripts", "videos-import.csv")
        import_csv(csv_path, dry_run=dry_run)
