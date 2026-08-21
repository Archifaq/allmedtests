# AllMedTests Project Context

## Current State

`allmedtests.com` is being rebuilt from an old WordPress medical / lab-test content site into an Astro static site with a restrained editorial design system.

The project currently has:

- 44 restored English educational articles in `src/content/articles/en/`.
- 9 Polish translated draft articles in `src/content/articles/pl/`.
- A design system implemented from provided HTML mockups.
- Marketplace collection scaffolding for categories, locations, tests, and providers.
- Draft category content for `pl`, `us`, `uk`, and `ie`.
- Draft city pages for `pl`, `us`, `uk`, and `ie`.
- Draft provider research records for `pl`, `ie`, `uk`, and `us`.
- An empty `tests` collection.
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

Reusable components live in `src/components/`:

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

The UI is wired to real content collections. Placeholder provider names, prices, availability values, and mockup numbers must not be imported as data.

## Page Implementations

Homepage:

```text
src/pages/index.astro
```

The homepage stays at `/`, displays real English articles from `articles/en`, shows Polish draft article count, and keeps marketplace messaging low-key. When `MARKETPLACE_ENABLED=true`, it also renders the existing low-key PL city preparation block with links to the 6 PL city pages. It does not currently add homepage city blocks for `us`, `uk`, or `ie`.

English article route:

```text
src/pages/[...slug].astro
```

Keeps English articles at root `/slug/`.

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

Category pages show category data and related guides. City pages show city content plus `EmptyStateCard` for unverified labs and collection points. Provider pages render draft research placeholders but do not contain verified prices, addresses, test availability, or CTAs. Tests are empty.

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

Polish translated article URLs are localized and prefixed with `/pl/`.

Marketplace city URLs are feature-gated and use:

```text
/{market}/cities/{slug}/
```

Examples:

```text
/pl/cities/warszawa/
/us/cities/new-york/
/uk/cities/london/
/ie/cities/dublin/
```

## Content Schema State

Article schema remains intentionally minimal. Only `title` is required.

The `locations` collection is intentionally minimal:

- `market`
- `title`
- `region`
- `description`
- `draft`

The `providers` collection is intentionally minimal:

- `market`
- `name`
- `affiliateNetwork` optional
- `affiliateUrl` optional
- `countriesAvailable` optional
- `draft`

Do not add new required fields to `src/content/config.ts` without explicit approval.

## Market Config

Market config lives in:

```text
src/data/markets.ts
```

It currently defines 20 planned market codes:

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

Defining a market code does not mean it has real content. It makes the code valid for `market` fields and lets marketplace routes build when `MARKETPLACE_ENABLED=true`.

When `MARKETPLACE_ENABLED=true`, `src/pages/[market]/index.astro` generates an index page for every market code in `markets.ts`, even when that market has no content. Empty markets render `EmptyStateCard`; this is expected.

Adding content for a market that does not already have it, or adding a new market code, still requires explicit user scope.

## Current Marketplace Content

Categories:

- `pl`: 8 draft category files.
- `us`: 7 draft category files.
- `uk`: 7 draft category files.
- `ie`: 7 draft category files.
- All other markets: no category files.

Locations:

- `pl`: 6 draft city pages: `warszawa`, `krakow`, `wroclaw`, `poznan`, `gdansk`, `lodz`.
- `us`: 6 draft city pages: `new-york`, `los-angeles`, `chicago`, `houston`, `phoenix`, `miami`.
- `uk`: 6 draft city pages: `london`, `manchester`, `birmingham`, `leeds`, `glasgow`, `bristol`.
- `ie`: 5 draft city pages: `dublin`, `cork`, `galway`, `limerick`, `waterford`.
- All other markets: no location files.

Providers:

- `pl`: 3 draft provider research records: `diagnostyka`, `alab-laboratoria`, `synevo`.
- `ie`: 27 draft provider research records.
- IE provider count by city: Dublin 9, Cork 7, Galway 3, Limerick 5, Waterford 3.
- `uk`: 24 draft provider research records.
- UK provider count by research city: London 4, Manchester 4, Birmingham 4, Leeds 4, Glasgow 4, Bristol 4.
- `us`: 24 draft provider research records.
- US provider count by research city: New York 4, Los Angeles 4, Chicago 4, Houston 4, Phoenix 4, Miami 4.
- All other markets: no provider records.

Tests:

- Empty for every market.

Provider research records are not verified live marketplace listings. They must remain `draft: true` and require manual validation before any future step treats them as real provider, address, price, or availability data.

Source tracing:

- PL provider research source log: `audit/providers_research_log.csv` with 18 data rows.
- IE provider research source log: `audit/providers_research_log_ie.csv` with 27 data rows.
- UK provider research source log: `audit/providers_research_log_uk.csv` with 24 data rows.
- US provider research source log: `audit/providers_research_log_us.csv` with 24 data rows.
- IE Waterford `UPMC Whitfield Hospital` is low-confidence because it is based on an aggregator source and needs direct-source confirmation.
- UK provider candidates are draft/unverified placeholders with `confidence` values in the audit CSV; several low-confidence aggregator or partner-site rows require direct-source confirmation before any live use.
- US provider candidates are draft/unverified placeholders sourced from official provider or health-system pages; they still require manual validation before any live use.

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

All Polish translated articles are machine translations pending review and must remain `draft: true`.

## Audit Files

Important audit files:

- `audit/urls_priority.csv`: prioritized article restoration queue.
- `audit/urls_full.csv`: full kept URL audit.
- `audit/backlinks.csv`: backlink source data.
- `audit/content_review_needed.md`: unresolved content, image, and manual review issues.
- `audit/images_to_recover.csv`: image recovery queue.
- `audit/remaining_articles_restore_report.csv`: restoration progress report.
- `audit/translation_status.csv`: translation tracking and EN mapping.
- `audit/category_sources_review.md`: source notes for English market category copy.
- `audit/providers_research_log.csv`: PL provider research source log.
- `audit/providers_research_log_ie.csv`: IE provider research source log.
- `audit/providers_research_log_uk.csv`: UK provider research source log.
- `audit/providers_research_log_us.csv`: US provider research source log.
- `audit/us_uk_ie_cities_source.md`: source notes for US/UK/IE draft city selection.

## Restoration Audit Details

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

Important recovered image:

```text
public/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png
```

It corresponds to:

```text
http://allmedtests.com/wp-content/uploads/2017/06/ABO-and-RH-Blood-Grouping.png
```

This image had 9 referring domains and must remain available at the same path after deployment.

Known review items include missing restored article images, marketplace test data sourcing, PL/IE/UK/US provider manual validation, low-confidence UK provider candidates, and the low-confidence IE Waterford aggregator-sourced provider candidate.

## Build Notes

Standard build:

```bash
npm run build
```

Marketplace build:

```bash
MARKETPLACE_ENABLED=true npm run build
```

Use the marketplace build when checking translated article routes or any market route, including categories, cities, providers, and tests.

Expected warning while tests are empty:

- Empty `tests` collection.

If production Cloudflare Pages builds without `MARKETPLACE_ENABLED=true`, market routes and homepage market-gated links are not present by design.
