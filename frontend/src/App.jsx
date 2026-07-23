import { useEffect, useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import HelpPage from './pages/HelpPage';
import LoginPage from './pages/LoginPage';
import HelpLauncher from './components/HelpLauncher';
import LanguageSwitcher from './components/LanguageSwitcher';
import { useI18n } from './i18n/I18nProvider';
import { SCREEN_HELP_ARTICLE, SCREEN_IDS, SCREEN_ORDER } from './i18n/screens';
import { inspections as seed } from './data/sampleData';
import { fetchAuthMe, fetchRecentInspections, logout } from './services';

const requireAuth = import.meta.env.VITE_REQUIRE_AUTH === 'true';

export default function App() {
  const { t } = useI18n();
  const [active, setActive] = useState(SCREEN_IDS.dashboard);
  const [inspections, setInspections] = useState(seed);
  const [selectedInspectionId, setSelectedInspectionId] = useState(seed[0]?.id ?? null);
  const [apiOnline, setApiOnline] = useState(false);
  const [authUser, setAuthUser] = useState(null);
  const [authReady, setAuthReady] = useState(!requireAuth);
  const [helpState, setHelpState] = useState({
    articleId: null,
    categoryId: null,
    query: '',
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await fetchAuthMe();
        if (!cancelled) setAuthUser(me);
      } catch {
        if (!cancelled) setAuthUser(null);
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (requireAuth && !authUser) return;
    let cancelled = false;
    (async () => {
      try {
        const latest = await fetchRecentInspections();
        if (!cancelled && latest.length) {
          setInspections(latest);
          setSelectedInspectionId(latest[0].id);
          setApiOnline(true);
        } else if (!cancelled) {
          setApiOnline(true);
        }
      } catch {
        if (!cancelled) setApiOnline(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authUser, requireAuth]);

  const selectedInspection = useMemo(
    () => inspections.find((i) => i.id === selectedInspectionId) || inspections[0] || null,
    [inspections, selectedInspectionId]
  );

  function openHelp(articleId) {
    const id = articleId || SCREEN_HELP_ARTICLE[active] || 'what-is-anomalymatrix';
    setHelpState({ articleId: id, categoryId: null, query: '' });
    setActive(SCREEN_IDS.help);
  }

  function openFullHelp({ categoryId = null, query = '' } = {}) {
    setHelpState({ articleId: 'what-is-anomalymatrix', categoryId, query });
    setActive(SCREEN_IDS.help);
  }

  async function handleLogout() {
    await logout();
    setAuthUser(null);
  }

  if (!authReady) {
    return <div className="shell"><p className="muted">{t('login.loading')}</p></div>;
  }

  if (requireAuth && !authUser) {
    return <LoginPage onSuccess={setAuthUser} />;
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
      <a href="#main-content" className="skip-link" data-testid="skip-to-content">{t('app.skipToContent')}</a>
      <header className="topbar">
        <div className="topbar-main">
          <div>
            <p className="eyebrow">{t('app.eyebrow')}</p>
            <h1>{t('app.title')}</h1>
            <p className="muted">
              {apiOnline ? t('app.connected') : t('app.offline')}
              {authUser ? ` · ${authUser.display_name}` : ''}
            </p>
          </div>
          <div className="topbar-actions">
            <LanguageSwitcher />
            {authUser ? (
              <button type="button" className="tab" data-testid="logout-btn" onClick={handleLogout}>
                {t('login.logout')}
              </button>
            ) : null}
          </div>
        </div>
        <nav className="tabs" aria-label={t('app.navLabel')}>
          {SCREEN_ORDER.map((screenId) => (
            <button
              key={screenId}
              type="button"
              data-testid={`nav-${screenId}`}
              onClick={() => setActive(screenId)}
              className={screenId === active ? 'tab active' : 'tab'}
            >
              {t(`nav.${screenId}`)}
            </button>
          ))}
        </nav>
      </header>
      <main id="main-content" className="main-content">
        {pages[active]}
      </main>
      <HelpLauncher onOpenArticle={openHelp} onOpenFullHelp={openFullHelp} />
    </div>
  );
}
