import type { CollectionEntry } from 'astro:content';

export function entrySlug(entry: CollectionEntry<'articles' | 'categories' | 'tests' | 'providers'>) {
  return entry.id.replace(/^[^/]+\//, '').replace(/\.md$/, '');
}

export function articleHref(article: CollectionEntry<'articles'>, locale = 'en', routePrefix = locale) {
  if (locale === 'en') {
    const slug = article.data.originalUrl
      ? article.data.originalUrl.replace(/^\/+/, '').replace(/\/+$/, '')
      : entrySlug(article);

    return `/${slug}/`;
  }

  const slug = article.data.originalUrl
    ? article.data.originalUrl.replace(/^\/+/, '').replace(/\/+$/, '')
    : entrySlug(article);

  return `/${routePrefix}/${slug}/`;
}

export function marketHref(market: string) {
  return `/${market}/`;
}

export function categoryHref(market: string, category: CollectionEntry<'categories'>) {
  return `/${market}/categories/${entrySlug(category)}/`;
}

export function testHref(market: string, test: CollectionEntry<'tests'>) {
  return `/${market}/tests/${entrySlug(test)}/`;
}

export function providerHref(market: string, provider: CollectionEntry<'providers'>) {
  return `/${market}/providers/${entrySlug(provider)}/`;
}
