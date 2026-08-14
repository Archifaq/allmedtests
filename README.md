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

Recommended deployment target: Vercel. Astro works well there, and future redirect rules can live in `vercel.json` when taxonomy and legacy-product mappings are ready.

No redirect file is created yet because the taxonomy and legacy shop URL mappings have not been approved.
