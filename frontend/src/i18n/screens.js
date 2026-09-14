export const SCREEN_IDS = {
  dashboard: 'dashboard',
  inspectionDetail: 'inspectionDetail',
  training: 'training',
  configuration: 'configuration',
  trends: 'trends',
  help: 'help',
};

/** Tesla-like primary destinations — keep this list short. */
export const PRIMARY_NAV = [
  SCREEN_IDS.dashboard,
  SCREEN_IDS.inspectionDetail,
  SCREEN_IDS.training,
  SCREEN_IDS.configuration,
];

/** Nested under Einstellungen, still fully reachable. */
export const SETTINGS_FAMILY = new Set([
  SCREEN_IDS.configuration,
  SCREEN_IDS.trends,
  SCREEN_IDS.help,
]);

export const SETTINGS_ITEMS = [
  { id: 'recipes', testId: 'settings-recipes', labelKey: 'settings.recipes', hintKey: 'settings.recipesHint' },
  { id: 'thresholds', testId: 'settings-thresholds', labelKey: 'settings.thresholds', hintKey: 'settings.thresholdsHint' },
  { id: 'cameras', testId: 'settings-cameras', labelKey: 'settings.cameras', hintKey: 'settings.camerasHint' },
  { id: 'vision', testId: 'settings-vision', labelKey: 'settings.vision', hintKey: 'settings.visionHint' },
  { id: 'trends', testId: 'nav-trends', labelKey: 'settings.trends', hintKey: 'settings.trendsHint', screen: SCREEN_IDS.trends },
  { id: 'storage', testId: 'settings-storage', labelKey: 'settings.storage', hintKey: 'settings.storageHint' },
  { id: 'license', testId: 'settings-license', labelKey: 'settings.license', hintKey: 'settings.licenseHint' },
  { id: 'help', testId: 'nav-help', labelKey: 'settings.help', hintKey: 'settings.helpHint', screen: SCREEN_IDS.help },
];

export const SCREEN_HELP_ARTICLE = {
  dashboard: 'dashboard-overview',
  inspectionDetail: 'inspection-detail',
  training: 'good-part-training',
  trends: 'trends-overview',
  configuration: 'configuration-overview',
  help: 'what-is-anomalymatrix',
};

export const SCREEN_ORDER = PRIMARY_NAV;
