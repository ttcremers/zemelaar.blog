#!/usr/bin/env python3
"""Check whether WordPress media inventory files exist in the media archive.

Input:
    migration/media-inventory.csv
    wordpress-data/media.tar

Output:
    migration/media-archive-check.md

This script does not extract files and does not modify wordpress-data/.
It only reads the tar index and compares expected filenames.
"""

from __future__ import annotations

import argparse
import csv
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class MediaRow:
    post_id: str
    title: str
    status: str
    post_date: str
    slug: str
    old_url: str
    attachment_url: str
    attached_file: str
    parent_id: str
    creator: str

    @property
    def expected_relative_path(self) -> str:
        """Return the expected uploads-relative path from the attachment URL.

        Example:
        https://example/wp-content/uploads/2025/06/image.jpg
        -> 2025/06/image.jpg
        """
        parsed = urlparse(self.attachment_url)
        marker = "/wp-content/uploads/"
        if marker not in parsed.path:
            return ""
        return parsed.path.split(marker, 1)[1].lstrip("/")

    @property
    def expected_filename(self) -> str:
        return Path(self.expected_relative_path).name


def read_media_inventory(input_file: Path) -> list[MediaRow]:
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_fields = {
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
        }
        missing_fields = required_fields - set(reader.fieldnames or [])
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Missing required fields in media inventory: {missing}")

        rows: list[MediaRow] = []
        for row in reader:
            rows.append(
                MediaRow(
                    post_id=row.get("post_id", "").strip(),
                    title=row.get("title", "").strip(),
                    status=row.get("status", "").strip(),
                    post_date=row.get("post_date", "").strip(),
                    slug=row.get("slug", "").strip(),
                    old_url=row.get("old_url", "").strip(),
                    attachment_url=row.get("attachment_url", "").strip(),
                    attached_file=row.get("attached_file", "").strip(),
                    parent_id=row.get("parent_id", "").strip(),
                    creator=row.get("creator", "").strip(),
                )
            )
        return rows


def list_tar_files(archive_file: Path) -> set[str]:
    names: set[str] = set()
    with tarfile.open(archive_file, "r:*") as archive:
        for member in archive.getmembers():
            if member.isfile():
                normalized = member.name.replace("\\", "/").lstrip("./")
                names.add(normalized)
    return names


def find_match(expected_relative_path: str, tar_files: set[str]) -> str:
    if not expected_relative_path:
        return ""

    expected_relative_path = expected_relative_path.replace("\\", "/").lstrip("/")

    for name in tar_files:
        if name.endswith(expected_relative_path):
            return name

    expected_filename = Path(expected_relative_path).name
    filename_matches = [name for name in tar_files if Path(name).name == expected_filename]
    if len(filename_matches) == 1:
        return filename_matches[0]

    return ""


def markdown_table_row(values: list[str]) -> str:
    escaped = [value.replace("|", "\\|") for value in values]
    return "| " + " | ".join(escaped) + " |"


def write_report(rows: list[MediaRow], tar_files: set[str], output_file: Path) -> tuple[int, int]:
    matched: list[tuple[MediaRow, str]] = []
    missing: list[MediaRow] = []
    unattached = [row for row in rows if row.parent_id in {"", "0"}]

    for row in rows:
        match = find_match(row.expected_relative_path, tar_files)
        if match:
            matched.append((row, match))
        else:
            missing.append(row)

    referenced_filenames = {match for _, match in matched}
    unreferenced_archive_files = sorted(tar_files - referenced_filenames)

    with output_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Media Archive Check\n\n")
        handle.write("Generated from `migration/media-inventory.csv` and the local media tar archive.\n\n")

        handle.write("## Summary\n\n")
        handle.write(markdown_table_row(["Metric", "Count"]))
        handle.write("\n")
        handle.write(markdown_table_row(["---", "---:"]))
        handle.write("\n")
        handle.write(markdown_table_row(["Inventory media rows", str(len(rows))]))
        handle.write("\n")
        handle.write(markdown_table_row(["Archive files", str(len(tar_files))]))
        handle.write("\n")
        handle.write(markdown_table_row(["Matched media rows", str(len(matched))]))
        handle.write("\n")
        handle.write(markdown_table_row(["Missing media rows", str(len(missing))]))
        handle.write("\n")
        handle.write(markdown_table_row(["Unattached inventory rows", str(len(unattached))]))
        handle.write("\n")
        handle.write(markdown_table_row(["Archive files not matched by inventory", str(len(unreferenced_archive_files))]))
        handle.write("\n\n")

        if missing:
            handle.write("## Missing from archive\n\n")
            handle.write(markdown_table_row(["Post ID", "Title", "Expected path", "Attachment URL"]))
            handle.write("\n")
            handle.write(markdown_table_row(["---", "---", "---", "---"]))
            handle.write("\n")
            for row in missing:
                handle.write(markdown_table_row([row.post_id, row.title, row.expected_relative_path, row.attachment_url]))
                handle.write("\n")
            handle.write("\n")

        if unattached:
            handle.write("## Unattached or structural media\n\n")
            handle.write("These rows have `parent_id` 0 or empty. They may be logos, cropped assets, loose uploads, or unused media.\n\n")
            handle.write(markdown_table_row(["Post ID", "Title", "Expected path", "Attachment URL"]))
            handle.write("\n")
            handle.write(markdown_table_row(["---", "---", "---", "---"]))
            handle.write("\n")
            for row in unattached:
                handle.write(markdown_table_row([row.post_id, row.title, row.expected_relative_path, row.attachment_url]))
                handle.write("\n")
            handle.write("\n")

        if unreferenced_archive_files:
            handle.write("## Archive files not matched by inventory\n\n")
            handle.write("These files exist in the tar archive but were not matched to an inventory attachment row. Review before deleting or ignoring.\n\n")
            handle.write("```text\n")
            for name in unreferenced_archive_files:
                handle.write(name)
                handle.write("\n")
            handle.write("```\n\n")

        handle.write("## Notes\n\n")
        handle.write("This check matches expected WordPress upload paths against tar member paths. ")
        handle.write("It does not extract files, compare checksums, or determine whether a media item is actually referenced inside post content.\n")

    return len(matched), len(missing)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check WordPress media tar archive against media inventory")
    parser.add_argument(
        "--inventory",
        default="migration/media-inventory.csv",
        help="Path to media inventory CSV",
    )
    parser.add_argument(
        "--archive",
        default="wordpress-data/media.tar",
        help="Path to WordPress media tar archive",
    )
    parser.add_argument(
        "--output",
        default="migration/media-archive-check.md",
        help="Path for generated Markdown report",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    inventory_file = Path(args.inventory)
    archive_file = Path(args.archive)
    output_file = Path(args.output)

    if not inventory_file.exists():
        print(f"Error: media inventory not found: {inventory_file}", file=sys.stderr)
        return 1

    if not archive_file.exists():
        print(f"Error: media archive not found: {archive_file}", file=sys.stderr)
        return 1

    output_file.parent.mkdir(parents=True, exist_ok=True)

    rows = read_media_inventory(inventory_file)
    tar_files = list_tar_files(archive_file)
    matched_count, missing_count = write_report(rows, tar_files, output_file)

    print("Media archive check complete")
    print()
    print(f"Inventory rows: {len(rows)}")
    print(f"Archive files: {len(tar_files)}")
    print(f"Matched rows: {matched_count}")
    print(f"Missing rows: {missing_count}")
    print(f"Wrote: {output_file}")

    return 0 if missing_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
