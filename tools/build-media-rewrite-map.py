#!/usr/bin/env python3
"""Generate a reviewed media rewrite map for Hugo uploads.

Inputs:
    migration/media-inventory.csv
    migration/url-map.csv

Output:
    migration/media-rewrite-map.csv

The generated names are context-based, not visually inspected.
They use the parent post slug when available, plus a cleaned attachment title
when that title is useful. Opaque filenames fall back to numbered image names.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class MediaRow:
    post_id: str
    title: str
    attachment_url: str
    attached_file: str
    parent_id: str

    @property
    def old_relative_path(self) -> str:
        parsed = urlparse(self.attachment_url)
        marker = "/wp-content/uploads/"
        if marker not in parsed.path:
            return ""
        return parsed.path.split(marker, 1)[1].lstrip("/")

    @property
    def extension(self) -> str:
        suffix = Path(urlparse(self.attachment_url).path).suffix.lower()
        return suffix or Path(self.attached_file).suffix.lower()


@dataclass(frozen=True)
class UrlMapRow:
    post_id: str
    title: str
    slug: str
    post_type: str
    status: str


def read_media_inventory(input_file: Path) -> list[MediaRow]:
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[MediaRow] = []
        for row in reader:
            rows.append(
                MediaRow(
                    post_id=row.get("post_id", "").strip(),
                    title=row.get("title", "").strip(),
                    attachment_url=row.get("attachment_url", "").strip(),
                    attached_file=row.get("attached_file", "").strip(),
                    parent_id=row.get("parent_id", "").strip(),
                )
            )
        return rows


def read_url_map(input_file: Path) -> dict[str, UrlMapRow]:
    rows: dict[str, UrlMapRow] = {}
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            post_id = row.get("post_id", "").strip()
            if not post_id:
                continue
            rows[post_id] = UrlMapRow(
                post_id=post_id,
                title=row.get("title", "").strip(),
                slug=row.get("slug", "").strip(),
                post_type=row.get("post_type", "").strip(),
                status=row.get("status", "").strip(),
            )
    return rows


def slugify(value: str) -> str:
    value = value.lower().strip()
    replacements = {
        "á": "a",
        "à": "a",
        "ä": "a",
        "â": "a",
        "é": "e",
        "è": "e",
        "ë": "e",
        "ê": "e",
        "í": "i",
        "ì": "i",
        "ï": "i",
        "î": "i",
        "ó": "o",
        "ò": "o",
        "ö": "o",
        "ô": "o",
        "ú": "u",
        "ù": "u",
        "ü": "u",
        "û": "u",
        "ç": "c",
        "ñ": "n",
        "’": "",
        "'": "",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def is_opaque_name(value: str) -> bool:
    clean = slugify(Path(value).stem)
    if not clean:
        return True

    # Camera names, hashes, UUID-ish names, and WordPress crop names are not useful long-term names.
    if re.fullmatch(r"[a-f0-9]{4,}-.+", clean):
        return True
    if re.fullmatch(r"[a-f0-9-]{12,}", clean):
        return True
    if re.fullmatch(r"dscf?\d+", clean):
        return True
    if re.fullmatch(r"do\d+", clean):
        return True
    if clean.startswith("cropped-"):
        return True
    if clean in {"image", "photo", "img", "untitled", "kopie"}:
        return True

    return False


def descriptor_for(row: MediaRow, sequence: int) -> str:
    title_slug = slugify(row.title)
    filename_slug = slugify(Path(row.old_relative_path).stem)

    if title_slug and not is_opaque_name(row.title):
        return title_slug
    if filename_slug and not is_opaque_name(filename_slug):
        return filename_slug
    return f"beeld-{sequence:02d}"


def unique_path(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        used.add(candidate)
        return candidate

    stem = Path(candidate).with_suffix("").as_posix()
    suffix = Path(candidate).suffix
    counter = 2
    while True:
        next_candidate = f"{stem}-{counter}{suffix}"
        if next_candidate not in used:
            used.add(next_candidate)
            return next_candidate
        counter += 1


def build_rewrite_rows(media_rows: list[MediaRow], url_rows_by_id: dict[str, UrlMapRow]) -> list[dict[str, str]]:
    counters: dict[str, int] = defaultdict(int)
    used_paths: set[str] = set()
    output_rows: list[dict[str, str]] = []

    for row in media_rows:
        parent = url_rows_by_id.get(row.parent_id)
        extension = row.extension or ".jpg"

        if parent and parent.post_type == "post" and parent.slug:
            counters[parent.slug] += 1
            descriptor = descriptor_for(row, counters[parent.slug])
            if descriptor == parent.slug:
                filename = f"{descriptor}{extension}"
            else:
                filename = f"{parent.slug}-{descriptor}{extension}"
            new_site_path = f"/uploads/{parent.slug}/{filename}"
            review_note = "review_generated_from_parent_post"
            post_slug = parent.slug
            post_title = parent.title
        else:
            counters["site"] += 1
            descriptor = descriptor_for(row, counters["site"])
            filename = f"{descriptor}{extension}"
            new_site_path = f"/uploads/site/{filename}"
            review_note = "manual_review_unattached_or_structural_media"
            post_slug = ""
            post_title = ""

        new_site_path = unique_path(new_site_path, used_paths)

        output_rows.append(
            {
                "old_attachment_url": row.attachment_url,
                "old_relative_path": row.old_relative_path,
                "new_site_path": new_site_path,
                "parent_id": row.parent_id,
                "post_slug": post_slug,
                "post_title": post_title,
                "media_title": row.title,
                "review_note": review_note,
            }
        )

    return output_rows


def write_csv(output_file: Path, rows: list[dict[str, str]]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "old_attachment_url",
        "old_relative_path",
        "new_site_path",
        "parent_id",
        "post_slug",
        "post_title",
        "media_title",
        "review_note",
    ]
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate media rewrite map for date-free Hugo media paths")
    parser.add_argument("--media-inventory", default="migration/media-inventory.csv", help="Path to media inventory CSV")
    parser.add_argument("--url-map", default="migration/url-map.csv", help="Path to URL map CSV")
    parser.add_argument("--output", default="migration/media-rewrite-map.csv", help="Path to generated media rewrite map")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    media_inventory_file = Path(args.media_inventory)
    url_map_file = Path(args.url_map)
    output_file = Path(args.output)

    for required_file in [media_inventory_file, url_map_file]:
        if not required_file.exists():
            print(f"Error: required file not found: {required_file}", file=sys.stderr)
            return 1

    media_rows = read_media_inventory(media_inventory_file)
    url_rows_by_id = read_url_map(url_map_file)
    rewrite_rows = build_rewrite_rows(media_rows, url_rows_by_id)
    write_csv(output_file, rewrite_rows)

    manual_review = sum(1 for row in rewrite_rows if row["review_note"].startswith("manual_review"))

    print("Media rewrite map complete")
    print()
    print(f"Media rows: {len(media_rows)}")
    print(f"Rewrite rows: {len(rewrite_rows)}")
    print(f"Manual review rows: {manual_review}")
    print(f"Wrote: {output_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
