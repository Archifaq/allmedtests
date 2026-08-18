import { defineCollection, z } from 'astro:content';
import { markets, type MarketCode } from '../data/markets';

const marketSchema = z.custom<MarketCode>(
  (value) => typeof value === 'string' && value in markets,
  'Invalid market code',
);

const referenceRangeRowSchema = z.object({
  label: z.string(),
  min: z.number(),
  max: z.number(),
  unit: z.string(),
  valuePosition: z.number(),
});

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
    translationOfSlug: z.string().optional(),
    referenceRanges: z.array(referenceRangeRowSchema).optional(),
    imageRestoreNeeded: z.boolean().default(false),
    draft: z.boolean().default(true),
  }),
});

const tests = defineCollection({
  type: 'content',
  schema: z.object({
    market: marketSchema,
    title: z.string(),
    category: z.string().optional(),
    description: z.string().optional(),
    referenceRanges: z.array(referenceRangeRowSchema).optional(),
    draft: z.boolean().default(true),
  }),
});

const providers = defineCollection({
  type: 'content',
  schema: z.object({
    market: marketSchema,
    name: z.string(),
    affiliateNetwork: z.string().optional(),
    affiliateUrl: z.string().url().optional(),
    countriesAvailable: z.array(z.string()).optional(),
    draft: z.boolean().default(true),
  }),
});

const categories = defineCollection({
  type: 'content',
  schema: z.object({
    market: marketSchema,
    title: z.string(),
    description: z.string().optional(),
    draft: z.boolean().default(true),
  }),
});

export const collections = { articles, tests, providers, categories };
