#!/usr/bin/env python3
"""Inspect a WordPress WXR export and generate migration inventories.

This script is intentionally read-only with regard to wordpress-data/.
It reads a WordPress XML export and writes CSV reports to migration/.

It does not convert content to Hugo yet.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "wp": "http://wordpress.org/export/1.2/",
}

DEFAULT_SOURCE_DOMAIN = "https://zemelaarblog.wordpress.com"
DEFAULT_TARGET_DOMAIN = "https://zemelaar.blog"


@dataclass(frozen=True)
class WpItem:
    post_id: str
    title: str
    post_type: str
    status: str
    post_date: str
    post_date_gmt: str
    post_modified: str
    slug: str
    old_url: str
    creator: str
    parent_id: str
    categories: list[str]
    tags: list[str]
    attachment_url: str
    attached_file: str


def text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def child_text(item: ET.Element, path: str) -> str:
    return text(item.find(path, NS))


def postmeta(item: ET.Element, key: str) -> str:
    for meta in item.findall("wp:postmeta", NS):
        meta_key = child_text(meta, "wp:meta_key")
        if meta_key == key:
            return child_text(meta, "wp:meta_value")
    return ""


def term_names(item: ET.Element, domain: str) -> list[str]:
    names: list[str] = []
    for category in item.findall("category"):
        if category.attrib.get("domain") == domain and category.text:
            names.append(category.text.strip())
    return names


def parse_items(export_file: Path) -> list[WpItem]:
    tree = ET.parse(export_file)
    channel = tree.getroot().find("channel")
    if channel is None:
        raise ValueError("Could not find <channel> in WordPress export")

    items: list[WpItem] = []

    for item in channel.findall("item"):
        items.append(
            WpItem(
                post_id=child_text(item, "wp:post_id"),
                title=child_text(item, "title"),
                post_type=child_text(item, "wp:post_type"),
                status=child_text(item, "wp:status"),
                post_date=child_text(item, "wp:post_date"),
                post_date_gmt=child_text(item, "wp:post_date_gmt"),
                post_modified=child_text(item, "wp:post_modified"),
                slug=child_text(item, "wp:post_name"),
                old_url=child_text(item, "link"),
                creator=child_text(item, "dc:creator"),
                parent_id=child_text(item, "wp:post_parent"),
                categories=term_names(item, "category"),
                tags=term_names(item, "post_tag"),
                attachment_url=child_text(item, "wp:attachment_url"),
                attached_file=postmeta(item, "_wp_attached_file"),
            )
        )

    return items


def csv_list(values: Iterable[str]) -> str:
    return "; ".join(value for value in values if value)


def old_path(old_url: str) -> str:
    if not old_url:
        return ""
    parsed = urlparse(old_url)
    return parsed.path or "/"


def canonical_url(item: WpItem, target_domain: str) -> str:
    if item.post_type == "post":
        return f"{target_domain.rstrip('/')}/{item.slug}/"

    if item.post_type == "page":
        if item.slug in {"home", "blog"}:
            return f"{target_domain.rstrip('/')}/"
        return f"{target_domain.rstrip('/')}/{item.slug}/"

    return ""


def review_note(item: WpItem) -> str:
    if item.post_type == "page" and item.slug in {"home", "blog"}:
        return "manual_review: WordPress structural page"
    if not item.slug:
        return "manual_review: missing slug"
    return ""


def write_posts_inventory(items: list[WpItem], output_file: Path, target_domain: str) -> None:
    fields = [
        "post_id",
        "title",
        "post_type",
        "status",
        "post_date",
        "post_date_gmt",
        "post_modified",
        "slug",
        "old_url",
        "suggested_new_url",
        "creator",
        "parent_id",
        "categories",
        "tags",
        "review_note",
    ]

    rows = [item for item in items if item.post_type in {"post", "page"}]

    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow(
                {
                    "post_id": item.post_id,
                    "title": item.title,
                    "post_type": item.post_type,
                    "status": item.status,
                    "post_date": item.post_date,
                    "post_date_gmt": item.post_date_gmt,
                    "post_modified": item.post_modified,
                    "slug": item.slug,
                    "old_url": item.old_url,
                    "suggested_new_url": canonical_url(item, target_domain),
                    "creator": item.creator,
                    "parent_id": item.parent_id,
                    "categories": csv_list(item.categories),
                    "tags": csv_list(item.tags),
                    "review_note": review_note(item),
                }
            )


def write_media_inventory(items: list[WpItem], output_file: Path) -> None:
    fields = [
        "post_id",
        "title",
        "status",
        "post_date",
        "slug",
        "old_url",
        "attachment_url",
        "attached_file",
        "parent_id",
        "creator",
    ]

    rows = [item for item in items if item.post_type == "attachment"]

    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow(
                {
                    "post_id": item.post_id,
                    "title": item.title,
                    "status": item.status,
                    "post_date": item.post_date,
                    "slug": item.slug,
                    "old_url": item.old_url,
                    "attachment_url": item.attachment_url,
                    "attached_file": item.attached_file,
                    "parent_id": item.parent_id,
                    "creator": item.creator,
                }
            )


def write_url_map(items: list[WpItem], output_file: Path, target_domain: str) -> None:
    fields = [
        "old_url",
        "new_url",
        "old_path",
        "new_path",
        "title",
        "post_type",
        "status",
        "post_date",
        "slug",
        "review_note",
    ]

    rows = [
        item
        for item in items
        if item.post_type in {"post", "page"}
        and item.status == "publish"
        and item.old_url
        and item.slug
    ]

    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            new_url = canonical_url(item, target_domain)
            writer.writerow(
                {
                    "old_url": item.old_url,
                    "new_url": new_url,
                    "old_path": old_path(item.old_url),
                    "new_path": old_path(new_url),
                    "title": item.title,
                    "post_type": item.post_type,
                    "status": item.status,
                    "post_date": item.post_date,
                    "slug": item.slug,
                    "review_note": review_note(item),
                }
            )


def print_summary(items: list[WpItem], output_dir: Path) -> None:
    by_type = Counter(item.post_type or "unknown" for item in items)
    by_status = Counter(item.status or "unknown" for item in items)
    duplicate_slugs = [slug for slug, count in Counter(item.slug for item in items if item.slug).items() if count > 1]

    print("WordPress export inspection complete")
    print()
    print(f"Total items: {len(items)}")
    print("By type:")
    for key, count in sorted(by_type.items()):
        print(f"  {key}: {count}")
    print("By status:")
    for key, count in sorted(by_status.items()):
        print(f"  {key}: {count}")

    if duplicate_slugs:
        print()
        print("Warning: duplicate slugs found:")
        for slug in duplicate_slugs:
            print(f"  {slug}")

    print()
    print(f"Wrote reports to: {output_dir}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a WordPress WXR export")
    parser.add_argument(
        "--input",
        default="wordpress-data/export.xml",
        help="Path to WordPress WXR export XML",
    )
    parser.add_argument(
        "--output-dir",
        default="migration",
        help="Directory for generated CSV reports",
    )
    parser.add_argument(
        "--target-domain",
        default=DEFAULT_TARGET_DOMAIN,
        help="Canonical target domain for generated URL mapping",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    export_file = Path(args.input)
    output_dir = Path(args.output_dir)

    if not export_file.exists():
        print(f"Error: export file not found: {export_file}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    items = parse_items(export_file)

    write_posts_inventory(items, output_dir / "posts-inventory.csv", args.target_domain)
    write_media_inventory(items, output_dir / "media-inventory.csv")
    write_url_map(items, output_dir / "url-map.csv", args.target_domain)
    print_summary(items, output_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
