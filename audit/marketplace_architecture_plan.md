# AllMedTests — Marketplace & Multi-Market Architecture Plan

Status: draft, for Codex implementation
Owner decision log: see "Decisions" section — these are already confirmed, do not re-litigate.

## 1. Non-negotiable constraints (from CLAUDE.md — do not violate)

- `/` (homepage) must stay exactly where it is. No redirect, no rename, no locale prefix on it. It carries 193 referring domains / 53 dofollow — the single most valuable SEO asset in the project.
- The 44 existing English articles under `src/content/articles/en/` keep their exact current slugs and paths (`/{slug}/`, unprefixed). Do not move them.
- Article frontmatter schema stays minimal; only `title` is required. Any new fields added below are optional.
- `public/_redirects` stays a placeholder until legacy product/taxonomy mapping (95 + 167 URLs) is finalized — unrelated to this plan, do not touch it as part of this work.
- Do not add `@astrojs/cloudflare` — static output only.

## 2. Decisions already made (do not re-ask)

- No geo-redirect on `/`. Market/locale detection is a banner/switcher, never a 30x on root.
- Two independent dimensions: **market** (country — currency, regulator, provider directory, hreflang region) and **locale** (language — UI strings + article translation). One locale can serve multiple markets.
- `/pl` ships as a full locale from day one: UI strings + translated articles + commercial layer (not commerce-only).
- Switzerland (`/ch`) market pages default to German (`de-CH`). No separate fr-CH/it-CH sub-variants in this phase.
- Belgium (`/be`) market pages default to French (`fr-BE`). No separate nl-BE sub-variant in this phase.

## 3. Market → Locale mapping

| Market | Locale | Currency | hreflang | Articles source |
|---|---|---|---|---|
| us | en | USD | en-US | `/{slug}/` (root, existing) |
| uk | en | GBP | en-GB | `/{slug}/` (root, existing) |
| ie | en | EUR | en-IE | `/{slug}/` (root, existing) |
| de | de | EUR | de-DE | `/de/{slug}/` |
| at | de | EUR | de-AT | `/de/{slug}/` (shared, no /at/ articles) |
| ch | de | CHF | de-CH | `/de/{slug}/` (shared, no /ch/ articles) |
| fr | fr | EUR | fr-FR | `/fr/{slug}/` |
| be | fr | EUR | fr-BE | `/fr/{slug}/` (shared, no /be/ articles) |
| pl | pl | PLN | pl-PL | `/pl/{slug}/` |
| es | es | EUR | es-ES | `/es/{slug}/` |
| ro | ro | RON | ro-RO | `/ro/{slug}/` |
| hu | hu | HUF | hu-HU | `/hu/{slug}/` |
| cz | cs | CZK | cs-CZ | `/cz/{slug}/` (route uses market code `cz`, locale code `cs`) |
| it | it | EUR | it-IT | `/it/{slug}/` |
| nl | nl | EUR | nl-NL | `/nl/{slug}/` |
| tr | tr | TRY | tr-TR | `/tr/{slug}/` |
| se | sv | SEK | sv-SE | `/se/{slug}/` (route uses market code `se`, locale code `sv`) |
| no | nb | NOK | nb-NO | `/no/{slug}/` (route uses market code `no`, locale code `nb`) |
| dk | da | DKK | da-DK | `/dk/{slug}/` (route uses market code `dk`, locale code `da`) |
| fi | fi | EUR | fi-FI | `/fi/{slug}/` |

20 markets. 13 net-new locales requiring translation: de, fr, pl, es, ro, hu, cs, it, nl, tr, sv, nb, da, fi (en already exists).

Note the market-code vs locale-code mismatch for cz/cs, se/sv, no/nb, dk/da — the URL segment always uses the 2-letter market/country code the business uses (`cz`, `se`, `no`, `dk`), while the underlying translation/locale key uses the correct ISO language code (`cs`, `sv`, `nb`, `da`). Keep this mapping centralized in one config file — do not hardcode it in multiple places.

## 4. Routing architecture

Do NOT create one static page file per market/locale (20+ near-duplicate files is unmaintainable). Use dynamic routes driven by a single config.

```
src/data/markets.ts                       # single source of truth, see below

src/pages/
  index.astro                             # unchanged — homepage
  [...slug].astro                         # unchanged — existing 44 EN articles

  [locale]/[...slug].astro                # translated articles, one file serves
                                           # de, fr, pl, es, ro, hu, cs/cz, it, nl,
                                           # tr, sv/se, nb/no, da/dk, fi

  [market]/index.astro                    # market landing page
  [market]/tests/[...slug].astro
  [market]/providers/[...slug].astro
  [market]/categories/[...slug].astro
```

`src/data/markets.ts`:

```ts
export const markets = {
  us: { locale: 'en', currency: 'USD', hreflang: 'en-US' },
  uk: { locale: 'en', currency: 'GBP', hreflang: 'en-GB' },
  ie: { locale: 'en', currency: 'EUR', hreflang: 'en-IE' },

  de: { locale: 'de', currency: 'EUR', hreflang: 'de-DE' },
  at: { locale: 'de', currency: 'EUR', hreflang: 'de-AT' },
  ch: { locale: 'de', currency: 'CHF', hreflang: 'de-CH' },

  fr: { locale: 'fr', currency: 'EUR', hreflang: 'fr-FR' },
  be: { locale: 'fr', currency: 'EUR', hreflang: 'fr-BE' },

  pl: { locale: 'pl', currency: 'PLN', hreflang: 'pl-PL' },
  es: { locale: 'es', currency: 'EUR', hreflang: 'es-ES' },
  ro: { locale: 'ro', currency: 'RON', hreflang: 'ro-RO' },
  hu: { locale: 'hu', currency: 'HUF', hreflang: 'hu-HU' },
  cz: { locale: 'cs', currency: 'CZK', hreflang: 'cs-CZ' },
  it: { locale: 'it', currency: 'EUR', hreflang: 'it-IT' },
  nl: { locale: 'nl', currency: 'EUR', hreflang: 'nl-NL' },
  tr: { locale: 'tr', currency: 'TRY', hreflang: 'tr-TR' },
  se: { locale: 'sv', currency: 'SEK', hreflang: 'sv-SE' },
  no: { locale: 'nb', currency: 'NOK', hreflang: 'nb-NO' },
  dk: { locale: 'da', currency: 'DKK', hreflang: 'da-DK' },
  fi: { locale: 'fi', currency: 'EUR', hreflang: 'fi-FI' },
} as const;

export type MarketCode = keyof typeof markets;
```

Astro i18n config only needs the actual distinct locales (used for the `[locale]/[...slug].astro` article route and UI string files), not all 20 market codes:

```js
i18n: {
  defaultLocale: 'en',
  locales: ['en', 'de', 'fr', 'pl', 'es', 'ro', 'hu', 'cs', 'it', 'nl', 'tr', 'sv', 'nb', 'da', 'fi'],
  routing: {
    prefixDefaultLocale: false   // en stays unprefixed — unchanged
  }
}
```

Market routing (`[market]/...`) is plain Astro dynamic routes, NOT wired through the i18n plugin — markets are a business/routing concept, not a language concept, and several markets share one locale.

Locale-scoping rule: any new locale or market route that reads from the `articles` collection must use `getArticlesByLocale()` from `src/lib/articles.ts` rather than calling `getCollection('articles')` directly with an inline filter. This keeps future locale work out of the protected homepage and root English article routes.

Deploy gate: translated article routes and market routes are feature-flagged off by default with the build-time environment variable `MARKETPLACE_ENABLED` read from `process.env`. Until Polish content and market pages pass review, `npm run build` with no flag set produces only the review-ready homepage and English article layer. To enable the `pl`/market layer in production later, set `MARKETPLACE_ENABLED=true` in the Cloudflare Pages environment variables for that deployment.

## 5. UI string translations

```
src/i18n/
  en.json
  de.json
  fr.json
  pl.json
  es.json
  ro.json
  hu.json
  cs.json
  it.json
  nl.json
  tr.json
  sv.json
  nb.json
  da.json
  fi.json
```

All hardcoded UI text currently in `index.astro` / `[...slug].astro` (brand line, footer disclaimer, "Find a Test Near You", draft badge label, etc.) must be extracted behind a `t(key, locale)` lookup before any non-English page can ship correctly.

## 6. Content collections

```
src/content/
  articles/
    en/*.md          # existing 44, unchanged
    de/*.md
    fr/*.md
    pl/*.md
    es/*.md
    ro/*.md
    hu/*.md
    cs/*.md
    it/*.md
    nl/*.md
    tr/*.md
    sv/*.md
    nb/*.md
    da/*.md
    fi/*.md

  tests/{us,uk,ie,de,at,ch,fr,be,pl,es,ro,hu,cz,it,nl,tr,se,no,dk,fi}/*.md
  providers/{...same 20 market codes}/*.md
  categories/{...same 20 market codes}/*.md
```

Schema additions (all optional, per the minimal-schema rule):

- `articles`: `translationOfSlug?: string` — links a translated article back to its EN original, used to build hreflang alternates.
- `tests` / `providers` / `categories`: `market: MarketCode` (required within these new collections only — they don't exist yet, so this isn't a breaking change to anything live).

All translated articles ship with `draft: true` by default, same rule as restored EN articles — no auto-publish without manual review, including machine-translated content.

## 7. hreflang / canonical strategy

- `/` and `/{slug}/` (existing EN articles) → `hreflang="en"` (neutral/x-default).
- Each market's commercial pages (`/[market]/tests/...` etc.) → the hreflang value from the `markets.ts` table (e.g. `en-US`, `de-AT`, `fr-BE`).
- Translated article pages (`/[locale]/{slug}/`) → the locale's primary hreflang (e.g. `de` → `de-DE` as default, cross-linked to `de-AT`/`de-CH` market commercial pages, not duplicate article pages).
- AT/CH commercial pages link out to `/de/{slug}/` for background reading; BE commercial pages link out to `/fr/{slug}/`. No duplicate article content is created for AT, CH, BE, US, UK, or IE.

## 8. Build order for Codex (sequenced, not "all in one PR")

1. **Scaffolding only, no content**: `src/data/markets.ts`, updated `astro.config` i18n locales, empty `src/i18n/*.json` (copy en.json as placeholder for all), new `articles`/`tests`/`providers`/`categories` schema updates in `src/content/config.ts`.
2. **Routing skeleton**: `[locale]/[...slug].astro`, `[market]/index.astro`, `[market]/tests/[...slug].astro`, `[market]/providers/[...slug].astro`, `[market]/categories/[...slug].astro` — all render safely with zero content (same pattern already used for empty tests/providers collections today).
3. **PL first full locale** (already prioritized): UI strings, `articles/pl/` translations starting from `priorityTier: P0` (9 articles per `audit/urls_priority.csv`), `pl` market commercial pages.
4. **US/UK/IE commercial layer**: no article translation needed (reuse root articles) — just `tests`/`providers`/`categories` content for these 3 markets, since they're lowest-effort (English only, no translation).
5. **DE/AT/CH wave**: one German article translation set (`articles/de/`) + three market commercial layers.
6. **FR/BE wave**: same pattern, one French set + two markets.
7. **Remaining 10 single-market/single-locale countries** (es, ro, hu, cz, it, nl, tr, se, no, dk, fi): each is one locale + one market, can be parallelized in any order — recommend prioritizing by expected traffic/backlink potential, to be defined separately (not blocking this architecture).
8. **New audit file**: `audit/translation_status.csv` — columns: `slug, locale, market(s), status (not_started/draft/reviewed), translator_source`.
9. **Update `CLAUDE.md`**: replace the current "Next likely phases → later add more locales under /es/, /de/" note (now outdated/superseded) with a reference to this document.
10. **Validation**: `npm run build` must pass with zero content in new market/locale folders (empty-collection warnings are expected and okay, same as today's tests/providers). Verify `/`, all 44 root article paths, are byte-identical in output path before/after.

## 9. Explicitly out of scope for this plan

- Actual translation work (13 languages × 44 articles + commercial copy) — separate content workstream, not a routing/architecture task.
- `/be-nl` and `/ch-fr` / `/ch-it` sub-variants — deferred, not part of this phase per decisions above.
- Real `_redirects` entries — unrelated legacy-URL mapping work, tracked separately.
