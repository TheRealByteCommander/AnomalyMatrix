const STORAGE_KEY = 'amx-locale';

export const LOCALES = [
  { id: 'de', label: 'Deutsch' },
  { id: 'en', label: 'English' },
];

export function detectLocale() {
  if (typeof window === 'undefined') return 'de';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === 'de' || stored === 'en') return stored;
  const nav = (navigator.language || 'en').toLowerCase();
  return nav.startsWith('de') ? 'de' : 'en';
}

export function persistLocale(locale) {
  window.localStorage.setItem(STORAGE_KEY, locale);
}

export function formatMessage(template, vars = {}) {
  if (typeof template !== 'string') return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => (vars[key] != null ? String(vars[key]) : `{${key}}`));
}

function resolvePath(obj, path) {
  return path.split('.').reduce((acc, part) => (acc && acc[part] != null ? acc[part] : undefined), obj);
}

export function createTranslator(messages) {
  return function t(key, vars) {
    const value = resolvePath(messages, key);
    if (value == null) return key;
    if (typeof value === 'string') return formatMessage(value, vars);
    return key;
  };
}
