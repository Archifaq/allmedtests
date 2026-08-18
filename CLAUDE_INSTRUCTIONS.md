# AllMedTests Claude Project Instructions

You are working in the `allmedtests.com` Astro repository.

## Core Priorities

1. Preserve SEO-critical legacy URLs.
2. Keep English article URLs unprefixed at `/slug/`.
3. Keep restored and translated articles as `draft: true` until explicit publication approval.
4. Keep the content schema minimal; do not add required frontmatter fields without approval.
5. Use existing Astro routes and content collection patterns instead of creating duplicate route structures.

## Do Not Change Without Explicit Approval

- The homepage route `/`.
- English article slugs in `src/content/articles/en/`.
- `draft: true` on restored or translated articles.
- Astro i18n config in `astro.config.*`, unless reporting a clear issue separately.
- Cloudflare redirects in `public/_redirects`, unless redirect mapping has been approved.
- Required frontmatter fields in `src/content/config.ts`.

## Routing Instructions

English article route:

```text
src/pages/[...slug].astro
```

Translated article route:

```text
src/pages/[locale]/[...slug].astro
```

Do not create per-locale article route files.

Marketplace routes:

```text
src/pages/[market]/index.astro
src/pages/[market]/categories/[...slug].astro
src/pages/[market]/tests/[...slug].astro
src/pages/[market]/providers/[...slug].astro
```

When changing translated slugs, check for collisions with reserved market route segments such as `categories`, `tests`, and `providers`.

## Article Content Instructions

English restored articles live in:

```text
src/content/articles/en/
```

Polish translated articles live in:

```text
src/content/articles/pl/
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

## Validation

For meaningful code, routing, or content changes, run:

```bash
npm run build
```

Warnings about empty `tests` and `providers` collections are expected while those collections are empty.

When validating translated article routes, also run:

```bash
MARKETPLACE_ENABLED=true npm run build
```

This is needed because localized article routes currently generate only when marketplace mode is enabled.
