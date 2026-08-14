# allmedtests.com

Astro project for the multilingual laboratory-test marketplace replacing the historical allmedtests.com site.

## Development

```bash
npm run dev
npm run build
```

## Content

Recovered English articles will live in `src/content/articles/en/`. The current content schema is intentionally minimal so old content can be imported without inventing extra required fields.

## Redirects

Deployment target: Cloudflare Pages.

Build command: `npm run build`.

Output directory: `dist/`.

Cloudflare Pages reads redirects from `public/_redirects`, using the Netlify-style format:

```text
/old-path  /new-path  301
```

The redirect file is intentionally not populated yet because taxonomy and legacy shop URL mappings have not been approved. Cloudflare Pages has a redirect-rule limit around 2000 rules; the expected migration map is roughly 260+ redirects from `audit/legacy_products_review.csv` and `audit/taxonomy_review.csv`, so it fits with plenty of room.
