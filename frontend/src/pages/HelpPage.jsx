import { useEffect, useMemo, useState } from 'react';
import { useI18n } from '../i18n/I18nProvider';
import { getArticleById, getArticlesByCategory, getHelpArticles, getHelpCategories } from '../help/helpContent';
import { searchHelpArticles } from '../help/searchHelp';

function ArticleBody({ article, categories, onSelectArticle, lookupArticle, t }) {
  const category = categories.find((c) => c.id === article.category);

  return (
    <article className="help-article-body">
      <header>
        <p className="eyebrow">{category ? `${category.icon} ${category.label}` : t('help.categoryFallback')}</p>
        <h2>{article.title}</h2>
        <p className="muted">{article.summary}</p>
      </header>

      {article.sections.map((section) => (
        <section key={section.heading} className="help-section">
          <h3>{section.heading}</h3>
          <ul className="help-bullet-list">
            {section.paragraphs.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </section>
      ))}

      {article.related?.length > 0 && (
        <footer className="help-related">
          <h3>{t('help.related')}</h3>
          <div className="help-related-links">
            {article.related.map((id) => {
              const rel = lookupArticle(id);
              if (!rel) return null;
              return (
                <button key={id} type="button" className="help-chip" onClick={() => onSelectArticle(id)}>
                  {rel.title}
                </button>
              );
            })}
          </div>
        </footer>
      )}
    </article>
  );
}

export default function HelpPage({
  initialArticleId = null,
  initialCategoryId = null,
  initialQuery = '',
  onNavigateArticle,
}) {
  const { locale, t, messages } = useI18n();
  const [query, setQuery] = useState(initialQuery);
  const [categoryId, setCategoryId] = useState(initialCategoryId || '');
  const [selectedId, setSelectedId] = useState(initialArticleId || 'help-using-help');

  const categories = useMemo(() => getHelpCategories(locale), [locale]);
  const allArticles = useMemo(() => getHelpArticles(locale), [locale]);

  useEffect(() => {
    if (initialArticleId) setSelectedId(initialArticleId);
    if (initialCategoryId) setCategoryId(initialCategoryId);
    if (initialQuery) setQuery(initialQuery);
  }, [initialArticleId, initialCategoryId, initialQuery]);

  const listItems = useMemo(() => {
    if (query.trim()) {
      return searchHelpArticles(query, { categoryId: categoryId || undefined, locale }).map((r) => r.article);
    }
    if (categoryId) return getArticlesByCategory(categoryId, locale);
    return allArticles;
  }, [query, categoryId, locale, allArticles]);

  const selected = getArticleById(selectedId, locale) || allArticles[0];

  const lookupArticle = (id) => getArticleById(id, locale);

  function selectArticle(id) {
    setSelectedId(id);
    onNavigateArticle?.(id);
  }

  const faqItems = messages.help.faqItems;

  return (
    <section className="page-grid help-page">
      <article className="card hero">
        <div>
          <p className="eyebrow">{t('help.eyebrow')}</p>
          <h2>{t('help.title')}</h2>
          <p className="muted">{t('help.subtitle')}</p>
        </div>
      </article>

      <div className="help-layout">
        <aside className="card help-sidebar">
          <input
            className="help-search-input"
            type="search"
            placeholder={t('help.searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={t('help.searchAria')}
          />

          <nav className="help-categories" aria-label={t('help.categoriesAria')}>
            <button
              type="button"
              className={!categoryId ? 'help-cat-btn active' : 'help-cat-btn'}
              onClick={() => setCategoryId('')}
            >
              {t('help.allTopics')}
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={categoryId === c.id ? 'help-cat-btn active' : 'help-cat-btn'}
                onClick={() => setCategoryId(c.id)}
              >
                <span aria-hidden="true">{c.icon}</span> {c.label}
                <span className="help-cat-count">{getArticlesByCategory(c.id, locale).length}</span>
              </button>
            ))}
          </nav>

          <ul className="help-article-list" aria-label={t('help.articlesAria')}>
            {listItems.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  className={selectedId === a.id ? 'help-article-btn active' : 'help-article-btn'}
                  onClick={() => selectArticle(a.id)}
                >
                  <span className="help-article-title">{a.title}</span>
                  <span className="muted help-article-summary">{a.summary}</span>
                </button>
              </li>
            ))}
            {listItems.length === 0 && (
              <li className="muted help-empty">{t('help.noResults')}</li>
            )}
          </ul>
        </aside>

        <div className="card help-main">
          <ArticleBody
            article={selected}
            categories={categories}
            onSelectArticle={selectArticle}
            lookupArticle={lookupArticle}
            t={t}
          />
        </div>
      </div>

      <article className="card help-faq-strip">
        <h3>{t('help.faqTitle')}</h3>
        <div className="help-faq-grid">
          {faqItems.map((item) => (
            <button key={item.id} type="button" className="help-faq-card" onClick={() => selectArticle(item.id)}>
              <span className="muted">{t('common.faq')}</span>
              <strong>{item.q}</strong>
            </button>
          ))}
        </div>
      </article>
    </section>
  );
}
