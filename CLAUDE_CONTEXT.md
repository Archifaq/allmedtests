# AllMedTests Project Context

## Current State

`allmedtests.com` is being rebuilt from an old WordPress medical / lab-test content site into an Astro static site with a restrained editorial design system.

The project currently has:

- 44 restored English educational articles in `src/content/articles/en/`.
- 9 Polish translated draft articles in `src/content/articles/pl/`.
- A design system implemented from provided HTML mockups.
- Marketplace collection scaffolding for categories, locations, tests, and providers.
- Polish category content in `src/content/categories/pl/`.
- Six Polish draft city pages in `src/content/locations/pl/`.
- Draft English-market category and city scaffolds for `us`, `uk`, and `ie`.
- An empty `tests` collection.
- Draft PL and IE provider research records in `src/content/providers/pl/` and `src/content/providers/ie/`, with source tracing in `audit/providers_research_log.csv` and `audit/providers_research_log_ie.csv`.
- Cloudflare Pages as the deployment target.

## Technical Stack

- Astro 5.
- TypeScript strict.
- Static output.
- Content collections in `src/content/config.ts`.
- Build command: `npm run build`.
- Output directory: `dist/`.

## Design System State

Design tokens live in:

```text
src/styles/tokens.css
```

The active layout is:

```text
src/layouts/BaseLayout.astro
```

`src/layouts/Base.astro` remains as a compatibility wrapper.

Reusable design components live in `src/components/`:

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

The signature visual motif is `RangeMark`, used in the logo, hero graphic, category pills, footer, translation notes, and related UI.

The UI has been wired to real content collections. Placeholder copy, provider names, prices, and numbers from the design mockups were not imported as data.

## Current Page Implementations

Homepage:

```text
src/pages/index.astro
```

Uses `BaseLayout`, `RangeMark`, `ArticleCard`, and `MarketplaceTeaser`. It displays real English articles from `articles/en`, Polish draft count from `articles/pl`, and no live marketplace CTAs while tests/providers are empty.

When `MARKETPLACE_ENABLED=true`, the homepage also renders a low-key "Polish city pages in preparation" block with links to the 6 PL city pages from `locations/pl`. Without that env var, the homepage has no city links.

English article route:

```text
src/pages/[...slug].astro
```

Keeps English articles at root `/slug/`. Uses `TableOfContents`, `DraftBadge`, `MissingImagePlaceholder`, `TranslationNote`, `ReferenceRangeTable`, and related `ArticleCard`s.

Translated article route:

```text
src/pages/[locale]/[...slug].astro
```

This is the single route for translated articles. Polish pages resolve to `/pl/{slug}/` when `MARKETPLACE_ENABLED=true`.

Marketplace routes:

```text
src/pages/[market]/index.astro
src/pages/[market]/categories/[...slug].astro
src/pages/[market]/cities/[...slug].astro
src/pages/[market]/tests/[...slug].astro
src/pages/[market]/providers/[...slug].astro
```

Category pages show real category data and related guides. City pages show real city content plus an `EmptyStateCard` for unverified labs and collection points. Tests/providers use empty-state UI until verified marketplace data exists.

Route helpers live in:

```text
src/lib/routes.ts
```

## Important URLs

The homepage `/` must remain the homepage because it has the strongest backlink profile:

- `https://allmedtests.com/`
- 193 referring domains.
- 53 dofollow referring domains.

English articles must remain at root paths such as:

```text
/abo-and-rh-blood-grouping/
/blood-glucose-test/
/serum-urea-test-kinetic-uv-method/
```

Do not create `/en/...` article URLs.

Polish article URLs are localized and prefixed with `/pl/`, for example:

```text
/pl/grupowanie-krwi-abo-i-rh/
/pl/badanie-glukozy-we-krwi-metoda-oksydazy-glukozowej/
```

Polish city URLs are marketplace-gated and prefixed with `/pl/cities/`, for example:

```text
/pl/cities/warszawa/
/pl/cities/krakow/
```

## Content Schema State

Article schema remains intentionally minimal. Only `title` is required.

`referenceRanges` is now optional for articles and tests so `ReferenceRangeTable` can render real structured range data when available. Existing content does not need this field.

Do not add fake reference ranges to restored articles or tests just to populate UI.

The `locations` collection is intentionally minimal:

- `market`
- `title`
- `region`
- `description`
- `draft`

All current PL city pages are `draft: true`.

## Current Polish Article Mapping

The current Polish translated articles are:

| pl slug | en_slug |
|---|---|
| `spektrofotometr-zasada-dzialania-uzycie-i-zastosowania` | `spectrophotometer-working-principle-use-applications` |
| `proba-benedicta-i-analiza-cukrow-redukujacych` | `benedicts-test-reducing-sugar` |
| `badanie-glukozy-we-krwi-metoda-oksydazy-glukozowej` | `blood-glucose-test` |
| `badanie-kinazy-kreatynowej-metoda-kinetyczna-ifcc-zasada-procedura-wyniki` | `creatine-kinase-test` |
| `badanie-mocznika-w-surowicy-metoda-kinetyczna-uv` | `serum-urea-test-kinetic-uv-method` |
| `grupowanie-krwi-abo-i-rh` | `abo-and-rh-blood-grouping` |
| `rozdzial-aminokwasow-metoda-chromatografii-bibulowej` | `separation-amino-acids-paper-chromatography` |
| `badanie-kliniczne-ukladu-czuciowego` | `clinical-examination-sensory-system` |
| `fotoelektryczny-kolorymetr-zasada-dzialania-uzycie-i-zastosowania` | `photoelectric-colorimeter` |

Each Polish article has `translationOfSlug` in frontmatter pointing to the corresponding English original.

All Polish translated articles are machine translations pending native review and must remain `draft: true`.

## Translation Status CSV

Translation status lives in:

```text
audit/translation_status.csv
```

Current columns:

```csv
slug,en_slug,locale,market,status,translator_source
```

The `slug` column tracks the localized content slug. The `en_slug` column links each translation row to its English source article.

## Important Audit Files

- `audit/urls_priority.csv`: prioritized article restoration queue.
- `audit/urls_full.csv`: full kept URL audit.
- `audit/backlinks.csv`: backlink source data.
- `audit/content_review_needed.md`: unresolved content, image, and mapping issues.
- `audit/images_to_recover.csv`: image recovery queue.
- `audit/remaining_articles_restore_report.csv`: restoration progress report.
- `audit/translation_status.csv`: translation tracking and EN mapping.
- `audit/category_sources_review.md`: source notes for English market category copy.
- `audit/providers_research_log.csv`: PL provider research source log.
- `audit/providers_research_log_ie.csv`: IE provider research source log.
- `audit/us_uk_ie_cities_source.md`: source notes for US/UK/IE draft city selection.

## Known Review Items

`audit/content_review_needed.md` includes missing image notes and content review items.

Existing examples include:

- Missing Benedict's test result image.
- Missing clinical sensory system image.
- Missing images for several restored English articles.
- Marketplace test data still requires real sourcing before populating tests.
- PL and IE provider research records still require manual validation before any provider data is treated as live.

## Marketplace State

Market config lives in:

```text
src/data/markets.ts
```

`src/data/markets.ts` defines the full list of planned market codes:

- `us`
- `uk`
- `ie`
- `de`
- `at`
- `ch`
- `fr`
- `be`
- `pl`
- `es`
- `ro`
- `hu`
- `cz`
- `it`
- `nl`
- `tr`
- `se`
- `no`
- `dk`
- `fi`

Defining a market code here does not mean it has real content. It makes the code valid for the `market` schema field and enables its marketplace route to build when `MARKETPLACE_ENABLED=true`.

`pl` is the first localized market with translated articles, city pages, category content, and draft provider research records. `us`, `uk`, and `ie` are English-language commercial-market scaffolds: they currently have `draft: true` category records and `draft: true` city pages. `ie` also has `draft: true` provider research placeholders; `us` and `uk` have no provider records yet. None of these markets has test records.

All other market codes in `markets.ts` have no content collections populated yet. Their presence in `markets.ts` is scaffolding for future markets, not implicit approval to add content.

When `MARKETPLACE_ENABLED=true`, `src/pages/[market]/index.astro` generates an index page for every market code in `markets.ts` via `getStaticPaths`, regardless of whether that market has real content. Empty markets render `EmptyStateCard` for categories, cities, and tests/providers. This is expected, not a bug.

Adding real content such as categories, cities, tests, or providers for a market code that does not already have it — or adding a new market code to `markets.ts` — still requires the user to explicitly scope that work, the same as any other marketplace expansion.

Polish categories currently exist under:

```text
src/content/categories/pl/
```

Polish city pages currently exist under:

```text
src/content/locations/pl/
```

Draft English-market city pages currently exist under:

```text
src/content/locations/us/
src/content/locations/uk/
src/content/locations/ie/
```

Current PL city slugs:

- `warszawa`
- `krakow`
- `wroclaw`
- `poznan`
- `gdansk`
- `lodz`

Tests are still empty. PL and IE provider records exist as `draft: true` research placeholders only, with source tracing kept in `audit/providers_research_log.csv` and `audit/providers_research_log_ie.csv`; they are not verified live marketplace listings.

Marketplace UI currently uses empty states and disabled/non-live messaging for missing provider, price, and test data.

City pages must not contain fake lab names, addresses, prices, collection points, or provider availability. They use `EmptyStateCard` until verified partner/location data exists.

City links currently appear in two places, both marketplace-gated:

- `/pl/`, the PL market index, has the Cities section.
- `/`, the root homepage, has the low-key city preparation block.

There is no standalone `/pl/cities/` listing route.

## Build Notes

Standard build:

```bash
npm run build
```

Expected warnings:

- Empty `tests` collection.
- Empty `providers` collection only in checkouts where provider records have not yet been populated.

Localized article routes and market pages currently generate only when marketplace mode is enabled:

```bash
MARKETPLACE_ENABLED=true npm run build
```

Use this extra build when checking `/pl/{slug}/`, `/pl/`, `/pl/cities/{slug}/`, `/us/cities/{slug}/`, `/uk/cities/{slug}/`, `/ie/cities/{slug}/`, or market pages.

If production Cloudflare Pages builds without `MARKETPLACE_ENABLED=true`, `/pl/`, `/pl/cities/...`, and homepage city links will not be present by design.
