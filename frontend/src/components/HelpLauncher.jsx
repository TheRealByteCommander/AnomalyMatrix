import { useEffect, useMemo, useState } from 'react';
import { useI18n } from '../i18n/I18nProvider';
import { getHelpCategories } from '../help/helpContent';
import { searchHelpArticles } from '../help/searchHelp';

export default function HelpLauncher({ onOpenArticle, onOpenFullHelp }) {
  const { locale, t } = useI18n();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'F1') {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const categories = useMemo(() => getHelpCategories(locale), [locale]);
  const results = useMemo(() => searchHelpArticles(query, { locale }).slice(0, 8), [query, locale]);
  const defaultResults = useMemo(() => searchHelpArticles('', { locale }).slice(0, 6), [locale]);

  function openArticle(id) {
    setOpen(false);
    setQuery('');
    onOpenArticle(id);
  }

  return (
    <>
      <button
        type="button"
        className="help-fab"
        onClick={() => setOpen(true)}
        aria-label={t('help.fabAria')}
        title={t('help.fabTitle')}
      >
        ?
      </button>

      {open && (
        <div className="help-overlay" role="presentation" onClick={() => setOpen(false)}>
          <div
            className="help-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-drawer-title"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="help-drawer-header">
              <div>
                <p className="eyebrow">{t('help.drawerEyebrow')}</p>
                <h2 id="help-drawer-title">{t('help.drawerTitle')}</h2>
              </div>
              <button type="button" className="tab" onClick={() => setOpen(false)} aria-label={t('common.close')}>
                ✕
              </button>
            </header>

            <input
              className="help-search-input"
              type="search"
              placeholder={t('help.drawerSearch')}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />

            <div className="help-quick-cats">
              {categories.slice(0, 4).map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="help-chip"
                  onClick={() => {
                    setOpen(false);
                    onOpenFullHelp({ categoryId: c.id });
                  }}
                >
                  {c.icon} {c.label}
                </button>
              ))}
            </div>

            <ul className="help-result-list">
              {(query ? results : defaultResults).map(({ article }) => (
                <li key={article.id}>
                  <button type="button" className="help-result-btn" onClick={() => openArticle(article.id)}>
                    <strong>{article.title}</strong>
                    <span className="muted">{article.summary}</span>
                  </button>
                </li>
              ))}
              {query && results.length === 0 && (
                <li className="muted help-empty">{t('help.drawerEmpty')}</li>
              )}
            </ul>

            <footer className="help-drawer-footer">
              <button type="button" className="tab active" onClick={() => { setOpen(false); onOpenFullHelp({}); }}>
                {t('help.drawerOpenAll')}
              </button>
              <span className="muted">{t('help.drawerHints')}</span>
            </footer>
          </div>
        </div>
      )}
    </>
  );
}
