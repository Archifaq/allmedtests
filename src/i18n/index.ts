import en from './en.json';
import de from './de.json';
import fr from './fr.json';
import pl from './pl.json';
import es from './es.json';
import ro from './ro.json';
import hu from './hu.json';
import cs from './cs.json';
import it from './it.json';
import nl from './nl.json';
import tr from './tr.json';
import sv from './sv.json';
import nb from './nb.json';
import da from './da.json';
import fi from './fi.json';

export const translations = {
  en,
  de,
  fr,
  pl,
  es,
  ro,
  hu,
  cs,
  it,
  nl,
  tr,
  sv,
  nb,
  da,
  fi,
} as const;

export type LocaleCode = keyof typeof translations;
export type TranslationKey = keyof typeof en;

export function t(key: TranslationKey, locale: LocaleCode = 'en') {
  return translations[locale]?.[key] ?? translations.en[key];
}
