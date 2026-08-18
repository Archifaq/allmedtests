# AllMedTests Claude Guide

This repository replaces the historical `allmedtests.com` WordPress site with an Astro static site.

For Claude Project setup, use these companion files:

- `CLAUDE_INSTRUCTIONS.md` as the project instructions.
- `CLAUDE_CONTEXT.md` as the project context / knowledge file.

The short version:

- Preserve SEO-critical legacy English URLs.
- Keep English articles unprefixed at `/slug/`.
- Keep restored and translated articles as `draft: true` until manual approval.
- Do not add required frontmatter fields without explicit approval.
- Use `audit/translation_status.csv` to track translated article status and EN mapping.

## Project Basics

- Framework: Astro 5.
- Language: TypeScript strict.
- Output: static.
- Deployment target: Cloudflare Pages.
- Build command: `npm run build`.
- Output directory: `dist/`.

Do not add `@astrojs/cloudflare` unless the project explicitly needs SSR later.

## Routing Rules

The homepage must stay at `/`.

English URLs must remain unprefixed:

- Correct: `/abo-and-rh-blood-grouping/`
- Incorrect: `/en/abo-and-rh-blood-grouping/`

Localized translated article routes use:

```text
src/pages/[locale]/[...slug].astro
```

Do not create per-locale article route files such as `src/pages/pl/[...slug].astro`.

Marketplace routes use:

```text
src/pages/[market]/index.astro
src/pages/[market]/categories/[...slug].astro
src/pages/[market]/tests/[...slug].astro
src/pages/[market]/providers/[...slug].astro
```

Avoid slug collisions with reserved market route segments such as:

- `categories`
- `tests`
- `providers`

## Content Locations

English restored articles:

```text
src/content/articles/en/
```

Polish translated articles:

```text
src/content/articles/pl/
```

Marketplace content collections:

```text
src/content/categories/
src/content/tests/
src/content/providers/
```

## Article Frontmatter

The article schema is intentionally minimal. Only `title` is required.

Common optional fields:

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
translationOfSlug: "english-original-slug"
imageRestoreNeeded: true
draft: true
---
```

Rules:

- Do not add new required frontmatter fields without explicit approval.
- All restored or translated articles must remain `draft: true` until the user explicitly approves publication.
- Do not publish by changing `draft` to `false` unless explicitly asked.
- For translated articles, `translationOfSlug` must point to the canonical English original slug.

## Slug Rules

English article slugs in `src/content/articles/en/` are legacy SEO URLs. Do not rename them unless the user explicitly asks for a migration and redirects.

Polish article slugs must:

- Be lowercase ASCII only.
- Use only `a-z`, `0-9`, and hyphens.
- Transliterate Polish characters:
  - `ą -> a`
  - `ć -> c`
  - `ę -> e`
  - `ł -> l`
  - `ń -> n`
  - `ó -> o`
  - `ś -> s`
  - `ź -> z`
  - `ż -> z`
- Have no spaces, underscores, Cyrillic, doubled hyphens, or leading/trailing hyphens.
- Match the actual route slug resolved by `src/pages/[locale]/[...slug].astro`.
- Be unique within `src/content/articles/pl/`.

## Translation Audit

Translation status is tracked in:

```text
audit/translation_status.csv
```

Current columns:

```csv
slug,en_slug,locale,market,status,translator_source
```

Column meanings:

- `slug`: localized article slug for the row locale.
- `en_slug`: English original article slug.
- `locale`: content locale such as `pl` or `en`.
- `market`: market code such as `pl`.
- `status`: translation state, currently draft for machine translations.
- `translator_source`: translation provenance and review note.

Rules:

- Preserve row order unless the task explicitly asks to sort.
- For `pl` rows, `en_slug` must match the article frontmatter `translationOfSlug`.
- For `en` rows, `en_slug` should equal `slug`.
- If `translationOfSlug` is missing or unresolved, leave `en_slug` empty and add a note to `audit/content_review_needed.md`.

## Article Restoration Rules

When restoring old content:

- Use `audit/urls_priority.csv` as the source of prioritized article URLs.
- Use `last_snapshot_url_for_fetch` when available.
- Cache raw snapshots in `audit/raw_snapshots/{slug}.html`.
- Do not rewrite, improve, or invent article text.
- Preserve original English legacy slugs exactly.
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

Important recovered image:

```text
public/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png
```

It corresponds to:

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
audit/translation_status.csv
```

Current URL classification rules:

- `homepage`: root URL only.
- `article`: real educational articles.
- `legacy_product`: old product / marketplace-style URLs.
- `taxonomy`: category, tag, and archive URLs.
- `other`: service, legal, and demo pages.

Known service/demo pages must remain out of article restoration:

- `contact`
- `about`
- `privacy-policy`
- `privacy`
- `terms`
- `disclaimer`
- `facebook-demo`
- `my-instagram-feed-demo`

Do not classify every slug containing `demo` as a service page. Real articles such as `demonstrate-*` are valid educational content.

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
- Include a non-clickable marketplace teaser while `tests` and `providers` collections are empty.
- Include a general affiliate disclosure in the footer.

Do not add links to categories, tests, or providers until those pages actually exist.

## Redirects

Cloudflare Pages uses:

```text
public/_redirects
```

The current file is intentionally only a placeholder.

Do not add real redirects until legacy product and taxonomy mapping is finalized.

Expected future redirect volume is around 260+ rules:

- 95 legacy product URLs.
- 167 taxonomy URLs.

This is below the normal Cloudflare Pages `_redirects` rule limit.

## Build And Validation

Before finishing meaningful code or content-routing changes, run:

```bash
npm run build
```

Expected warnings about empty `tests` and `providers` collections are okay while those collections have no content.

Localized article routes in `src/pages/[locale]/[...slug].astro` currently generate only when:

```bash
MARKETPLACE_ENABLED=true npm run build
```

Use this extra validation when changing translated article slugs or marketplace routing.
