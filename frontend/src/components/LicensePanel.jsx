import { useMemo, useState } from 'react';
import { importLicenseGrant } from '../services';
import { useI18n } from '../i18n/I18nProvider';
import StatusBadge from './StatusBadge';

export default function LicensePanel({ license, canManage, onLicenseChange }) {
  const { t } = useI18n();
  const [licenseKey, setLicenseKey] = useState('');
  const [grantText, setGrantText] = useState('');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);

  const features = useMemo(
    () => (Array.isArray(license?.features) ? license.features : []),
    [license]
  );
  const deviceId = license?.device_id || '';
  const licenseState = license?.active ? 'green' : 'amber';

  async function copyDeviceId() {
    if (!deviceId) return;
    try {
      await navigator.clipboard.writeText(deviceId);
      setNotice({ ok: true, message: t('license.copied') });
    } catch {
      setNotice({ ok: false, message: t('license.copyFailed') });
    }
  }

  async function submit({ grant, key }) {
    if (!canManage) return;
    setBusy(grant ? 'import' : 'activate');
    setNotice(null);
    try {
      const result = await importLicenseGrant({ grant, licenseKey: key });
      onLicenseChange?.(result);
      setNotice({ ok: true, message: t('license.activated') });
      if (grant) setGrantText('');
      if (key) setLicenseKey('');
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('license.importFailed') });
    } finally {
      setBusy('');
    }
  }

  async function handleFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    try {
      const text = await file.text();
      setGrantText(text);
      const parsed = JSON.parse(text);
      await submit({ grant: parsed, key: licenseKey.trim() || undefined });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('license.invalidFile') });
    }
  }

  async function handlePasteImport() {
    if (!grantText.trim()) return;
    try {
      const parsed = JSON.parse(grantText);
      await submit({ grant: parsed, key: licenseKey.trim() || undefined });
    } catch {
      setNotice({ ok: false, message: t('license.invalidFile') });
    }
  }

  async function handleActivateKey() {
    if (!licenseKey.trim()) return;
    await submit({ key: licenseKey.trim() });
  }

  return (
    <article className="card" data-testid="license-panel">
      <h3>{t('license.title')}</h3>
      <p className="muted">{t('license.hint')}</p>

      <div className="kpi-grid billing-status">
        <div>
          <label>{t('configuration.licenseTier')}</label>
          <strong>{license?.tier || t('license.na')}</strong>
        </div>
        <div>
          <label>{t('configuration.status')}</label>
          <StatusBadge state={licenseState}>
            {license?.active ? t('license.licensed') : t('license.unlicensed')}
          </StatusBadge>
        </div>
        <div>
          <label>{t('license.mode')}</label>
          <strong>{license?.offline ? t('license.offline') : license?.mode || t('license.na')}</strong>
        </div>
        <div>
          <label>{t('license.validUntil')}</label>
          <strong>{license?.valid_until || t('license.perpetual')}</strong>
        </div>
      </div>

      <div className="license-device">
        <label>{t('license.deviceId')}</label>
        <code data-testid="license-device-id" className="license-device-id">
          {deviceId || t('license.na')}
        </code>
        <button type="button" className="tab" data-testid="license-copy-device" disabled={!deviceId} onClick={copyDeviceId}>
          {t('license.copyDeviceId')}
        </button>
        <p className="muted">{t('license.deviceHint')}</p>
      </div>

      {license?.license_key ? (
        <p className="muted" data-testid="license-key">
          {t('license.number')}: {license.license_key}
        </p>
      ) : null}

      {features.length ? (
        <p className="muted" data-testid="license-features">
          {t('license.features')}: {features.join(', ')}
        </p>
      ) : null}

      {canManage ? (
        <div className="billing-form">
          <label>
            {t('license.importFile')}
            <input type="file" accept=".json,.lic.json,application/json" data-testid="license-import-file" disabled={Boolean(busy)} onChange={handleFile} />
          </label>
          <label>
            {t('license.pasteGrant')}
            <textarea
              rows={6}
              value={grantText}
              disabled={Boolean(busy)}
              data-testid="license-import-json"
              onChange={(event) => setGrantText(event.target.value)}
              placeholder='{"format":"licenseGrant/v1", ...}'
            />
          </label>
          <label>
            {t('license.enterKey')}
            <input
              type="text"
              autoComplete="off"
              value={licenseKey}
              disabled={Boolean(busy)}
              data-testid="license-key-input"
              onChange={(event) => setLicenseKey(event.target.value)}
              placeholder="XXXX-XXXX-XXXX-XXXX"
            />
          </label>
          <div className="billing-actions">
            <button
              type="button"
              className="tab active"
              data-testid="license-import"
              disabled={Boolean(busy) || !grantText.trim()}
              onClick={handlePasteImport}
            >
              {busy === 'import' ? t('license.importing') : t('license.import')}
            </button>
            <button
              type="button"
              className="tab"
              data-testid="license-activate-key"
              disabled={Boolean(busy) || !licenseKey.trim()}
              onClick={handleActivateKey}
            >
              {busy === 'activate' ? t('license.activating') : t('license.activate')}
            </button>
          </div>
        </div>
      ) : (
        <p className="muted">{t('license.readOnly')}</p>
      )}

      {notice ? (
        <p className={notice.ok ? 'ok' : 'error'} role="status">
          {notice.message}
        </p>
      ) : null}
    </article>
  );
}
