#!/usr/bin/env python3
"""Convert published WordPress posts to first-pass Hugo Markdown files.

Inputs:
    wordpress-data/export.xml
    migration/url-map.csv
    migration/media-inventory.csv

Output:
    site/content/posts/<slug>.md

This is a deliberately conservative first-pass converter.
It does not rewrite prose, rename slugs, rename media files, deploy, or touch DNS.
It skips WordPress pages such as Home/Blog and all non-post items.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
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

DEFAULT_TARGET_DOMAIN = "https://zemelaar.blog"


@dataclass(frozen=True)
class WpPost:
    post_id: str
    title: str
    slug: str
    status: str
    post_type: str
    post_date: str
    post_date_gmt: str
    post_modified: str
    creator: str
    categories: list[str]
    tags: list[str]
    content_html: str


@dataclass(frozen=True)
class UrlMapRow:
    old_url: str
    new_url: str
    old_path: str
    new_path: str
    title: str
    post_type: str
    status: str
    post_date: str
    slug: str
    review_note: str


@dataclass(frozen=True)
class MediaRow:
    attachment_url: str
    parent_id: str

    @property
    def target_path(self) -> str:
        parsed = urlparse(self.attachment_url)
        marker = "/wp-content/uploads/"
        if marker not in parsed.path:
            return ""
        relative = parsed.path.split(marker, 1)[1].lstrip("/")
        return f"/uploads/{relative}"


class BasicHtmlToMarkdown(HTMLParser):
    """Small HTML-to-Markdown converter for WordPress post bodies.

    This intentionally handles only common WordPress body markup.
    Unknown tags are ignored, but their text content is preserved.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.link_stack: list[str] = []
        self.list_depth = 0
        self.in_pre = False
        self.in_code = False
        self.skip_depth = 0

    def get_markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def append(self, value: str) -> None:
        if self.skip_depth:
            return
        self.parts.append(value)

    def ensure_blank_line(self) -> None:
        if self.skip_depth:
            return
        current = "".join(self.parts)
        if not current:
            return
        if current.endswith("\n\n"):
            return
        if current.endswith("\n"):
            self.parts.append("\n")
        else:
            self.parts.append("\n\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()

        if tag in {"script", "style"}:
            self.skip_depth += 1
            return

        if self.skip_depth:
            return

        if tag in {"p", "div", "section", "article"}:
            self.ensure_blank_line()
        elif tag in {"br"}:
            self.append("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self.ensure_blank_line()
            self.append("#" * level + " ")
        elif tag == "blockquote":
            self.ensure_blank_line()
            self.append("> ")
        elif tag in {"strong", "b"}:
            self.append("**")
        elif tag in {"em", "i"}:
            self.append("*")
        elif tag == "code":
            if not self.in_pre:
                self.append("`")
            self.in_code = True
        elif tag == "pre":
            self.ensure_blank_line()
            self.append("```\n")
            self.in_pre = True
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            self.ensure_blank_line()
        elif tag == "li":
            indent = "  " * max(self.list_depth - 1, 0)
            self.append(f"{indent}* ")
        elif tag == "a":
            href = attrs_dict.get("href", "")
            self.link_stack.append(href)
            self.append("[")
        elif tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "") or attrs_dict.get("title", "")
            self.ensure_blank_line()
            self.append(f"![{escape_markdown(alt)}]({src})")
            self.ensure_blank_line()
        elif tag == "figure":
            self.ensure_blank_line()
        elif tag == "figcaption":
            self.ensure_blank_line()
            self.append("_")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in {"script", "style"}:
            self.skip_depth = max(self.skip_depth - 1, 0)
            return

        if self.skip_depth:
            return

        if tag in {"p", "div", "section", "article", "figure"}:
            self.ensure_blank_line()
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.ensure_blank_line()
        elif tag == "blockquote":
            self.ensure_blank_line()
        elif tag in {"strong", "b"}:
            self.append("**")
        elif tag in {"em", "i"}:
            self.append("*")
        elif tag == "code":
            if not self.in_pre:
                self.append("`")
            self.in_code = False
        elif tag == "pre":
            self.append("\n```")
            self.ensure_blank_line()
            self.in_pre = False
        elif tag in {"ul", "ol"}:
            self.list_depth = max(self.list_depth - 1, 0)
            self.ensure_blank_line()
        elif tag == "li":
            self.append("\n")
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            self.append(f"]({href})")
        elif tag == "figcaption":
            self.append("_")
            self.ensure_blank_line()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_pre:
            self.append(data)
            return
        collapsed = re.sub(r"\s+", " ", data)
        self.append(collapsed)


def escape_markdown(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]")


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def child_text(item: ET.Element, path: str) -> str:
    return text(item.find(path, NS))


def term_names(item: ET.Element, domain: str) -> list[str]:
    names: list[str] = []
    for category in item.findall("category"):
        if category.attrib.get("domain") == domain and category.text:
            names.append(category.text.strip())
    return names


def parse_posts(export_file: Path) -> list[WpPost]:
    tree = ET.parse(export_file)
    channel = tree.getroot().find("channel")
    if channel is None:
        raise ValueError("Could not find <channel> in WordPress export")

    posts: list[WpPost] = []
    for item in channel.findall("item"):
        posts.append(
            WpPost(
                post_id=child_text(item, "wp:post_id"),
                title=child_text(item, "title"),
                slug=child_text(item, "wp:post_name"),
                status=child_text(item, "wp:status"),
                post_type=child_text(item, "wp:post_type"),
                post_date=child_text(item, "wp:post_date"),
                post_date_gmt=child_text(item, "wp:post_date_gmt"),
                post_modified=child_text(item, "wp:post_modified"),
                creator=child_text(item, "dc:creator"),
                categories=term_names(item, "category"),
                tags=term_names(item, "post_tag"),
                content_html=child_text(item, "content:encoded"),
            )
        )
    return posts


def read_url_map(input_file: Path) -> dict[str, UrlMapRow]:
    rows: dict[str, UrlMapRow] = {}
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            slug = row.get("slug", "").strip()
            if not slug:
                continue
            rows[slug] = UrlMapRow(
                old_url=row.get("old_url", "").strip(),
                new_url=row.get("new_url", "").strip(),
                old_path=row.get("old_path", "").strip(),
                new_path=row.get("new_path", "").strip(),
                title=row.get("title", "").strip(),
                post_type=row.get("post_type", "").strip(),
                status=row.get("status", "").strip(),
                post_date=row.get("post_date", "").strip(),
                slug=slug,
                review_note=row.get("review_note", "").strip(),
            )
    return rows


def read_media_map(input_file: Path) -> dict[str, str]:
    media_map: dict[str, str] = {}
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            media = MediaRow(
                attachment_url=row.get("attachment_url", "").strip(),
                parent_id=row.get("parent_id", "").strip(),
            )
            if media.attachment_url and media.target_path:
                media_map[media.attachment_url] = media.target_path
    return media_map


def rewrite_media_urls(content: str, media_map: dict[str, str]) -> str:
    rewritten = content
    for old_url, new_path in sorted(media_map.items(), key=lambda item: len(item[0]), reverse=True):
        rewritten = rewritten.replace(old_url, new_path)
    return rewritten


def rewrite_internal_links(content: str, url_map: dict[str, UrlMapRow]) -> str:
    rewritten = content
    for row in sorted(url_map.values(), key=lambda item: len(item.old_url), reverse=True):
        if row.review_note.startswith("manual_review"):
            continue
        if row.old_url and row.new_path:
            rewritten = rewritten.replace(row.old_url, row.new_path)
        if row.old_path and row.new_path:
            rewritten = rewritten.replace(row.old_path, row.new_path)
    return rewritten


def html_to_markdown(content_html: str) -> str:
    parser = BasicHtmlToMarkdown()
    parser.feed(content_html)
    parser.close()
    return html.unescape(parser.get_markdown())


def frontmatter(post: WpPost, url_row: UrlMapRow, target_domain: str) -> str:
    canonical = url_row.new_url or f"{target_domain.rstrip('/')}/{post.slug}/"
    date = post.post_date.replace(" ", "T")

    lines = [
        "---",
        f"title: {yaml_quote(post.title)}",
        f"date: {date}",
        f"slug: {yaml_quote(post.slug)}",
        "draft: false",
        f"canonical: {yaml_quote(canonical)}",
        f"categories: [{', '.join(yaml_quote(value) for value in post.categories)}]",
        f"tags: [{', '.join(yaml_quote(value) for value in post.tags)}]",
        "---",
        "",
    ]
    return "\n".join(lines)


def write_post(post: WpPost, url_row: UrlMapRow, media_map: dict[str, str], url_map: dict[str, UrlMapRow], output_dir: Path, target_domain: str) -> None:
    rewritten_html = rewrite_media_urls(post.content_html, media_map)
    rewritten_html = rewrite_internal_links(rewritten_html, url_map)
    markdown = html_to_markdown(rewritten_html)

    output_file = output_dir / f"{post.slug}.md"
    output_file.write_text(frontmatter(post, url_row, target_domain) + markdown, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert WordPress posts to first-pass Hugo Markdown")
    parser.add_argument("--input", default="wordpress-data/export.xml", help="Path to WordPress WXR export XML")
    parser.add_argument("--url-map", default="migration/url-map.csv", help="Path to URL map CSV")
    parser.add_argument("--media-inventory", default="migration/media-inventory.csv", help="Path to media inventory CSV")
    parser.add_argument("--output-dir", default="site/content/posts", help="Output directory for Hugo Markdown posts")
    parser.add_argument("--target-domain", default=DEFAULT_TARGET_DOMAIN, help="Canonical target domain")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    export_file = Path(args.input)
    url_map_file = Path(args.url_map)
    media_inventory_file = Path(args.media_inventory)
    output_dir = Path(args.output_dir)

    for required_file in [export_file, url_map_file, media_inventory_file]:
        if not required_file.exists():
            print(f"Error: required file not found: {required_file}", file=sys.stderr)
            return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    posts = parse_posts(export_file)
    url_map = read_url_map(url_map_file)
    media_map = read_media_map(media_inventory_file)

    converted = 0
    skipped_pages = 0
    skipped_other = 0
    skipped_unpublished = 0
    skipped_missing_url_map = 0

    for post in posts:
        if post.post_type == "page":
            skipped_pages += 1
            continue
        if post.post_type != "post":
            skipped_other += 1
            continue
        if post.status != "publish":
            skipped_unpublished += 1
            continue
        if post.slug not in url_map:
            skipped_missing_url_map += 1
            continue

        write_post(post, url_map[post.slug], media_map, url_map, output_dir, args.target_domain)
        converted += 1

    print("Hugo conversion complete")
    print()
    print(f"Converted posts: {converted}")
    print(f"Skipped pages: {skipped_pages}")
    print(f"Skipped other items: {skipped_other}")
    print(f"Skipped unpublished posts: {skipped_unpublished}")
    print(f"Skipped posts missing URL map: {skipped_missing_url_map}")
    print(f"Wrote posts to: {output_dir}")

    return 0 if skipped_missing_url_map == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
