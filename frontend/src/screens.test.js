import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { PRIMARY_NAV, SCREEN_IDS, SETTINGS_FAMILY, SETTINGS_ITEMS } from './i18n/screens.js';

describe('HMI information architecture', () => {
  it('keeps primary navigation to four destinations', () => {
    assert.deepEqual(PRIMARY_NAV, [
      SCREEN_IDS.dashboard,
      SCREEN_IDS.inspectionDetail,
      SCREEN_IDS.training,
      SCREEN_IDS.configuration,
    ]);
  });

  it('nests trends and help under settings without dropping them', () => {
    assert.equal(SETTINGS_FAMILY.has(SCREEN_IDS.trends), true);
    assert.equal(SETTINGS_FAMILY.has(SCREEN_IDS.help), true);
    const ids = SETTINGS_ITEMS.map((item) => item.id);
    assert.deepEqual(ids, [
      'recipes',
      'thresholds',
      'cameras',
      'vision',
      'trends',
      'storage',
      'license',
      'help',
    ]);
  });
});
