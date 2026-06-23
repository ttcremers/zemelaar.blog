# Agent Instructions

This repository contains the migration foundation for Zemelaar.blog.

Agents must work slowly and inspectably.

## Hard rules

- Do not modify anything in `wordpress-data/`.
- Do not commit WordPress XML exports, media archives, or generated media.
- Do not change DNS, Cloudflare settings, domain settings, or deployment settings.
- Do not rewrite, improve, summarize, or normalize prose unless explicitly asked.
- Do not rename titles or slugs unless explicitly asked.
- Do not delete posts or merge content unless explicitly asked.
- Do not choose a final design before the content migration is inspectable.
- Prefer small Python scripts over large frameworks.
- Prefer CSV/Markdown reports for intermediate migration output.
- Explain assumptions in generated notes or comments.

## Migration order

1. Inventory
2. URL mapping
3. Media inventory
4. Hugo conversion
5. Local preview
6. Cloudflare Pages preview
7. DNS switch
8. Domain/registrar migration

## Current milestone

The current milestone is a trustworthy migration inventory, not a finished website.

Expected generated files:

```text
migration/posts-inventory.csv
migration/media-inventory.csv
migration/url-map.csv
```

Source URLs from WordPress.com belong in migration mapping files, not in final Hugo frontmatter, unless temporarily needed for debugging and explicitly reviewed.
