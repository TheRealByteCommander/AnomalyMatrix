import { useEffect, useState } from 'react';
import {
  fetchMqttStatus,
  fetchRetention,
  fetchStorageStats,
  fetchWatchdog,
  runRetention,
  saveRetention,
} from '../services';
import { useI18n } from '../i18n/I18nProvider';
import StatusBadge from './StatusBadge';

export default function StorageEndurancePanel({ canConfigure }) {
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [watchdog, setWatchdog] = useState(null);
  const [mqtt, setMqtt] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [s, p, w, m] = await Promise.all([
          fetchStorageStats().catch(() => null),
          fetchRetention().catch(() => null),
          fetchWatchdog().catch(() => null),
          fetchMqttStatus().catch(() => null),
        ]);
        setStats(s);
        setPolicy(p);
        setWatchdog(w);
        setMqtt(m);
      } catch {
        setNotice({ ok: false, message: t('storage.loadFailed') });
      }
    })();
  }, [t]);

  async function handleSave() {
    if (!policy || !canConfigure) return;
    setBusy(true);
    try {
      const saved = await saveRetention({
        ttl_days: Number(policy.ttl_days),
        archive_bucket: policy.archive_bucket,
        archive_prefix: policy.archive_prefix,
        legal_hold_default: Boolean(policy.legal_hold_default),
        delete_after_archive: Boolean(policy.delete_after_archive),
        enabled: Boolean(policy.enabled),
      });
      setPolicy(saved);
      setNotice({ ok: true, message: t('storage.saved') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('storage.saveFailed') });
    } finally {
      setBusy(false);
    }
  }

  async function handleRun() {
    setBusy(true);
    try {
      await runRetention();
      const s = await fetchStorageStats();
      setStats(s);
      setNotice({ ok: true, message: t('storage.ran') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('storage.runFailed') });
    } finally {
      setBusy(false);
    }
  }

  const wdState = watchdog?.gap_detected ? 'amber' : watchdog?.status === 'ok' ? 'green' : 'amber';

  return (
    <article className="card" data-testid="storage-endurance">
      <h3>{t('storage.title')}</h3>
      <p className="muted">{t('storage.hint')}</p>
      <div className="kpi-grid">
        <div>
          <label>{t('storage.objects')}</label>
          <strong>{stats?.object_count ?? '—'}</strong>
        </div>
        <div>
          <label>{t('storage.bytes')}</label>
          <strong>{stats ? `${Math.round((stats.total_bytes || 0) / 1024)} KiB` : '—'}</strong>
        </div>
        <div>
          <label>{t('storage.avg')}</label>
          <strong>{stats ? `${Math.round((stats.avg_bytes || 0) / 1024)} KiB` : '—'}</strong>
        </div>
        <div>
          <label>{t('storage.watchdog')}</label>
          <StatusBadge state={wdState}>{watchdog?.status || '—'}</StatusBadge>
        </div>
      </div>
      <p className="muted">
        MQTT: {mqtt?.enabled ? t('common.yes') : t('common.no')}
        {mqtt?.connected ? ` · ${t('storage.mqttConnected')}` : ''}
        {' · '}OPC-UA {t('storage.opcuaActive')}
      </p>
      {policy ? (
        <div className="training-form">
          <label>
            {t('storage.ttl')}
            <input
              type="number"
              min={1}
              value={policy.ttl_days}
              disabled={!canConfigure}
              onChange={(e) => setPolicy({ ...policy, ttl_days: Number(e.target.value) })}
            />
          </label>
          <label>
            {t('storage.archiveBucket')}
            <input
              value={policy.archive_bucket || ''}
              disabled={!canConfigure}
              onChange={(e) => setPolicy({ ...policy, archive_bucket: e.target.value })}
            />
          </label>
          <label>
            {t('storage.archivePrefix')}
            <input
              value={policy.archive_prefix || ''}
              disabled={!canConfigure}
              onChange={(e) => setPolicy({ ...policy, archive_prefix: e.target.value })}
            />
          </label>
        </div>
      ) : null}
      {canConfigure ? (
        <div className="training-actions">
          <button type="button" className="primary" disabled={busy} onClick={handleSave}>
            {t('storage.save')}
          </button>
          <button type="button" className="tab" disabled={busy} onClick={handleRun}>
            {t('storage.runNow')}
          </button>
        </div>
      ) : (
        <p className="muted">{t('storage.readOnly')}</p>
      )}
      {notice ? <p className={notice.ok ? 'ok' : 'error'}>{notice.message}</p> : null}
    </article>
  );
}
