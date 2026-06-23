# Migration Output

Generated migration reports live here.

This directory is for inspectable intermediate files, not final website content.

## Expected files

```text
posts-inventory.csv   # all posts/pages from the WordPress export
media-inventory.csv   # all attachment/media records from the WordPress export
url-map.csv           # old WordPress URLs mapped to new canonical URLs
redirects.md          # human-readable redirect notes
migration-notes.md    # assumptions, risks, and manual decisions
```

CSV files are ignored by Git by default because they are generated output.

Small Markdown notes may be committed when they document reviewed migration decisions.

## URL decision

Canonical Zemelaar post URLs are date-free:

```text
https://zemelaar.blog/<slug>/
```

Old date-based WordPress URLs should be treated as legacy redirects where possible.
