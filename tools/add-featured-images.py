#!/usr/bin/env python3
"""Add featured images to converted Hugo blog posts."""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"wp": "http://wordpress.org/export/1.2/"}


def t(node):
    return "" if node is None or node.text is None else node.text.strip()


def wp(item, name):
    return t(item.find(name, NS))


def meta(item, key):
    for m in item.findall("wp:postmeta", NS):
        if wp(m, "wp:meta_key") == key:
            return wp(m, "wp:meta_value")
    return ""


def read_thumbnails(export_path: Path):
    root = ET.parse(export_path).getroot()
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("No channel found in export")

    result = {}
    for item in channel.findall("item"):
        if wp(item, "wp:post_type") != "post" or wp(item, "wp:status") != "publish":
            continue
        slug = wp(item, "wp:post_name")
        thumb_id = meta(item, "_thumbnail_id")
        title = t(item.find("title"))
        if slug and thumb_id:
            result[slug] = {"title": title, "thumb_id": thumb_id}
    return result


def read_attachment_urls(path: Path):
    result = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            post_id = row.get("post_id", "").strip()
            url = row.get("attachment_url", "").strip()
            if post_id and url:
                result[post_id] = url
    return result


def read_rewrite_map(path: Path):
    result = {}
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            old = row.get("old_attachment_url", "").strip()
            new = row.get("new_site_path", "").strip()
            if old and new:
                result[old] = new
    return result


def escape_alt(text):
    return text.replace("[", "\\[").replace("]", "\\]")


def add_after_frontmatter(content, image_line):
    marker = "---\n"
    if not content.startswith(marker):
        return image_line + "\n" + content
    end = content.find("\n---\n", len(marker))
    if end == -1:
        return image_line + "\n" + content
    split_at = end + len("\n---\n")
    return content[:split_at] + "\n" + image_line + "\n" + content[split_at:].lstrip("\n")


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", default="wordpress-data/export.xml")
    parser.add_argument("--media-inventory", default="migration/media-inventory.csv")
    parser.add_argument("--media-rewrite-map", default="migration/media-rewrite-map.csv")
    parser.add_argument("--content-dir", default="site/content/blog")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    thumbs = read_thumbnails(Path(args.export))
    urls = read_attachment_urls(Path(args.media_inventory))
    rewrite = read_rewrite_map(Path(args.media_rewrite_map))
    content_dir = Path(args.content_dir)

    updated = 0
    already = 0
    missing = 0

    for slug, info in thumbs.items():
        post_file = content_dir / f"{slug}.md"
        old_url = urls.get(info["thumb_id"], "")
        new_path = rewrite.get(old_url, "")
        if not post_file.exists() or not new_path:
            missing += 1
            continue
        content = post_file.read_text(encoding="utf-8")
        if new_path in content:
            already += 1
            continue
        image_line = f"![{escape_alt(info['title'])}]({new_path})\n"
        post_file.write_text(add_after_frontmatter(content, image_line), encoding="utf-8")
        updated += 1

    print("Featured image pass complete")
    print(f"Posts with thumbnails: {len(thumbs)}")
    print(f"Updated posts: {updated}")
    print(f"Already present: {already}")
    print(f"Missing mappings: {missing}")
    return 0 if missing == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
