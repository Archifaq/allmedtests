import { getCollection, type CollectionEntry } from 'astro:content';

export async function getArticlesByLocale(locale: string): Promise<CollectionEntry<'articles'>[]> {
  return getCollection('articles', ({ id }) => id.startsWith(`${locale}/`));
}
