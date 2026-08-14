# allmedtests.com URL audit

Run:

```bash
python3 scripts/audit_urls.py --refresh
```

Use `--refresh` to force a new Wayback Machine CDX fetch. Without it, the script uses `audit/cache/cdx_raw.json` when the cache is less than 24 hours old.

Ahrefs files:

- Put the Ahrefs "Best by Links" export at `audit/backlinks.csv`, or pass another path with `--backlinks path/to/file.csv`. Expected columns: `Target URL` and `Referring domains`, or close equivalents.
- Put the Ahrefs "Organic Search -> Top Pages" export at `audit/ahrefs_traffic.csv`, or pass another path with `--traffic path/to/file.csv`. Expected columns: `URL` or `Page`, plus `Traffic`, or close equivalents.

Outputs:

- `audit/urls_full.csv`: all kept URLs with metadata and priority.
- `audit/urls_priority.csv`: article URLs only, sorted by migration priority.
- `audit/legacy_products_review.csv`: legacy shop/product URLs for manual redirect/drop decisions.
- `audit/taxonomy_review.csv`: WordPress tag/category URLs for redirect mapping.
- `audit/summary.md`: compact migration-priority summary.
