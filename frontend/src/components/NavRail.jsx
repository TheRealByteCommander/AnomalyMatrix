import { PRIMARY_NAV, SCREEN_IDS, SETTINGS_FAMILY } from '../i18n/screens';
import { useI18n } from '../i18n/I18nProvider';

function IconBetrieb() {
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="7.25" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <circle cx="12" cy="12" r="2.4" fill="currentColor" />
    </svg>
  );
}

function IconQualitaet() {
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 4.5 19 8v8l-7 3.5L5 16V8l7-3.5Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9.2 12.1 11 13.9l3.8-3.8" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function IconTraining() {
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4.5" y="6.5" width="15" height="11" rx="2" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <path d="M8 15.5v-4.2M12 15.5v-7M16 15.5v-2.6" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="3.1" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M12 5.2v-1.4M12 20.2v-1.4M5.2 12H3.8M20.2 12h-1.4M7.1 7.1 6.1 6.1M17.9 17.9l-1 1M17.9 7.1l1-1M7.1 16.9l-1 1"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </svg>
  );
}

const ICONS = {
  [SCREEN_IDS.dashboard]: IconBetrieb,
  [SCREEN_IDS.inspectionDetail]: IconQualitaet,
  [SCREEN_IDS.training]: IconTraining,
  [SCREEN_IDS.configuration]: IconSettings,
};

function isActive(screenId, active) {
  if (screenId === SCREEN_IDS.configuration) return SETTINGS_FAMILY.has(active);
  return screenId === active;
}

export default function NavRail({ active, onNavigate }) {
  const { t } = useI18n();

  return (
    <nav className="nav-rail" aria-label={t('app.navLabel')}>
      <p className="nav-brand">AMX</p>
      {PRIMARY_NAV.map((screenId) => {
        const Icon = ICONS[screenId];
        const activeItem = isActive(screenId, active);
        return (
          <button
            key={screenId}
            type="button"
            data-testid={`nav-${screenId}`}
            className={activeItem ? 'nav-item active' : 'nav-item'}
            onClick={() => onNavigate(screenId)}
          >
            <Icon />
            <span>{t(`nav.${screenId}`)}</span>
          </button>
        );
      })}
    </nav>
  );
}
