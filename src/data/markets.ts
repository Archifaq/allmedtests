type MarketConfig = {
  locale: string;
  currency: string;
  hreflang: string;
  primaryForLocale?: true;
};

export const markets = {
  us: { locale: 'en', currency: 'USD', hreflang: 'en-US' },
  uk: { locale: 'en', currency: 'GBP', hreflang: 'en-GB' },
  ie: { locale: 'en', currency: 'EUR', hreflang: 'en-IE' },

  de: { locale: 'de', currency: 'EUR', hreflang: 'de-DE', primaryForLocale: true },
  at: { locale: 'de', currency: 'EUR', hreflang: 'de-AT' },
  ch: { locale: 'de', currency: 'CHF', hreflang: 'de-CH' },

  fr: { locale: 'fr', currency: 'EUR', hreflang: 'fr-FR', primaryForLocale: true },
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
} as const satisfies Record<string, MarketConfig>;

export type MarketCode = keyof typeof markets;
