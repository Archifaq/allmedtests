# AllMedTests Claude Project Instructions

You are working in the `allmedtests.com` Astro repository.

## Core Priorities

1. Preserve SEO-critical legacy URLs.
2. Keep English article URLs unprefixed at `/slug/`.
3. Keep restored and translated articles as `draft: true` until explicit publication approval.
4. Keep the content schema minimal; do not add required frontmatter fields without approval.
5. Use existing Astro routes, layouts, components, and content collection patterns.
6. Keep UI connected to real content collections; do not copy placeholder data from mockups into production pages.

## Do Not Change Without Explicit Approval

- The homepage route `/`.
- English article slugs in `src/content/articles/en/`.
- `draft: true` on restored or translated articles.
- Astro i18n config in `astro.config.*`, unless reporting a clear issue separately.
- Cloudflare redirects in `public/_redirects`, unless redirect mapping has been approved.
- Required frontmatter fields in `src/content/config.ts`.
- The single translated article route `src/pages/[locale]/[...slug].astro`.

## Routing Instructions

English article route:

```text
src/pages/[...slug].astro
```

Translated article route:

```text
src/pages/[locale]/[...slug].astro
```

Do not create `/en/...` article URLs and do not create per-locale article route files such as `src/pages/pl/[...slug].astro`.

Marketplace routes:

```text
src/pages/[market]/index.astro
src/pages/[market]/categories/[...slug].astro
src/pages/[market]/cities/[...slug].astro
src/pages/[market]/tests/[...slug].astro
src/pages/[market]/providers/[...slug].astro
```

When changing translated slugs, check for collisions with reserved market route segments such as `categories`, `cities`, `tests`, and `providers`.

Use `src/lib/routes.ts` helpers for article, category, city, test, provider, and market URLs instead of hand-rolling path strings.

## Design System Instructions

Design tokens live in:

```text
src/styles/tokens.css
```

Use only the established token palette and font variables unless the user explicitly asks for a design expansion:

- `--paper`
- `--surface`
- `--ink`
- `--ink-soft`
- `--line`
- `--teal`
- `--teal-tint`
- `--amber`
- `--amber-tint`
- `--red`
- `--font-display`
- `--font-body`
- `--font-mono`

The base layout is:

```text
src/layouts/BaseLayout.astro
```

`src/layouts/Base.astro` is a compatibility wrapper around `BaseLayout.astro`.

Use these existing components rather than duplicating markup:

- `SiteHeader.astro`
- `SiteFooter.astro`
- `RangeMark.astro`
- `DraftBadge.astro`
- `EmptyStateCard.astro`
- `MissingImagePlaceholder.astro`
- `ReferenceRangeTable.astro`
- `ArticleCard.astro`
- `MarketplaceTeaser.astro`
- `TranslationNote.astro`
- `TableOfContents.astro`

Component behavior rules:

- `DraftBadge` renders only for `draft: true`.
- `MissingImagePlaceholder` is shown when `imageRestoreNeeded: true`.
- `TranslationNote` renders only when a translation/original URL resolves.
- `TableOfContents` uses rendered article headings, not hardcoded headings.
- `ReferenceRangeTable` must use real `referenceRanges` data when present; do not invent ranges from mockups.
- `MarketplaceTeaser` stays low-key and non-clickable while tests/providers are empty.
- `EmptyStateCard` is the shared UI for unavailable marketplace data.

## Article Content Instructions

English restored articles live in:

```text
src/content/articles/en/
```

Polish translated articles live in:

```text
src/content/articles/pl/
```

Marketplace content lives in:

```text
src/content/categories/{market}/
src/content/locations/{market}/
src/content/tests/{market}/
src/content/providers/{market}/
```

For translated articles:

- Use localized article slugs for filenames.
- Keep slugs lowercase ASCII with hyphens only.
- Transliterate Polish diacritics into ASCII.
- Keep `translationOfSlug` pointing to the English original slug.
- Verify the English original exists in `src/content/articles/en/`.

Polish transliteration:

- `ą -> a`
- `ć -> c`
- `ę -> e`
- `ł -> l`
- `ń -> n`
- `ó -> o`
- `ś -> s`
- `ź -> z`
- `ż -> z`

## Frontmatter Instructions

Only `title` is required for articles. Most other fields are optional by design.

Current optional article fields include:

- `description`
- `originalUrl`
- `originalPublishDate`
- `restoredDate`
- `sourceSnapshot`
- `referringDomains`
- `priorityTier`
- `translationOfSlug`
- `referenceRanges`
- `imageRestoreNeeded`
- `draft`

`referenceRanges` is optional for articles and tests. If present, it should be an array of:

```yaml
referenceRanges:
  - label: "Adults"
    min: 25
    max: 60
    unit: "mmol/L"
    valuePosition: 40
```

Do not add fake `referenceRanges` just to make the UI look populated.

## Translation Audit Instructions

Translation status is tracked in:

```text
audit/translation_status.csv
```

Current CSV columns:

```csv
slug,en_slug,locale,market,status,translator_source
```

Rules:

- Preserve the existing row order unless explicitly asked to sort.
- Do not change existing values except the columns requested by the task.
- For `pl` rows, `en_slug` must match the corresponding article frontmatter `translationOfSlug`.
- For `en` rows, `en_slug` should equal `slug`.
- If a translated article cannot be mapped to an English original, leave `en_slug` empty and add a note to `audit/content_review_needed.md`:

```text
translationOfSlug missing or unresolved, needs manual mapping to EN original
```

## Restoration Instructions

When restoring legacy article content:

- Use `audit/urls_priority.csv`.
- Fetch from `last_snapshot_url_for_fetch` when available.
- Cache raw snapshots under `audit/raw_snapshots/{slug}.html`.
- Preserve the original English slug exactly.
- Do not rewrite, modernize, summarize, or invent article text.
- Preserve headings, lists, and tables where possible.
- Remove navigation, sidebar, footer, comments, ads, related posts, and Wayback UI.
- Mark unclear fragments with:

```html
<!-- TODO: fragment unclear in archived snapshot, needs manual review -->
```

- Also document unclear fragments in `audit/content_review_needed.md`.

## Image Instructions

Recovered images must keep their original WordPress paths:

```text
public/wp-content/uploads/{year}/{month}/{filename}
```

Markdown should reference local paths:

```md
![Alt text](/wp-content/uploads/2017/06/example.png)
```

Do not leave Markdown pointing to `allmedtests.com/wp-content/...`.

If an image is missing:

- Remove the broken Markdown image from the article body.
- Add `imageRestoreNeeded: true`.
- Add a note to `audit/content_review_needed.md`.

## Marketplace Instructions

Categories, cities, tests, and providers belong to the feature-flagged marketplace layer.

The marketplace layer is gated by:

```bash
MARKETPLACE_ENABLED=true
```

Without this env var, default builds must not generate `/pl/`, `/pl/cities/...`, or city links on the homepage.

`src/data/markets.ts` currently defines more market codes than have real content. Only `pl` (translated articles, categories, cities, and draft provider research records), `ie` (draft categories, draft city pages, and draft provider research records), and `us`/`uk` (draft categories and draft city pages only) currently have populated marketplace content collections. The presence of a market code in `markets.ts` is not itself approval to add content for it. Treat adding content for any market code, new or already defined, the same as adding a new market: it needs the user to explicitly scope that work first.

`draft: true` on a content record means "not approved / pending review." It does not prevent the record's marketplace route from being generated when `MARKETPLACE_ENABLED=true`. Draft records still render, marked with `DraftBadge`; they are just not implied to be verified or live.

PL city pages currently use the `locations` collection and route:

```text
src/content/locations/pl/
src/pages/[market]/cities/[...slug].astro
```

Initial PL city slugs are:

- `warszawa`
- `krakow`
- `wroclaw`
- `poznan`
- `gdansk`
- `lodz`

Tests are intentionally empty until real test catalog data is available. Provider records may exist as `draft: true` research placeholders, but they are not verified live marketplace listings until manual approval and should not create CTAs, prices, availability, or address listings.

Do not create fake providers, lab names, addresses, prices, LOINC codes, collection points, or availability values from design mockups.

When tests/providers/city listings are empty:

- Use `EmptyStateCard`.
- Do not render real links or CTAs that imply the marketplace is live.
- Keep homepage marketplace messaging as a one-line `MarketplaceTeaser`.

Current PL city links are intentionally limited to:

- `/pl/`, the PL market index, which contains a Cities section when marketplace mode is enabled.
- `/`, which contains a low-key "Polish city pages in preparation" block when marketplace mode is enabled.

Do not create a standalone `/pl/cities/` listing route unless explicitly requested.

`us`, `uk`, and `ie` currently have explicitly scoped draft city pages. Do not add more cities, replicate city pages to other markets, or add real lab/provider/location data unless the user explicitly scopes that work.

## Validation

For meaningful code, routing, design, or content changes, run:

```bash
npm run build
```

Warnings about an empty `tests` collection are expected while tests have no content. Empty provider warnings may appear only in checkouts where providers have not yet been populated.

When validating translated article routes or marketplace routes, also run:

```bash
MARKETPLACE_ENABLED=true npm run build
```

This is needed because localized article routes and market pages currently generate only when marketplace mode is enabled.
