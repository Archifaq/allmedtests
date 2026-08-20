# AllMedTests Claude Guide

This repository replaces the historical `allmedtests.com` WordPress site with an Astro static site.

For Claude Project setup, use these companion files:

- `CLAUDE_INSTRUCTIONS.md` as the project instructions.
- `CLAUDE_CONTEXT.md` as the project context / knowledge file.

The short version:

- Preserve SEO-critical legacy English URLs.
- Keep English articles unprefixed at `/slug/`.
- Keep restored, translated, and marketplace research records as `draft: true` until explicit approval.
- Do not add required frontmatter fields without explicit approval.
- Use `audit/translation_status.csv` to track translated article status and EN mapping.
- Use the current design system in `src/styles/tokens.css`, `src/layouts/BaseLayout.astro`, and `src/components/`.

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

English article URLs must remain unprefixed:

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
src/pages/[market]/cities/[...slug].astro
src/pages/[market]/tests/[...slug].astro
src/pages/[market]/providers/[...slug].astro
```

Marketplace routes are gated by `MARKETPLACE_ENABLED=true`. Without that env var, default builds must not generate market routes.

Avoid slug collisions with reserved market route segments:

- `categories`
- `cities`
- `tests`
- `providers`

Use URL helpers in `src/lib/routes.ts` instead of hand-written paths.

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
src/content/locations/
src/content/tests/
src/content/providers/
```

## Design System

Design tokens live in:

```text
src/styles/tokens.css
```

The active layout is:

```text
src/layouts/BaseLayout.astro
```

Reusable UI components:

```text
src/components/SiteHeader.astro
src/components/SiteFooter.astro
src/components/RangeMark.astro
src/components/DraftBadge.astro
src/components/EmptyStateCard.astro
src/components/MissingImagePlaceholder.astro
src/components/ReferenceRangeTable.astro
src/components/ArticleCard.astro
src/components/MarketplaceTeaser.astro
src/components/TranslationNote.astro
src/components/TableOfContents.astro
```

Rules:

- Reuse these components instead of duplicating markup.
- `DraftBadge` renders only for `draft: true`.
- `EmptyStateCard` is the shared empty marketplace state.
- `MarketplaceTeaser` stays low-key and non-clickable while verified tests/providers are unavailable.
- `ReferenceRangeTable` must use real optional `referenceRanges` data; do not invent ranges from mockups.

## Article And Slug Rules

English article slugs in `src/content/articles/en/` are legacy SEO URLs. Do not rename them unless the user explicitly asks for a migration and redirects.

All restored or translated articles must remain `draft: true` until explicit publication approval. Do not publish by changing `draft` to `false` unless explicitly asked.

Polish translated article slugs must be lowercase ASCII, use hyphens, and keep `translationOfSlug` pointing to the canonical English original slug.

## Marketplace UI

Current populated marketplace content:

- `pl`: draft categories, draft city pages, and draft provider research records.
- `ie`: draft categories, draft city pages, and draft provider research records.
- `us` and `uk`: draft categories and draft city pages only.
- `tests`: empty.

Provider records in `pl` and `ie` are unverified research placeholders only. They must remain `draft: true` and must not be treated as live marketplace listings until manual validation.

Do not create fake providers, prices, LOINC codes, addresses, collection points, availability values, or CTAs from design mockups or unverified sources.

When marketplace data is missing or unverified:

- Use `EmptyStateCard`.
- Do not render live links or CTAs that imply tests/providers are available.
- Keep homepage marketplace messaging low-key.

Current homepage city links are limited to the existing PL city preparation block when `MARKETPLACE_ENABLED=true`. Do not add extra homepage blocks for `us`, `uk`, or `ie` without explicit scope.

There is no standalone `/pl/cities/` listing route; do not add one without an explicit request.

## Redirects

Cloudflare Pages uses:

```text
public/_redirects
```

Do not add real redirects until legacy product and taxonomy mapping is finalized.

## Build And Validation

Before finishing meaningful code, routing, design, or content-routing changes, run:

```bash
npm run build
```

When validating translated article routes or marketplace routes, also run:

```bash
MARKETPLACE_ENABLED=true npm run build
```

Warnings about an empty `tests` collection are expected while tests have no content. Empty provider warnings should appear only in checkouts where provider records have not yet been populated.
