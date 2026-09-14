import { useCallback, useEffect, useMemo, useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import HeatmapDisplayPage from './pages/HeatmapDisplayPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import TrainingPage from './pages/TrainingPage';
import TrendsPage from './pages/TrendsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import HelpPage from './pages/HelpPage';
import LoginPage from './pages/LoginPage';
import { isHeatmapDisplayPath } from './displayRoute';
import HelpLauncher from './components/HelpLauncher';
import LanguageSwitcher from './components/LanguageSwitcher';
import NavRail from './components/NavRail';
import { useI18n } from './i18n/I18nProvider';
import { SCREEN_HELP_ARTICLE, SCREEN_IDS } from './i18n/screens';
import { inspections as seed } from './data/sampleData';
import { readStoredRecipeId, writeStoredRecipeId } from './recipeSelection';
import { fetchAuthMe, fetchRecentInspections, logout } from './services';

const requireAuth = import.meta.env.VITE_REQUIRE_AUTH === 'true';

export default function App() {
  const { t } = useI18n();
  const [active, setActive] = useState(SCREEN_IDS.dashboard);
  const [settingsSection, setSettingsSection] = useState('');
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
  const [selectedRecipeId, setSelectedRecipeIdState] = useState(() => readStoredRecipeId());

  const setSelectedRecipeId = useCallback((next) => {
    setSelectedRecipeIdState((prev) => {
      const value = typeof next === 'function' ? next(prev) : next;
      const resolved = String(value || '').trim();
      writeStoredRecipeId(resolved);
      return resolved;
    });
  }, []);

  const goTo = useCallback((screenId, options = {}) => {
    setActive(screenId);
    if (screenId === SCREEN_IDS.configuration) {
      setSettingsSection(options.section || '');
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('session_id') || params.get('checkout')) {
      goTo(SCREEN_IDS.configuration, { section: 'license' });
    }
  }, [goTo]);

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
    return (
      <div className="login-shell">
        <p className="muted">{t('login.loading')}</p>
      </div>
    );
  }

  if (requireAuth && !authUser) {
    return <LoginPage onSuccess={setAuthUser} />;
  }

  if (isHeatmapDisplayPath()) {
    return <HeatmapDisplayPage />;
  }

  const pageProps = {
    inspections,
    setInspections,
    selectedInspection,
    setSelectedInspectionId,
    goTo,
    apiOnline,
    openHelp,
    selectedRecipeId,
    setSelectedRecipeId,
    settingsSection,
    setSettingsSection,
  };

  const pages = {
    [SCREEN_IDS.dashboard]: <DashboardPage {...pageProps} />,
    [SCREEN_IDS.inspectionDetail]: <InspectionDetailPage {...pageProps} />,
    [SCREEN_IDS.training]: <TrainingPage {...pageProps} />,
    [SCREEN_IDS.trends]: <TrendsPage {...pageProps} />,
    [SCREEN_IDS.configuration]: <ConfigurationPage {...pageProps} />,
    [SCREEN_IDS.help]: (
      <HelpPage
        initialArticleId={helpState.articleId}
        initialCategoryId={helpState.categoryId}
        initialQuery={helpState.query}
        onNavigateArticle={(id) => setHelpState((s) => ({ ...s, articleId: id }))}
        goTo={goTo}
      />
    ),
  };

  return (
    <div className="hmi-shell">
      <a href="#main-content" className="skip-link" data-testid="skip-to-content">{t('app.skipToContent')}</a>
      <NavRail active={active} onNavigate={goTo} />
      <div className="hmi-stage">
        <header className="status-bar">
          <div className="status-bar-live">
            <span className={apiOnline ? 'status-dot online' : 'status-dot offline'} aria-hidden="true" />
            <span className="muted">
              {apiOnline ? t('app.connected') : t('app.offline')}
              {authUser ? ` · ${authUser.display_name}` : ''}
            </span>
          </div>
          <div className="topbar-actions">
            <LanguageSwitcher />
            {authUser ? (
              <button type="button" className="tab" data-testid="logout-btn" onClick={handleLogout}>
                {t('login.logout')}
              </button>
            ) : null}
          </div>
        </header>
        <main id="main-content" className="main-content">
          {pages[active]}
        </main>
      </div>
      <HelpLauncher onOpenArticle={openHelp} onOpenFullHelp={openFullHelp} />
    </div>
  );
}
