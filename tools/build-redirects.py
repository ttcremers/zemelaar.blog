#!/usr/bin/env python3
"""Build redirect files from the reviewed URL map.

Input:
    migration/url-map.csv

Outputs:
    migration/redirects.md      Human-readable redirect overview
    migration/_redirects        Cloudflare Pages-compatible redirect file

This script does not touch wordpress-data/ and does not deploy anything.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RedirectRow:
    old_url: str
    new_url: str
    old_path: str
    new_path: str
    title: str
    post_type: str
    status: str
    review_note: str


def read_url_map(input_file: Path) -> list[RedirectRow]:
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_fields = {
            "old_url",
            "new_url",
            "old_path",
            "new_path",
            "title",
            "post_type",
            "status",
            "review_note",
        }
        missing_fields = required_fields - set(reader.fieldnames or [])
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Missing required fields in URL map: {missing}")

        rows: list[RedirectRow] = []
        for row in reader:
            rows.append(
                RedirectRow(
                    old_url=row.get("old_url", "").strip(),
                    new_url=row.get("new_url", "").strip(),
                    old_path=row.get("old_path", "").strip(),
                    new_path=row.get("new_path", "").strip(),
                    title=row.get("title", "").strip(),
                    post_type=row.get("post_type", "").strip(),
                    status=row.get("status", "").strip(),
                    review_note=row.get("review_note", "").strip(),
                )
            )
        return rows


def should_redirect(row: RedirectRow) -> bool:
    if row.status != "publish":
        return False
    if not row.old_path or not row.new_path:
        return False
    if row.old_path == row.new_path:
        return False
    if row.review_note.startswith("manual_review"):
        return False
    return True


def cloudflare_redirect_line(row: RedirectRow) -> str:
    return f"{row.old_path} {row.new_path} 301"


def write_cloudflare_redirects(rows: list[RedirectRow], output_file: Path) -> int:
    redirect_rows = [row for row in rows if should_redirect(row)]

    with output_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Generated from migration/url-map.csv\n")
        handle.write("# Date-based legacy WordPress paths -> canonical Zemelaar slug paths\n")
        handle.write("\n")
        for row in redirect_rows:
            handle.write(cloudflare_redirect_line(row))
            handle.write("\n")

    return len(redirect_rows)


def write_markdown_report(rows: list[RedirectRow], output_file: Path) -> int:
    redirect_rows = [row for row in rows if should_redirect(row)]
    manual_review_rows = [row for row in rows if row.review_note.startswith("manual_review")]

    with output_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Redirect Map\n")
        handle.write("\n")
        handle.write("Generated from `migration/url-map.csv`.\n")
        handle.write("\n")
        handle.write("These redirects map old date-based WordPress paths to canonical date-free Zemelaar paths.\n")
        handle.write("\n")
        handle.write("## Cloudflare Pages redirects\n")
        handle.write("\n")
        handle.write("```text\n")
        for row in redirect_rows:
            handle.write(cloudflare_redirect_line(row))
            handle.write("\n")
        handle.write("```\n")
        handle.write("\n")

        if manual_review_rows:
            handle.write("## Manual review\n")
            handle.write("\n")
            handle.write("These rows were not emitted as redirects because they are structural WordPress pages or otherwise marked for review.\n")
            handle.write("\n")
            handle.write("| Title | Old path | New path | Note |\n")
            handle.write("|---|---|---|---|\n")
            for row in manual_review_rows:
                handle.write(f"| {row.title} | `{row.old_path}` | `{row.new_path}` | {row.review_note} |\n")
            handle.write("\n")

        handle.write("## WordPress.com subdomain note\n")
        handle.write("\n")
        handle.write("Redirects from `zemelaarblog.wordpress.com` cannot be fully controlled from Cloudflare Pages. ")
        handle.write("They depend on WordPress.com redirect/domain options. The redirects generated here are for paths served by `zemelaar.blog`.\n")

    return len(redirect_rows)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build redirects from migration/url-map.csv")
    parser.add_argument(
        "--input",
        default="migration/url-map.csv",
        help="Path to URL map CSV generated by inspect-wp-export.py",
    )
    parser.add_argument(
        "--output-dir",
        default="migration",
        help="Directory for generated redirect files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    input_file = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_file.exists():
        print(f"Error: URL map not found: {input_file}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_url_map(input_file)

    redirects_count = write_cloudflare_redirects(rows, output_dir / "_redirects")
    write_markdown_report(rows, output_dir / "redirects.md")

    print("Redirect map build complete")
    print()
    print(f"Input rows: {len(rows)}")
    print(f"Redirects emitted: {redirects_count}")
    print(f"Wrote: {output_dir / 'redirects.md'}")
    print(f"Wrote: {output_dir / '_redirects'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
