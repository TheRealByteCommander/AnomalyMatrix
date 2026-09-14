import { useEffect, useState } from 'react';
import ContextHelp from './ContextHelp';
import {
  cloneVisionProfile,
  exportVisionProfile,
  fetchRecommendations,
  fetchVisionProfile,
  importVisionProfile,
  saveVisionProfile,
} from '../services';
import { useI18n } from '../i18n/I18nProvider';

const ROLES = ['top', 'side', 'bottom', 'stf', 'completeness', 'other'];
const FORMATS = ['png', 'jpeg', 'raw'];
const COLORS = ['mono', 'rgb', 'bayer'];
const TRIGGERS = ['freerun', 'software', 'hardware', 'mqtt', 'opcua'];
const CHECK_KEYS = [
  'corners_visible',
  'edges_visible',
  'features_visible',
  'bottom_view_covered',
  'lighting_uniform',
  'no_motion_blur',
  'focus_confirmed',
  'fov_covers_part',
];

function emptySlot(index) {
  return {
    slot: index,
    camera_id: `cam-${String(index).padStart(2, '0')}`,
    role: ROLES[Math.min(index - 1, ROLES.length - 1)],
    enabled: true,
    lens_notes: '',
    fov_notes: '',
    working_distance_mm: '',
    lighting: {
      profile_name: 'default',
      exposure_ms: 8,
      gain_db: 0,
      trigger_mode: 'software',
      light_controller: { enabled: false, protocol: 'config', endpoint: '', notes: '' },
    },
    capture: { image_format: 'png', jpeg_quality: 92, width: '', height: '', color_mode: 'mono' },
  };
}

export default function StationVisionSetup({ canConfigure, openHelp }) {
  const { t } = useI18n();
  const [profile, setProfile] = useState(null);
  const [recs, setRecs] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cloneId, setCloneId] = useState('eol-line-2');
  const [importText, setImportText] = useState('');
  const [loadFailed, setLoadFailed] = useState(false);

  async function reload() {
    const [p, r] = await Promise.all([
      fetchVisionProfile(),
      fetchRecommendations().catch(() => null),
    ]);
    setProfile(p);
    setRecs(r);
    setLoadFailed(false);
  }

  useEffect(() => {
    reload().catch(() => {
      setLoadFailed(true);
      setNotice({ ok: false, message: t('vision.loadFailed') });
    });
  }, []);

  function updateCam(index, patch) {
    setProfile((prev) => {
      const cameras = [...(prev.cameras || [])];
      cameras[index] = { ...cameras[index], ...patch };
      return { ...prev, cameras };
    });
  }

  async function handleSave(extra = {}) {
    if (!profile || !canConfigure) return;
    setBusy(true);
    setNotice(null);
    try {
      const saved = await saveVisionProfile({ ...profile, ...extra });
      setProfile(saved);
      setNotice({ ok: true, message: t('vision.saved') });
      const nextRecs = await fetchRecommendations().catch(() => recs);
      setRecs(nextRecs);
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('vision.saveFailed') });
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(fmt) {
    try {
      const { text, filename } = await exportVisionProfile(fmt);
      const blob = new Blob([text], { type: fmt === 'yaml' ? 'application/yaml' : 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      setNotice({ ok: true, message: t('vision.exported') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('vision.exportFailed') });
    }
  }

  async function handleImport() {
    if (!importText.trim()) return;
    setBusy(true);
    try {
      const saved = await importVisionProfile(importText);
      setProfile(saved);
      setNotice({ ok: true, message: t('vision.imported') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('vision.importFailed') });
    } finally {
      setBusy(false);
    }
  }

  async function handleClone() {
    setBusy(true);
    try {
      const saved = await cloneVisionProfile(cloneId);
      setProfile(saved);
      setNotice({ ok: true, message: t('vision.cloned') });
    } catch (err) {
      setNotice({ ok: false, message: err.message || t('vision.cloneFailed') });
    } finally {
      setBusy(false);
    }
  }

  if (!profile) {
    return (
      <article className="card" data-testid="vision-setup">
        <h3>{t('vision.title')}</h3>
        <p className={loadFailed ? 'error' : 'muted'}>
          {loadFailed ? t('vision.loadFailed') : t('vision.loading')}
        </p>
      </article>
    );
  }

  const maxCameras = profile.max_cameras || 4;

  return (
    <article className="card" data-testid="vision-setup">
      <h3>{t('vision.title')}</h3>
      <p className="muted">{t('vision.hint')}</p>
      <ContextHelp articleId="eol-vision-setup" onOpen={openHelp} />

      <div className="training-form">
        <label>
          {t('vision.stationId')}
          <input
            value={profile.station_id || ''}
            disabled={!canConfigure}
            onChange={(e) => setProfile({ ...profile, station_id: e.target.value })}
          />
        </label>
        <label>
          {t('vision.lineId')}
          <input
            value={profile.line_id || ''}
            disabled={!canConfigure}
            onChange={(e) => setProfile({ ...profile, line_id: e.target.value })}
          />
        </label>
        <label>
          {t('vision.profileName')}
          <input
            value={profile.name || ''}
            disabled={!canConfigure}
            onChange={(e) => setProfile({ ...profile, name: e.target.value })}
          />
        </label>
      </div>

      {(profile.cameras || []).map((cam, index) => (
        <div className="vision-cam-card" key={`${cam.camera_id}-${index}`}>
          <strong>{t('vision.slot', { n: index + 1 })}</strong>
          <div className="training-form">
            <label>
              {t('vision.cameraId')}
              <input
                value={cam.camera_id || ''}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { camera_id: e.target.value })}
              />
            </label>
            <label>
              {t('vision.role')}
              <select
                value={cam.role || 'other'}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { role: e.target.value })}
              >
                {ROLES.map((role) => (
                  <option key={role} value={role}>{t(`vision.roles.${role}`)}</option>
                ))}
              </select>
            </label>
            <label>
              {t('vision.lensNotes')}
              <input
                value={cam.lens_notes || ''}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { lens_notes: e.target.value })}
                placeholder={t('vision.lensPlaceholder')}
              />
            </label>
            <label>
              {t('vision.fovNotes')}
              <input
                value={cam.fov_notes || ''}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { fov_notes: e.target.value })}
                placeholder={t('vision.fovPlaceholder')}
              />
            </label>
            <label>
              {t('vision.exposure')}
              <input
                type="number"
                value={cam.lighting?.exposure_ms ?? 8}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { lighting: { ...cam.lighting, exposure_ms: Number(e.target.value) } })}
              />
            </label>
            <label>
              {t('vision.gain')}
              <input
                type="number"
                value={cam.lighting?.gain_db ?? 0}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { lighting: { ...cam.lighting, gain_db: Number(e.target.value) } })}
              />
            </label>
            <label>
              {t('vision.triggerMode')}
              <select
                value={cam.lighting?.trigger_mode || 'software'}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { lighting: { ...cam.lighting, trigger_mode: e.target.value } })}
              >
                {TRIGGERS.map((mode) => (
                  <option key={mode} value={mode}>{mode}</option>
                ))}
              </select>
            </label>
            <label>
              {t('vision.format')}
              <select
                value={cam.capture?.image_format || 'png'}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { capture: { ...cam.capture, image_format: e.target.value } })}
              >
                {FORMATS.map((fmt) => (
                  <option key={fmt} value={fmt}>{fmt}</option>
                ))}
              </select>
            </label>
            <label>
              {t('vision.colorMode')}
              <select
                value={cam.capture?.color_mode || 'mono'}
                disabled={!canConfigure}
                onChange={(e) => updateCam(index, { capture: { ...cam.capture, color_mode: e.target.value } })}
              >
                {COLORS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              {t('vision.lightHook')}
              <input
                value={cam.lighting?.light_controller?.endpoint || ''}
                disabled={!canConfigure}
                placeholder="mqtt:// | opc.tcp:// | http://"
                onChange={(e) => updateCam(index, {
                  lighting: {
                    ...cam.lighting,
                    light_controller: { ...cam.lighting?.light_controller, endpoint: e.target.value, enabled: Boolean(e.target.value) },
                  },
                })}
              />
            </label>
          </div>
        </div>
      ))}

      {canConfigure && (profile.cameras || []).length < maxCameras ? (
        <button
          type="button"
          className="tab"
          onClick={() => setProfile({ ...profile, cameras: [...profile.cameras, emptySlot(profile.cameras.length + 1)] })}
        >
          {t('vision.addSlot')}
        </button>
      ) : null}

      <h4>{t('vision.checklistTitle')}</h4>
      <p className="muted">{t('vision.checklistHint')}</p>
      <ul className="camera-select-list">
        {CHECK_KEYS.map((key) => (
          <li key={key}>
            <label>
              <input
                type="checkbox"
                checked={Boolean(profile.checklist?.[key])}
                disabled={!canConfigure}
                onChange={(e) => setProfile({
                  ...profile,
                  checklist: { ...profile.checklist, [key]: e.target.checked },
                })}
              />
              {t(`vision.checks.${key}`)}
            </label>
          </li>
        ))}
      </ul>

      {canConfigure ? (
        <div className="training-actions">
          <button type="button" className="primary" disabled={busy} onClick={() => handleSave()}>
            {busy ? t('vision.saving') : t('vision.save')}
          </button>
          <button type="button" className="tab" disabled={busy} onClick={() => handleSave({ checklist_confirmed: true })}>
            {t('vision.confirmChecklist')}
          </button>
          <button type="button" className="tab" onClick={() => handleExport('json')}>{t('vision.exportJson')}</button>
          <button type="button" className="tab" onClick={() => handleExport('yaml')}>{t('vision.exportYaml')}</button>
        </div>
      ) : (
        <p className="muted">{t('vision.readOnly')}</p>
      )}

      {canConfigure ? (
        <div className="training-form">
          <label>
            {t('vision.cloneId')}
            <input value={cloneId} onChange={(e) => setCloneId(e.target.value)} />
          </label>
          <button type="button" className="tab" onClick={handleClone}>{t('vision.clone')}</button>
        </div>
      ) : null}

      {canConfigure ? (
        <label className="muted">
          {t('vision.importLabel')}
          <textarea
            rows={4}
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder="{ ... JSON/YAML ... }"
            style={{ width: '100%', marginTop: '.35rem' }}
          />
          <button type="button" className="tab" onClick={handleImport}>{t('vision.import')}</button>
        </label>
      ) : null}

      {recs?.items?.length ? (
        <div data-testid="vision-recommendations">
          <h4>{t('vision.recsTitle')}</h4>
          <ul>
            {recs.items.map((item) => (
              <li key={item.topic}>
                <strong>{item.recommendation}</strong>
                <span className="muted"> — {item.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {notice ? <p className={notice.ok ? 'ok' : 'error'} role="status">{notice.message}</p> : null}
    </article>
  );
}
