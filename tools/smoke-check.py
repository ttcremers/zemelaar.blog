#!/usr/bin/env python3
"""Run a small sanity check for the Zemelaar Hugo migration."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site" / "content" / "blog"
STATIC_DIR = ROOT / "site" / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
REDIRECTS_FILE = STATIC_DIR / "_redirects"
HUGO_CONFIG = ROOT / "site" / "hugo.toml"


def ok(message: str) -> None:
    print(f"OK   {message}")


def fail(message: str) -> None:
    print(f"FAIL {message}")


def warn(message: str) -> None:
    print(f"WARN {message}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_links(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)


def main() -> int:
    failures = 0
    warnings = 0

    if CONTENT_DIR.exists():
        ok(f"content directory exists: {CONTENT_DIR.relative_to(ROOT)}")
    else:
        fail(f"content directory missing: {CONTENT_DIR.relative_to(ROOT)}")
        return 1

    posts = sorted(CONTENT_DIR.glob("*.md"))
    if len(posts) >= 18:
        ok(f"blog post count: {len(posts)}")
    else:
        fail(f"expected at least 18 blog posts, found {len(posts)}")
        failures += 1

    if UPLOADS_DIR.exists():
        images = [path for path in UPLOADS_DIR.rglob("*") if path.is_file()]
        ok(f"uploads directory exists with {len(images)} files")
    else:
        fail(f"uploads directory missing: {UPLOADS_DIR.relative_to(ROOT)}")
        failures += 1
        images = []

    if REDIRECTS_FILE.exists():
        redirects = [line for line in read_text(REDIRECTS_FILE).splitlines() if line and not line.startswith("#")]
        if len(redirects) >= 18:
            ok(f"Cloudflare redirects present: {len(redirects)}")
        else:
            fail(f"expected at least 18 redirects, found {len(redirects)}")
            failures += 1
    else:
        fail(f"Cloudflare redirects file missing: {REDIRECTS_FILE.relative_to(ROOT)}")
        failures += 1

    if HUGO_CONFIG.exists():
        config = read_text(HUGO_CONFIG)
        if "blog = '/:slug/'" in config or 'blog = "/:slug/"' in config:
            ok("blog section publishes at root URLs")
        else:
            fail("blog permalink is not configured as root /:slug/")
            failures += 1
    else:
        fail("site/hugo.toml is missing")
        failures += 1

    wordpress_refs = []
    blog_canonicals = []
    posts_without_images = []
    broken_image_refs = []

    for post in posts:
        content = read_text(post)
        if "zemelaarblog.wordpress.com" in content:
            wordpress_refs.append(post)
        if "canonical: \"https://zemelaar.blog/blog/" in content or "canonical: 'https://zemelaar.blog/blog/" in content:
            blog_canonicals.append(post)

        links = markdown_links(content)
        if not links:
            posts_without_images.append(post)

        for link in links:
            if not link.startswith("/uploads/"):
                continue
            target = STATIC_DIR / link.lstrip("/")
            if not target.exists():
                broken_image_refs.append((post, link))

    if wordpress_refs:
        fail(f"WordPress.com references remain in {len(wordpress_refs)} posts")
        failures += 1
    else:
        ok("no WordPress.com references in blog content")

    if blog_canonicals:
        fail(f"/blog/ canonical URLs found in {len(blog_canonicals)} posts")
        failures += 1
    else:
        ok("no /blog/ canonical URLs found")

    if posts_without_images:
        warn(f"posts without Markdown images: {len(posts_without_images)}")
        warnings += 1
    else:
        ok("all posts contain at least one Markdown image")

    if broken_image_refs:
        fail(f"broken local image references: {len(broken_image_refs)}")
        for post, link in broken_image_refs[:10]:
            print(f"     {post.relative_to(ROOT)} -> {link}")
        failures += 1
    else:
        ok("all local /uploads/ image references exist")

    print()
    print(f"Smoke check complete: {failures} failure(s), {warnings} warning(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
