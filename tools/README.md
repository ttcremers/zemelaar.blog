# Tools

Small migration tools live here.

These scripts should be boring, inspectable, and safe.

## Rules

- Read from `wordpress-data/`.
- Write generated output to `migration/`.
- Never modify source exports.
- Prefer standard-library Python where practical.
- Make scripts idempotent where possible.
- Print clear counts and warnings.

## Planned scripts

```text
inspect-wp-export.py   # create inventory CSVs from WordPress WXR XML
build-url-map.py       # derive canonical Zemelaar URLs and legacy redirects
convert-to-hugo.py     # convert reviewed inventory/content to Hugo Markdown
```

The first real script should be `inspect-wp-export.py`.
