# Zemelaar.blog — Project Manifest

## Purpose

Zemelaar.blog is a small literary essay site.

It is not a news site, not a diary, not a portfolio, and not a generic WordPress blog.

The site should function as a quiet archive for Dutch-language essays, observations, memories, language pieces, and reflective prose by Thomas Cremers.

The goal of this migration is to move Zemelaar away from WordPress.com and rebuild it as a simple, durable, static website with full control over content, URLs, design, hosting, and SEO.

## Core principles

This project follows a small-tools-first approach.

Prefer simple, inspectable files over opaque systems.

Prefer Markdown, Git, static HTML, and clear build steps over databases, plugins, dashboards, and hidden platform behavior.

Do not automate too much too early.

The correct order is:

1. Inventory
2. Mapping
3. Conversion
4. Local preview
5. Hosted preview
6. DNS switch
7. Registrar/domain migration

No DNS or domain changes should happen before the new site has been built and tested on a preview URL.

## Source material

The original source material lives in:

```text
wordpress-data/
```

Expected contents:

```text
wordpress-data/
├── export.xml
└── media.tar
```

These files are archival source files.

They must not be edited, rewritten, moved, normalized, cleaned, or modified by migration scripts.

All generated migration output should go into:

```text
migration/
```

All generated Hugo site files should go into:

```text
site/
```

## Suggested project structure

```text
zemelaar.blog/
├── wordpress-data/
│   ├── export.xml
│   └── media.tar
│
├── migration/
│   ├── posts-inventory.csv
│   ├── media-inventory.csv
│   ├── media-rewrite-map.csv
│   ├── url-map.csv
│   ├── redirects.md
│   └── migration-notes.md
│
├── tools/
│   ├── inspect-wp-export.py
│   ├── build-url-map.py
│   └── convert-to-hugo.py
│
├── site/
│   └── Hugo site
│
└── README.md
```

## Migration strategy

Do not begin by creating a finished Hugo site.

First inspect the WordPress export and generate inventories.

The first migration scripts should produce:

```text
migration/posts-inventory.csv
migration/media-inventory.csv
migration/url-map.csv
```

Only after these files have been reviewed should conversion to Hugo Markdown begin.

## URL strategy

Zemelaar should use clean, date-free canonical URLs.

The content is not primarily a diary or news archive. Most posts should remain readable as essays, observations, or standalone pieces. Dates belong in article metadata, not in the public URL.

Canonical post URLs must use this structure:

```text
https://zemelaar.blog/<slug>/
```

Example:

```text
https://zemelaar.blog/zijn-ouwe-zemelaars-eigenwijs/
```

Old WordPress date-based URLs must be treated as legacy URLs and redirected where possible.

Example:

```text
/2025/06/28/zijn-ouwe-zemelaars-eigenwijs/
→
/zijn-ouwe-zemelaars-eigenwijs/
```

The site must be internally consistent:

* canonical URLs use `/slug/`
* sitemap contains only canonical URLs
* internal links point only to canonical URLs
* old date-based URLs exist only as redirects
* dates remain visible as metadata on the page

## Redirect strategy

The migration should generate a redirect map.

For Cloudflare Pages this will likely become a `_redirects` file.

Example:

```text
/2025/06/28/zijn-ouwe-zemelaars-eigenwijs/ /zijn-ouwe-zemelaars-eigenwijs/ 301
/2022/08/08/sap-van-gefermenteerde-druiven/ /sap-van-gefermenteerde-druiven/ 301
```

Redirects from the old `zemelaarblog.wordpress.com` subdomain may depend on what WordPress.com allows after migration. These should be documented separately.

Redirects for `zemelaar.blog` itself are mandatory.

## SEO strategy

The current indexing state is weak and confused. The migration should create a cleaner canonical foundation rather than preserve every WordPress.com behavior.

SEO priorities:

* one canonical domain: `https://zemelaar.blog`
* one canonical URL per article
* clean sitemap
* correct canonical tags
* correct Open Graph metadata
* no duplicate date and non-date versions indexed
* no tag/category spam unless intentionally designed
* no accidental indexing of preview or temporary domains

The migration should improve clarity, not chase short-term preservation of flawed indexing.

## Platform target

The target platform should match the setup used for artistiekportret.nl as closely as practical.

Target stack:

```text
Source control: GitHub
Hosting: Cloudflare Pages
DNS: Cloudflare
Static site generator: Hugo
Domain: zemelaar.blog
```

GitHub is the source of truth for code and content.

Cloudflare Pages builds and hosts the public site.

Cloudflare DNS manages the domain records.

The domain may initially remain registered at WordPress.com if needed, but the intended long-term direction is to move domain control away from WordPress.com.

Do not change DNS until the Cloudflare Pages preview is working and reviewed.

## Static site generator

Use Hugo.

Reasons:

* fast
* simple
* static
* Markdown-native
* easy to version in Git
* suitable for long-form writing
* already aligned with the user’s other site workflow
* no database
* no plugin dependency

Avoid unnecessary frontend complexity.

No React framework is needed for Zemelaar.

## Theme

Use Hugo Bear Blog as the technical base.

Bear Blog is acceptable because it is small, text-first, fast, and not visually noisy.

However, the default theme should be adapted into a custom Zemelaar layer.

The site should not feel like:

* a tech blog
* a dashboard
* a startup blog
* a lifestyle blog
* a portfolio site
* an American “writerly” template
* a WordPress theme imitation

The site should feel like:

* a quiet literary archive
* a small European essay site
* sober
* personal
* readable
* slightly melancholic
* handmade through restraint, not decoration

## Typography direction

Zemelaar should feel European, literary, and restrained.

The typography should suggest literature through proportion, spacing, rhythm, and serif forms.

It should not announce itself with decorative effects.

Avoid:

* handwriting fonts
* script fonts
* typewriter nostalgia
* quirky American blog aesthetics
* garish display typography
* overly warm Pinterest-like beige styling
* decorative gimmicks that say “writer”
* excessive ornaments
* faux-vintage design

Preferred direction:

* classic European serif headings
* highly readable long-form body text
* quiet paragraph rhythm
* generous line height
* calm reading width
* subtle contrast between headings and body
* restrained italics
* strong support for Dutch text and diacritics

Initial font direction:

```text
Headings: EB Garamond
Body: Source Serif 4
```

Possible fallback:

```text
Headings: Georgia or system serif
Body: Georgia, Source Serif 4, or system serif
```

The literary atmosphere should come from understatement.

The suggestion is enough.

## Visual tone

The visual design should rely on:

* whitespace
* typography
* rhythm
* margins
* quiet color
* readable text
* calm navigation

The site should not rely on:

* animation
* novelty interactions
* loud color
* decorative icons
* complex cards
* large UI chrome
* stock-blog aesthetics

Color direction:

* warm off-white background
* near-black text, not pure black
* muted accent color
* restrained link styling
* no aggressive contrast unless needed for accessibility

## Content handling

Do not rewrite the original texts during migration.

Do not “improve” prose automatically.

Do not rename titles for SEO.

Do not normalize the author’s voice.

Conversion scripts may clean technical HTML artifacts, but literary content must remain intact unless explicitly reviewed by the user.

Allowed automatic changes:

* convert HTML to Markdown
* rewrite internal links
* rewrite media URLs
* add frontmatter
* preserve dates
* preserve slugs
* preserve categories/tags where useful
* remove WordPress-specific wrapper markup where safe

Not allowed without review:

* rewriting paragraphs
* changing titles
* changing meaning
* inventing summaries
* generating SEO descriptions from scratch
* renaming slugs
* merging posts
* deleting posts

## Content model

Each migrated post should become a Hugo Markdown file with frontmatter.

Suggested frontmatter:

```yaml
---
title: "Post title"
date: 2025-06-28T00:00:00+02:00
slug: "post-slug"
draft: false
canonical: "https://zemelaar.blog/post-slug/"
categories: []
tags: []
---
```

Dates should be preserved from WordPress.

The date may be shown on article pages, but should not dominate the design.

Old WordPress source URLs belong in migration mapping files, not in final Hugo frontmatter, unless temporarily needed for debugging and explicitly reviewed.

Final public Hugo frontmatter should not contain references to `zemelaarblog.wordpress.com`.

## Pages

WordPress pages should not be blindly converted.

Homepage, blog index, menu pages, and WordPress-generated structure should be reviewed manually.

The Hugo site should have a deliberately designed homepage.

Possible core pages:

```text
/
 /over/
 /archief/
```

Keep the navigation small.

## Media handling

Media from the WordPress export and media archive should be inventoried before conversion.

The migration should identify:

* original WordPress media URLs
* local media filenames
* attachment titles
* attachment parents
* files actually referenced by posts
* unused media

Referenced media should be copied into the Hugo site in a predictable structure.

Suggested direction:

```text
site/static/uploads/YYYY/MM/filename.ext
```

or, if using Hugo page bundles:

```text
site/content/posts/post-slug/images/filename.ext
```

Do not choose the final media strategy before inspecting actual usage.

### Media renaming policy

Media files may be renamed during Hugo export for readability, context, and long-term maintainability.

This is especially useful for files with opaque WordPress/import names, UUIDs, hashes, cropped variants, or phone-camera filenames.

Original exported media files must never be renamed, modified, deleted, or normalized.

Renaming means copying a source file into the Hugo site under a reviewed, cleaner destination name.

The migration must preserve a mapping from original WordPress attachment URLs to new local Hugo asset paths.

Use an explicit rewrite map before copying or renaming media:

```text
migration/media-rewrite-map.csv
```

Suggested columns:

```csv
old_attachment_url,old_local_path,new_site_path,post_slug,title,review_note
```

The rewrite map should be reviewed before use.

Do not automatically invent “creative” or SEO-heavy filenames.

Preferred naming style:

* plain lowercase filenames
* ASCII-safe where practical
* descriptive enough to understand later
* based on the post slug or visible context
* no keyword stuffing
* no decorative naming

Example:

```text
/uploads/2025/06/zijn-ouwe-zemelaars-eigenwijs-portret.png
```

The goal is practical clarity, not SEO theater.

## Development workflow

Use Git.

Use small commits.

Prefer clear, reversible steps.

Suggested branch flow:

```text
main
└── feat/wordpress-migration-foundation
```

Commit examples:

```text
docs: add migration manifest
tools: add WordPress export inspection script
migration: add initial URL mapping
site: initialize Hugo project
site: add Bear Blog theme base
```

## Agent / AI guardrails

AI assistants may help with scripts, conversion, review, and documentation.

They must not perform large uncontrolled rewrites.

Any AI or agent working on this project must follow these rules:

* do not modify files in `wordpress-data/`
* do not change DNS
* do not deploy without explicit instruction
* do not rewrite prose
* do not rename slugs unless asked
* do not invent missing content
* do not choose a final design before content conversion works
* do not optimize prematurely
* produce inspectable output files
* explain assumptions
* prefer small scripts over large frameworks

When asking an AI assistant for help, prefer narrow prompts.

Good first prompt:

```text
Create a Python script that inspects the WordPress WXR export and generates inventory CSV files. Do not convert the site yet.
```

Bad first prompt:

```text
Build me a complete Hugo replacement for my WordPress blog.
```

## First milestone

The first milestone is not a website.

The first milestone is a trustworthy migration inventory.

Definition of done:

* `posts-inventory.csv` exists
* `media-inventory.csv` exists
* `url-map.csv` exists
* all published posts are listed
* all old post URLs are captured
* all proposed canonical URLs are visible
* page handling is documented
* media risks are listed
* no source files were modified

Only after this milestone should the Hugo conversion begin.
