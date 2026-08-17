# AllMedTests Project Context

## Project Summary

This repository is the replacement site for `allmedtests.com`.

The old site was a WordPress-based medical/lab-test content site. The current project is an Astro-based static site that is being rebuilt in stages:

- Preserve SEO-critical URLs from the old domain.
- Restore legacy educational article content from Wayback Machine snapshots.
- Keep original article slugs unchanged.
- Preserve legacy WordPress image paths under `/wp-content/uploads/...` where images were recovered.
- Prepare the site to later become a multilingual lab-test marketplace with provider/test collections.

The current deployment target is Cloudflare Pages.

## Current Technical Stack

- Astro 5
- TypeScript strict
- Static output
- Content collections in `src/content/config.ts`
- Deployment: Cloudflare Pages
- Build command: `npm run build`
- Output directory: `dist/`

Do not add `@astrojs/cloudflare` unless the project explicitly needs SSR later.

## Important Routing Rules

The homepage must stay at `/`.

This is critical because the root URL has the strongest backlink profile:

- `https://allmedtests.com/`
- 193 referring domains
- 53 dofollow referring domains

Do not move, redirect, rename, or replace the homepage route with another path.

English URLs must remain unprefixed:

- Correct: `/abo-and-rh-blood-grouping/`
- Incorrect: `/en/abo-and-rh-blood-grouping/`

This is controlled by Astro i18n:

```js
i18n: {
  defaultLocale: 'en',
  locales: ['en'],
  routing: {
    prefixDefaultLocale: false
  }
}
```

## Content Collections

Articles live in:

```text
src/content/articles/en/
```

The article frontmatter schema is intentionally minimal. Do not introduce new required fields without explicit approval, because restored legacy articles must remain importable.

Expected article frontmatter fields:

```yaml
---
title: "..."
description: "..."
originalUrl: "/legacy-slug/"
originalPublishDate: "YYYY-MM-DD"
restoredDate: "2026-08-14"
sourceSnapshot: "http://web.archive.org/web/..."
referringDomains: 0
priorityTier: "P0"
draft: true
imageRestoreNeeded: true
---
```

Only `title` is required. Most other fields are optional by schema.

All restored articles must remain:

```yaml
draft: true
```

until the user explicitly approves publication after manual review.

## Article Restoration Rules

When restoring old content:

- Use `audit/urls_priority.csv` as the source of prioritized article URLs.
- Use `last_snapshot_url_for_fetch` when available.
- Cache raw snapshots in `audit/raw_snapshots/{slug}.html`.
- Do not rewrite, improve, or invent article text.
- Preserve the original slug exactly.
- Preserve headings, lists, and tables where possible.
- Remove navigation, sidebar, footer, comments, ads, related posts, and Wayback UI.
- If a fragment is unclear, add:

```html
<!-- TODO: fragment unclear in archived snapshot, needs manual review -->
```

and document it in:

```text
audit/content_review_needed.md
```

## Image Restoration Rules

Recovered images must be stored under their original WordPress paths:

```text
public/wp-content/uploads/{year}/{month}/{filename}
```

Markdown image links should point to local paths:

```md
![Alt text](/wp-content/uploads/2017/06/example.png)
```

Never leave article Markdown pointing to:

```text
allmedtests.com/wp-content/...
```

If an image cannot be found in Wayback:

- Remove the broken Markdown image from the article body.
- Add `imageRestoreNeeded: true` to the article frontmatter.
- Add a note to `audit/content_review_needed.md`.

The most important recovered image is:

```text
public/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png
```

It corresponds to the legacy URL:

```text
http://allmedtests.com/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png
```

This image had 9 referring domains and must remain available at the same path after deployment.

## Audit Files

Key audit files:

```text
audit/summary.md
audit/urls_full.csv
audit/urls_priority.csv
audit/backlinks.csv
audit/content_review_needed.md
audit/images_to_recover.csv
audit/remaining_articles_restore_report.csv
```

`audit/urls_priority.csv` is the source of article prioritization.

Current URL classification rules:

- `homepage`: root URL only
- `article`: real educational articles
- `legacy_product`: old product/marketplace-style URLs
- `taxonomy`: category/tag/archive URLs
- `other`: service/legal/test pages

Known service/demo pages must remain out of article restoration:

- `contact`
- `about`
- `privacy-policy`
- `privacy`
- `terms`
- `disclaimer`
- `facebook-demo`
- `my-instagram-feed-demo`

Do not classify all slugs containing `demo` as service pages, because real articles such as `demonstrate-*` are valid educational content.

## Homepage

The homepage is:

```text
src/pages/index.astro
```

It should:

- Stay at `/`.
- Show the `allmedtests.com` brand.
- List restored lab-test guide articles from the `articles` collection.
- Show draft badges for articles with `draft: true`.
- Include a non-clickable "Find a Test Near You" / marketplace teaser while `tests` and `providers` collections are empty.
- Include a general affiliate disclosure in the footer.

Do not add links to categories, tests, or providers until those pages actually exist.

## Article Routes

Article rendering is handled by:

```text
src/pages/[...slug].astro
```

It should render articles using the original legacy slugs, typically derived from `originalUrl`.

Do not create duplicate article routes under `/en/`.

## Redirects

Cloudflare Pages uses:

```text
public/_redirects
```

Current file is intentionally only a placeholder.

Do not add real redirects until legacy product and taxonomy mapping is finalized.

Expected future redirect volume is around 260+ rules:

- 95 legacy product URLs
- 167 taxonomy URLs

This is below the normal Cloudflare Pages `_redirects` rule limit.

## Build And Validation

Before finishing meaningful changes, run:

```bash
npm run build
```

Expected warnings about empty `tests` and `providers` collections are okay while those collections have no content.

Useful validation checks:

```bash
find src/content/articles/en -name '*.md' | wc -l
```

```bash
python3 - <<'PY'
import re
from pathlib import Path
missing = []
external = []
for md in sorted(Path('src/content/articles/en').glob('*.md')):
    text = md.read_text()
    for m in re.finditer(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', text):
        src = m.group(1)
        if 'allmedtests.com/wp-content' in src:
            external.append((md.name, src))
        if src.startswith('/wp-content/uploads/') and not (Path('public') / src.lstrip('/')).exists():
            missing.append((md.name, src))
print('missing', missing)
print('external', external)
PY
```

There should be no broken local image paths and no external image references to the old domain.

## Git Hygiene

Do not commit generated local build/cache noise unless explicitly requested.

Avoid staging:

```text
.astro/
dist/
node_modules/
scripts/__pycache__/
```

Prefer explicit `git add` paths for relevant source, audit, script, and public asset files.

## Current Migration Status

Completed:

- URL audit and prioritization.
- Astro skeleton.
- Cloudflare Pages redirect placeholder.
- Wave 1/P0 article restoration.
- Wave 1 image restoration.
- P2/P3 article restoration batch.
- Homepage replacement.
- `iodine-test-starch` recovery from an earlier working Wayback snapshot.
- Reclassification of service/demo pages out of article priority.

Current expected article count:

```text
44 Markdown article files in src/content/articles/en/
```

Current expected audit counters:

```text
homepage: 1
article: 44
legacy_product: 95
taxonomy: 167
other: 26
```

Priority counts:

```text
P0: 9
P1: 0
P2: 25
P3: 10
```

Next likely phases:

- Manual article review.
- Recover or recreate missing images flagged by `imageRestoreNeeded`.
- Build real marketplace taxonomy.
- Map legacy product and taxonomy redirects.
- Add provider/test content.
- Later add more locales under prefixed routes such as `/es/...` and `/de/...`.
