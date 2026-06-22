import { LOCALES } from '../i18n/core';
import { useI18n } from '../i18n/I18nProvider';

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="lang-switcher">
      <label htmlFor="amx-locale" className="lang-switcher-label">
        {t('lang.label')}
      </label>
      <select
        id="amx-locale"
        className="lang-switcher-select"
        value={locale}
        onChange={(e) => setLocale(e.target.value)}
        aria-label={t('lang.label')}
      >
        {LOCALES.map((opt) => (
          <option key={opt.id} value={opt.id}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
