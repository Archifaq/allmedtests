import { defineCollection, z } from 'astro:content';

const articles = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    originalUrl: z.string().optional(),
    originalPublishDate: z.string().optional(),
    restoredDate: z.string().optional(),
    sourceSnapshot: z.string().optional(),
    referringDomains: z.number().optional(),
    priorityTier: z.enum(['P0', 'P1', 'P2', 'P3']).optional(),
    draft: z.boolean().default(true),
  }),
});

const tests = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    category: z.string(),
    description: z.string().optional(),
    draft: z.boolean().default(true),
  }),
});

const providers = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    affiliateNetwork: z.string().optional(),
    affiliateUrl: z.string().url().optional(),
    countriesAvailable: z.array(z.string()).optional(),
    draft: z.boolean().default(true),
  }),
});

export const collections = { articles, tests, providers };
