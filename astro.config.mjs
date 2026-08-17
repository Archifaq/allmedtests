import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'de', 'fr', 'pl', 'es', 'ro', 'hu', 'cs', 'it', 'nl', 'tr', 'sv', 'nb', 'da', 'fi'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
