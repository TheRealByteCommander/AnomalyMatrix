import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { createTranslator, detectLocale, persistLocale } from './core';
import de from './locales/de.js';
import en from './locales/en.js';

const MESSAGES = { de, en };

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [locale, setLocaleState] = useState(detectLocale);

  const value = useMemo(() => {
    const messages = MESSAGES[locale] || MESSAGES.de;
    const t = createTranslator(messages);
    return {
      locale,
      messages,
      t,
      setLocale(next) {
        if (next !== 'de' && next !== 'en') return;
        persistLocale(next);
        setLocaleState(next);
      },
    };
  }, [locale]);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
