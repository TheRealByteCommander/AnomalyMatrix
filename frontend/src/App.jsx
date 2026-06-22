import { useEffect, useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import HelpPage from './pages/HelpPage';
import HelpLauncher from './components/HelpLauncher';
import LanguageSwitcher from './components/LanguageSwitcher';
import { useI18n } from './i18n/I18nProvider';
import { SCREEN_HELP_ARTICLE, SCREEN_IDS, SCREEN_ORDER } from './i18n/screens';
import { inspections as seed } from './data/sampleData';
import { fetchRecentInspections } from './services';

export default function App() {
  const { t } = useI18n();
  const [active, setActive] = useState(SCREEN_IDS.dashboard);
  const [inspections, setInspections] = useState(seed);
  const [selectedInspectionId, setSelectedInspectionId] = useState(seed[0]?.id ?? null);
  const [apiOnline, setApiOnline] = useState(false);
  const [helpState, setHelpState] = useState({
    articleId: null,
    categoryId: null,
    query: '',
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const latest = await fetchRecentInspections();
        if (!cancelled && latest.length) {
          setInspections(latest);
          setSelectedInspectionId(latest[0].id);
          setApiOnline(true);
        }
      } catch {
        if (!cancelled) setApiOnline(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedInspection = useMemo(
    () => inspections.find((i) => i.id === selectedInspectionId) || inspections[0] || null,
    [inspections, selectedInspectionId]
  );

  function openHelp(articleId) {
    const id = articleId || SCREEN_HELP_ARTICLE[active] || 'help-using-help';
    setHelpState({ articleId: id, categoryId: null, query: '' });
    setActive(SCREEN_IDS.help);
  }

  function openFullHelp({ categoryId = null, query = '' } = {}) {
    setHelpState({ articleId: 'help-using-help', categoryId, query });
    setActive(SCREEN_IDS.help);
  }

  const pageProps = {
    inspections,
    setInspections,
    selectedInspection,
    setSelectedInspectionId,
    goTo: setActive,
    apiOnline,
    openHelp,
  };

  const pages = {
    [SCREEN_IDS.dashboard]: <DashboardPage {...pageProps} />,
    [SCREEN_IDS.inspectionDetail]: <InspectionDetailPage {...pageProps} />,
    [SCREEN_IDS.trends]: <TrendsPage {...pageProps} />,
    [SCREEN_IDS.configuration]: <ConfigurationPage {...pageProps} />,
    [SCREEN_IDS.help]: (
      <HelpPage
        initialArticleId={helpState.articleId}
        initialCategoryId={helpState.categoryId}
        initialQuery={helpState.query}
        onNavigateArticle={(id) => setHelpState((s) => ({ ...s, articleId: id }))}
      />
    ),
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-main">
          <div>
            <p className="eyebrow">{t('app.eyebrow')}</p>
            <h1>{t('app.title')}</h1>
            <p className="muted">{apiOnline ? t('app.connected') : t('app.offline')}</p>
          </div>
          <LanguageSwitcher />
        </div>
        <nav className="tabs" aria-label={t('app.navLabel')}>
          {SCREEN_ORDER.map((screenId) => (
            <button
              key={screenId}
              type="button"
              onClick={() => setActive(screenId)}
              className={screenId === active ? 'tab active' : 'tab'}
            >
              {t(`nav.${screenId}`)}
            </button>
          ))}
        </nav>
      </header>
      {pages[active]}
      <HelpLauncher onOpenArticle={openHelp} onOpenFullHelp={openFullHelp} />
    </div>
  );
}
